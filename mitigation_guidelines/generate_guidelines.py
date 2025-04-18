import sys
import json
import os
from data_guidelines_prompts import (
    guidelines_tag,
    data_guidelines_prompt,
    previous_guidelines_prompt,
    data_output_format,
    input_format,
)

from trajectory_guidelines_prompts import (
    trajectory_guidelines_prompt,
    trajectory_output_format,
)

from build_language_prompt import (
    build_language_prompt,
    language_tag,
    building_language_input_format,
    building_language_output_format,
    previous_template_prompt,
)

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)

sys.path.append(parent)
from model import LLM
from utils import load_config


# load configs
config = load_config(os.path.join(current, "guidelines_config.yaml"))

# load llm instance
llm_instance = LLM(llm_name=config["llm_name"], config=config)

if config["guidelines_type"] == "data":
    guidelines_prompt = data_guidelines_prompt
    output_format = data_output_format
    tag = guidelines_tag
    input_format = input_format
    previous = previous_guidelines_prompt
elif config["guidelines_type"] == "input":
    guidelines_prompt = build_language_prompt
    output_format = building_language_output_format
    tag = language_tag
    input_format = building_language_input_format
    previous = previous_template_prompt
elif config["guidelines_type"] == "trajectory":
    guidelines_prompt = trajectory_guidelines_prompt
    output_format = trajectory_output_format
    tag = guidelines_tag
    input_format = input_format
    previous = previous_guidelines_prompt

if config["prev_guidelines_file"] and config["use_prev_guidelines_file"]:
    with open(config["prev_guidelines_file"], "r") as file:
        prev_guidelines = file.read()
else:
    prev_guidelines = ""


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


benign_files = [
    file
    for file in os.listdir(os.path.join(parent, config["outputs_benign"]))
    if ".json" in file and "judge.json" not in file
]

malicious_files = [
    file
    for file in os.listdir(os.path.join(parent, config["outputs_malicious"]))
    if (".json" in file and "judge.json" not in file)
]

if len(malicious_files) < len(benign_files):
    malicious_files = malicious_files * 2


for i in range(len(benign_files)):
    print("========")
    benign_file = benign_files[i]
    malicious_file = malicious_files[i]

    benign_output = json.load(
        open(os.path.join(parent, config["outputs_benign"], benign_file))
    )
    malicious_output = json.load(
        open(os.path.join(parent, config["outputs_malicious"], malicious_file))
    )

    benign_history = get_history(benign_output)
    malicious_history = get_history(malicious_output)

    if config["guidelines_type"] == "input":
        input_format_populated = [input_format.format(benign_history)]
    else:
        input_format_populated = [
            input_format.format(config["user_task"], benign_history, malicious_history)
        ]

    prompt = guidelines_prompt

    for conv in input_format_populated:
        if prev_guidelines:
            previous_guidelines_prompt_populated = previous.format(prev_guidelines)
            prompt_conv = prompt + previous_guidelines_prompt_populated
        else:
            prompt_conv = prompt

        prompt_conv = prompt_conv + conv

        prompt_conv = prompt_conv + output_format

        prompt_conv = [{"role": "system", "content": prompt_conv}]

        guidelines_output_str = llm_instance.call_model(prompt_conv)
        print(guidelines_output_str)

        prev_guidelines = (
            guidelines_output_str.split(f"<{tag}>")[-1].split(f"</{tag}>")[0].strip()
        )
        print("========")

    with open(f"{config['guidelines_type']}_guidelines.txt", "w") as f:
        f.write(prev_guidelines)
