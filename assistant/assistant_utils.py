def extract_output(response: str, delimiter: str) -> str:
    """
    Extract the corresponding segment from response give the delimiter of that segment
    """
    if not delimiter in response:
        return ""
    output = response.split(f"<{delimiter}>")[-1].split(f"</{delimiter}>")[0]
    return output


def format_history(history: list[str]) -> str:
    """
    Format history as one string
    history is formated as [ turn1: [item1, item2, etc.], etc.]
    """
    history_str = "\n".join(history)
    return history_str
