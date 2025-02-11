def format_new_history_item(
    ai_assistant_input: str, thought_summary: str, tool_return: str
) -> str:
    """
    Format new history items as inputs from the AI assistant and the output of the user_environment
    """
    new_item = f"""
    <!-- from the {{AI assistant}} -->
    Input: {ai_assistant_input}

    <!-- from the {{user_environment}} (you) -->
    simulator_log_summary: {thought_summary}.
    observation: {tool_return}.
    """
    return new_item


def extract_output(
    output_str: str, thought_summary_delimiter: str, tool_return_delimiter: str
) -> tuple[str, str]:
    """
    Extracts the thought_summary and tool_return from the answer.
    It assumes the model has used the correct formatting of <delimiter> </{delimiter}>
    """

    thought_summary = output_str.split(f"<{thought_summary_delimiter}>")[-1].split(
        f"</{thought_summary_delimiter}>"
    )[0]
    tool_return = output_str.split(f"<{tool_return_delimiter}>")[-1].split(
        f"</{tool_return_delimiter}>"
    )[0]
    return thought_summary, tool_return
