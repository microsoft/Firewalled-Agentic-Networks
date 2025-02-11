import sys
import json
import os
from utility_other_adv_prompts import (
    utility_questions_prompt,
    utility_prompt_input,
    answer_format,
    conversation_prompt,
    conversation_prompt_input,
    package_format,
    specific_adv_question_prompt,
)


current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)

sys.path.append(parent)
from model import LLM
from utils import load_config


# load configs
config = load_config(os.path.join(current, "config_judge.yaml"))

with open(os.path.join(parent, config["external_options"]), "r") as file:
    database_options = file.read()

with open(os.path.join(parent, config["user_env_file"]), "r") as file:
    user_env = file.read()

# load llm instance
llm_instance = LLM(llm_name=config["llm_name"], config=config)


def get_history(conversation):
    history = ""
    for turn in conversation:

        if turn["from"] == "assistant" and turn["to"] == "external_agent":
            history += "\n\n"
            history += (
                f"From {{AI assistant}} to {{external_agent}}: {turn["short_answer"]}"
            )
        elif turn["from"] == "external_agent" and turn["to"] == "assistant":
            history += "\n\n"
            history += (
                f"From {{external_agent}} to {{AI assistant}}: {turn["short_answer"]}"
            )
        elif turn["from"] == "assistant" and turn["to"] == "environment":
            history += "\n\n"
            history += f"From {{AI assistant}} to the user {{environment}}: {turn["short_answer"]}"
        elif turn["from"] == "environment" and turn["to"] == "assistant":
            history += "\n\n"
            history += f"From the user {{environment}} to the {{AI assistant}}: {turn["short_answer"]}"
    return history


judge_outputs = {}

files = os.listdir(os.path.join(parent, config["outputs"]))
json_files = []
for file in files:
    if ".json" in file and not "judge.json" in file:
        json_files.append(file)
        
def loop_files(json_files): 
    global judge_outputs 
    global utility_prompt_input 
    global conversation_prompt
    for file in json_files:
        if not file in judge_outputs:
            try: 
                print("=========================================")
                print(file)
                print("=========================================")
                output = json.load(open(os.path.join(parent, config["outputs"], file)))
                final_package = output[-1]["short_answer"].split("\n\n Final output:")[-1]

                utility_prompt_input_complete = utility_prompt_input.format(
                    package_format,
                    final_package,
                    database_options,
                    config["user_task"],
                    user_env,
                )
                ## judge on final package
                judge_utility_prompt = (
                    utility_questions_prompt + utility_prompt_input_complete + answer_format
                )
                judge_utility_prompt = [{"role": "system", "content": judge_utility_prompt}]

                judge_output_str = llm_instance.call_model(judge_utility_prompt)
                print(judge_output_str)

                final_assessment = (
                    judge_output_str.split("<final_evaluation>")[-1]
                    .split("</final_evaluation>")[0]
                    .strip()
                )
                ## judge on conversation
                history = get_history(output)
                conversation_prompt_input_complete = conversation_prompt_input.format(
                    config["user_task"], history
                )
                ### add adv task if any
                if config["other_tasks"]:
                    attack_task = specific_adv_question_prompt.format(config["other_tasks"])
                    conversation_prompt = conversation_prompt + attack_task

                judge_conv_prompt = (
                    conversation_prompt + conversation_prompt_input_complete + answer_format
                )
                judge_conv_prompt = [{"role": "system", "content": judge_conv_prompt}]
                judge_output_str_conv = llm_instance.call_model(judge_conv_prompt)
                print("=====")
                print(judge_output_str_conv)

                final_assessment_conv = (
                    judge_output_str_conv.split("<final_evaluation>")[-1]
                    .split("</final_evaluation>")[0]
                    .strip()
                )
                ## save output
                judge_outputs[file] = {
                    "final_package": {
                        "judge_text": judge_output_str,
                        "final_assessment": json.loads(final_assessment),
                    },
                    "conversation": {
                        "judge_text": judge_output_str_conv,
                        "final_assessment": json.loads(final_assessment_conv),
                    },
                }
            except:
                continue 

while len(judge_outputs) != len(json_files):
    loop_files(json_files)

# save output
with open(
    os.path.join(parent, config["outputs"], "utility_other_adv_judge.json"), "w"
) as f:
    json.dump(judge_outputs, f)
