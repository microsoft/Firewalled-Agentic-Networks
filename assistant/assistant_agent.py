from response_types import Response
import sys
from model import LLM


give_up = 5

from assistant.assistant_prompts import (
    aggregated_prompts_for_planning,
    aggregated_prompts_for_turn,
    aggregated_prompts_for_planning_naive,
    aggregated_prompts_for_turn_naive,
    start_turn_prompt,
    start_plan_prompt,
    env_delimiter,
    agent_delimiter,
    simulation_ended,
    final_output_delimiter,
    thought_summary_delimiter,
    scratch_pad_delimiter,
    initial_plan_delimiter,
    get_aggregated_prompts_for_turn_firewall,
)

from assistant.assistant_utils import extract_output, format_history


class Assistant:
    def __init__(
        self,
        user_task: str,
        external_agent_role: str,
        llm_instance: LLM,
        baseline_mode: bool = False,
        guidelines: str = "",
        use_guidelines: bool = False,
    ) -> None:
        self.user_task = user_task
        self.external_agent_role = external_agent_role
        self.llm_instance = llm_instance
        self.history = []
        self.update_history([user_task], "user_task")
        self.baseline_mode = baseline_mode
        if self.baseline_mode:
            print("I am baseline")
            self.aggregated_prompts_for_planning = aggregated_prompts_for_planning_naive
            self.aggregated_prompts_for_turn = aggregated_prompts_for_turn_naive
        else:
            self.aggregated_prompts_for_planning = aggregated_prompts_for_planning
            self.aggregated_prompts_for_turn = aggregated_prompts_for_turn

        self.guidelines, self.use_guidelines = guidelines, use_guidelines

    def update_history(self, item: list, item_type: str) -> None:
        """
        add answers to local history depending on their type
        can be user_task (at the beginning, initial_plan, assistant, environment, external_agent)
        called whenever the agent has a turn (adding its own answers), or when it receives an answer (either from the environment or externally)
        """

        if item_type == "user_task":
            self.history.append("<!-- user_task -->")
            self.history.append(f"observation: {item[0]}")

        if item_type == "initial_plan":
            self.history.append("<!-- {initial_plan} from the {AI assistant} (you) -->")
            self.history.append(f"observation: {item[0]}")

        if item_type == "assistant":
            self.history.append("<!-- from the {AI assistant} (you) -->")
            self.history.append(f"assistant_log_summary: {item[0]}")
            self.history.append(f"observation: {item[1]}")

        if item_type == "environment":
            self.history.append("<!-- from the {environment} -->")
            self.history.append(f"observation: {item[0]}")

        if item_type == "external_agent":
            self.history.append("<!-- from the {external_agent} -->")
            self.history.append(f"observation: {item[0]}")

    def generate_initial_plan(self) -> None:
        """
        Prompt the assistant to generate the initial plan
        """
        start_plan_prompt_updated = start_plan_prompt.format(
            self.user_task,
            self.external_agent_role,
            initial_plan_delimiter,
            initial_plan_delimiter,
        )
        local_prompts = [
            {"role": "system", "content": self.aggregated_prompts_for_planning}
        ]
        local_prompts += [{"role": "system", "content": start_plan_prompt_updated}]

        plan_str_output = self.llm_instance.call_model(local_prompts)
        print(plan_str_output)
        extracted_plan = extract_output(plan_str_output, initial_plan_delimiter)

        self.update_history([extracted_plan], "initial_plan")
        return plan_str_output, extracted_plan

    def process_received_turn(self, PreviousResponse):
        """
        add the previous received turn to the local history
        either add as external_agent output or environment output
        """
        if PreviousResponse.type == "external_agent_return":
            self.update_history([PreviousResponse.answer], "external_agent")

        elif PreviousResponse.type == "environment_return":
            self.update_history([str(PreviousResponse.answer)], "environment")

    def process_agent_turn(
        self, output_text: str, make_history_update: bool = True
    ) -> Response:
        """
        extracts and processes the agent's own turn
        first, extracts assistant_log_summary
        second, check if the simulation has ended, if not if the answer is to {environment} or to {external_agent}
        if {environment}, extracts environment request
        if {external_agent}, extract text
        return None if none of that exists
        """

        assistant_log_summary = extract_output(output_text, thought_summary_delimiter)
        if simulation_ended in output_text:
            if make_history_update:
                self.update_history(
                    [
                        assistant_log_summary,
                        "task ended",
                    ],
                    "assistant",
                )
            final_output = extract_output(output_text, final_output_delimiter)
            turn_response = Response(
                type="assistant_return",
                answer=simulation_ended + "\n\n Final output:" + final_output,
            )
            if make_history_update:
                self.update_history(
                    [assistant_log_summary, simulation_ended], "assistant"
                )
            return turn_response

        if env_delimiter in output_text:
            env_request = extract_output(output_text, env_delimiter)
            assert env_request != None

            turn_response = Response(
                type="to_environment",
                answer=env_request,
            )
            if make_history_update:
                self.update_history(
                    [
                        assistant_log_summary,
                        f"output to the {{environment}}: {env_request}",
                    ],
                    "assistant",
                )
            return turn_response

        if agent_delimiter in output_text:
            external_agent_segment = extract_output(output_text, agent_delimiter)
            assert external_agent_segment != None

            if make_history_update:
                self.update_history(
                    [
                        assistant_log_summary,
                        f"output to the {{external_agent}}: {external_agent_segment}",
                    ],
                    "assistant",
                )
            turn_response = Response(
                type="to_external_agent", answer=external_agent_segment
            )
            return turn_response

        return None

    def generate_turn(self, PreviousResponse: Response | None = None) -> None:

        if PreviousResponse:
            self.process_received_turn(PreviousResponse)

        current_history = format_history(self.history)
        start_turn_prompt_updated = start_turn_prompt.format(
            self.user_task, self.external_agent_role, current_history
        )

        local_prompts = [
            {"role": "system", "content": self.aggregated_prompts_for_turn}
        ]
        local_prompts += [{"role": "system", "content": start_turn_prompt_updated}]

        turn_response = None
        for i in range(0, give_up):
            turn_output_str = self.llm_instance.call_model(local_prompts)
            print(turn_output_str)
            turn_response = self.process_agent_turn(turn_output_str)
            if turn_response:
                break

        if turn_response == None:
            print(f"Failed to get correct format after {give_up} trials. Exiting.")
            sys.exit()

        if self.guidelines and self.use_guidelines and "to" in turn_response.type:
            assistant_log_summary = self.history[-2]
            self.history = self.history[0:-3]
            last_output_observation = turn_response.answer
            entity = turn_response.type.split("to_")[1]

            aggregated_prompts_for_turn_firewall = (
                get_aggregated_prompts_for_turn_firewall(
                    user_task=self.user_task,
                    external_agent_role=self.external_agent_role,
                    history=current_history,
                    last_output_thought_summary=assistant_log_summary,
                    last_output_thought_observation=last_output_observation,
                    last_output_address=entity,
                    guidelines=self.guidelines,
                )
            )

            local_prompts = [
                {"role": "system", "content": aggregated_prompts_for_turn_firewall}
            ]
            turn_output_str = self.llm_instance.call_model(local_prompts)
            print("\n\n================= After Firewall correction =================")
            print(turn_output_str)
            turn_response = self.process_agent_turn(turn_output_str)

        return turn_response, turn_output_str
