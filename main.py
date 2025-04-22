import sys
import json
import datetime
import os
from user_environment.environment_agent import UserEnvironmentAgent
from assistant.assistant_agent import Assistant
from external_agent.external_agent import External
from assistant.assistant_prompts import simulation_ended

from model import LLM
from utils import load_config, Logger, log_conversations
from mitigation_guidelines.input_guidelines_prompts import input_guidelines_prompt

config = load_config()

# create output dir
os.makedirs(config["logs_folder"], exist_ok=True)

# Get the current timestamp and format it
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = os.path.join(config["logs_folder"], f"output_{timestamp}.txt")

# save conversations
conversations_history = []

# Redirect sys.stdout to the Logger object
sys.stdout = Logger(log_filename)

print("\n\n\n=== configuration ===")
print(config)
print("=====================")

with open(config["user_env_file"], "r") as file:
    user_env = file.read()

if config["apply_data_firewall"] and config["data_rules"]:
    with open(config["data_rules"], "r") as file:
        confid_rules = file.read()
else:
    confid_rules = ""

if config["apply_trajectory_firewall"] and config["trajectory_rules"]:
    assert config["baseline_mode"] == False
    with open(config["trajectory_rules"], "r") as file:
        integrity_rules = file.read()
else:
    integrity_rules = ""

if config["apply_input_firewall"] and config["apply_input_firewall"]:
    """
    this is the predefined input firewall
    """
    with open(config["fixed_input_firewall_path"], "r") as file:
        fixed_input_firewall = file.read()
else:
    fixed_input_firewall = ""

llm_instance = LLM(llm_name=config["llm_name"], config=config)
simulator = UserEnvironmentAgent(
    llm_instance=llm_instance,
    user_env=user_env,
    apply_firewall=config["apply_data_firewall"],
    firewall_rules=confid_rules,
    user_task=config["user_task"],
)
assistant = Assistant(
    config["user_task"],
    config["external_agent_role"],
    llm_instance,
    baseline_mode=config["baseline_mode"],
    guidelines=integrity_rules,
    use_guidelines=config["apply_trajectory_firewall"],
    predefined_input_firewall_flag=config["apply_input_firewall"]
    and (True if fixed_input_firewall != "" else False),
)

if config["external_options"] != "":
    with open(config["external_options"], "r") as file:
        package_options = file.read()
    external = External(
        config["external_agent_role"],
        config["external_agent_mode"],
        llm_instance,
        curated_package_options=package_options,
        external_agent_additional_info=(
            config["external_agent_additional_info"]
            if config["use_additional_info"]
            else ""
        ),
        apply_input_firewall=config["apply_input_firewall"],
        input_guidelines_prompt=input_guidelines_prompt,
        predefined_language=fixed_input_firewall,
    )

# generate initial plan
print("\n\n\n=== assistant ===")
plan_str_output, extracted_plan = assistant.generate_initial_plan()
conversations_history.append(
    log_conversations(plan_str_output, extracted_plan, "assistant", "assistant")
)

previous_turn, previous_turn_str = None, None
task_done = False

while not task_done:
    print("\n\n\n=== assistant ===")
    # start with assistant always
    if previous_turn:
        if previous_turn.type == "external_agent_return":
            conversations_history.append(
                log_conversations(
                    previous_turn_str,
                    previous_turn.answer,
                    "external_agent",
                    "assistant",
                )
            )
        if previous_turn.type == "environment_return":
            conversations_history.append(
                log_conversations(
                    previous_turn_str, previous_turn.answer, "environment", "assistant"
                )
            )

    response, response_str = assistant.generate_turn(previous_turn)
    if config["apply_input_firewall"] and fixed_input_firewall != "":
        """
        if we have predefined input IDs replace back the IDs with their corresponding names
        """
        response.answer = external.update_ids_to_names(response.answer)
        print("==== Assistant response fter replacing IDs with names again ")
        print(response.answer)

    # check if is done
    if (
        response.type == "assistant_return"
        and (simulation_ended + "\n\n Final output:") in response.answer
    ):
        task_done = True
        conversations_history.append(
            log_conversations(response_str, response.answer, "assistant", "assistant")
        )
        break

    # check if the answer is addressed to the env
    if response.type == "to_environment":
        print("\n\n\n==== user_environment ====")
        conversations_history.append(
            log_conversations(response_str, response.answer, "assistant", "environment")
        )

        previous_turn, previous_turn_str = simulator.simulate_env(
            response.answer,
        )

    # check if the answer is addressed to the external agent
    if response.type == "to_external_agent":
        print("\n\n\n==== external ====")
        conversations_history.append(
            log_conversations(
                response_str, response.answer, "assistant", "external_agent"
            )
        )

        previous_turn, previous_turn_str = external.generate_turn(response)


conv_filename = os.path.join(config["logs_folder"], f"output_{timestamp}.json")
sys.stdout.flush()
with open(conv_filename, "w") as f:
    json.dump(conversations_history, f)
