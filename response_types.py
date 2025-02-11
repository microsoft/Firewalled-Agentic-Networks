class Response:
    """
    if the output from assistant to user_environment, type is: to_environment
    if the output from user_environment to assistant, type is: environment_return

    if the output from assistant to external agent, type is: to_external_agent
    if the output from external agent to assistant, type is: external_agent_return

    if the output from assistant and end of simulation, type is: assistant_return

    answer: is always the extracted part in the output

    """

    def __init__(
        self,
        type: str,
        answer: str,
    ) -> None:
        self.type = type
        self.answer = answer
