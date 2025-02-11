import sys
import json
import os
from privacy_prompts import (
    privacy_general_questions_prompt,
    privacy_specific_question_prompt,
    privacy_prompt_input,
    privacy_format,
)


current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)

sys.path.append(parent)
from model import LLM
from utils import load_config


# load configs
config = load_config(os.path.join(current, "config_judge.yaml"))

# load llm instance
llm_instance = LLM(llm_name=config["llm_name"], config=config)


def get_history(conversation):
    history = ""
    for turn in conversation:
        # "from": "assistant"
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
    return history


judge_outputs = {}

files = os.listdir(os.path.join(parent, config["outputs"]))
json_files = []
for file in files:
    if ".json" in file and not "judge.json" in file:
        json_files.append(file)


def loop_files(json_files):
    global judge_outputs
    global privacy_specific_question_prompt
    global privacy_general_questions_prompt
    for file in json_files:
        if not file in judge_outputs:
            try:
                print("=========================================")
                print(file)
                print("=========================================")
                output = json.load(open(os.path.join(parent, config["outputs"], file)))

                history = get_history(output)

                if config["privacy_question"]:
                    privacy_attack_task = privacy_specific_question_prompt.format(
                        config["privacy_question"]
                    )
                    privacy_general_questions_prompt = (
                            privacy_general_questions_prompt + privacy_attack_task
                    )

                privacy_prompt_input_complete = privacy_prompt_input.format(
                    config["user_task"], history
                )

                judge_privacy_prompt = (
                        privacy_general_questions_prompt
                        + privacy_prompt_input_complete
                        + privacy_format
                )
                judge_privacy_prompt = [{"role": "system", "content": judge_privacy_prompt}]

                judge_output_str = llm_instance.call_model(judge_privacy_prompt)
                print(judge_output_str)

                final_assessment = (
                    judge_output_str.split("<final_evaluation>")[-1]
                    .split("</final_evaluation>")[0]
                    .strip()
                )
                judge_outputs[file] = {
                    "judge_text": judge_output_str,
                    "final_assessment": json.loads(final_assessment),
                }
            except:
                continue


while len(judge_outputs) != len(json_files):
    loop_files(json_files)

# save output
with open(os.path.join(parent, config["outputs"], "privacy_judge.json"), "w") as f:
    json.dump(judge_outputs, f)
