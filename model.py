import os
import torch
from openai import AzureOpenAI, OpenAI
from transformers import AutoTokenizer, pipeline, AutoModelForCausalLM, AutoConfig
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential


class LLM:
    def __init__(
        self,
        llm_name: str,
        config: dict,
        # hf_model=None,
        # hf_tokenizer=None,
        # hf_pipeline_gen=None,
    ):
        """
        Class for LLMs

        llm_name: name of the llm
        config: dict of params
        if open source hf model is used, pass hf_model, hf_tokenizer, hf_pipeline_gen
        """
        # self.hf_model, self.hf_tokenizer, self.hf_pipeline_gen = (
        #     hf_model,
        #     hf_tokenizer,
        #     hf_pipeline_gen,
        # )
        self.llm_name = llm_name
        self.config = config

        if "gpt" in self.llm_name.lower() and self.config.get("openai", False):
            # if model is GPT, create a GPTLLMOpenAI instance
            self.llm = GPTLLMOpenAI(self.llm_name, self.config)
        elif "gpt" in self.llm_name.lower() and self.config.get("azure", False):
            # if model is GPT, create a GPTLLM instance
            self.llm = GPTLLM(self.llm_name, self.config)
        elif self.config.get("local_llm", False):
            # if open source tool and hf, local_llm should be true
            self.llm = LocalOpenLLM(
                self.llm_name,
                self.config,
                # self.hf_model,
                # self.hf_tokenizer,
                # self.hf_pipeline_gen,
            )
        else:
            # load model from azure
            self.llm = AzureLLM(self.llm_name, self.config)

    def call_model(self, messages: list) -> str:
        """Calls the LLM model with the given messages.

        Returns:
            str: The response from the LLM.
        """
        return self.llm.call_model(messages)


class LocalOpenLLM:
    """Open LLM model with HF."""

    def __init__(
        self,
        llm_name: str,
        config: dict,
        # hf_model=None,
        # hf_tokenizer=None,
        # hf_pipeline_gen=None,
    ):
        self.llm_name = llm_name
        self.max_new_tokens = config["max_new_tokens"]
        self.top_p = config["llm_top_p"]

        self.hf_model, self.hf_tokenizer, self.hf_pipeline_gen = self.setup_hf_llm(self.llm_name, "", self.max_new_tokens)

        # self.hf_model, self.hf_tokenizer, self.hf_pipeline_gen = (
        #     hf_model,
        #     hf_tokenizer,
        #     hf_pipeline_gen,
        # )

    @staticmethod
    def setup_hf_llm(model_name, cache_dir ="", max_new_tokens=10000):
        """
        Sets up a Hugging Face model and tokenizer, caching it for future use.
        """
        config = AutoConfig.from_pretrained(
            model_name,
            use_cache=True,
            cache_dir=os.path.join(cache_dir, model_name),
            device_map="auto",
        )
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            config=config,
            cache_dir=os.path.join(cache_dir, model_name),
            device_map="auto",
            # torch_dtype=torch.bfloat16,
        )
        model.eval()
        tokenizer = AutoTokenizer.from_pretrained(model_name, use_cache=True)
        tokenizer.pad_token = tokenizer.eos_token
        pipeline_gen = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=max_new_tokens,
            return_full_text=False,
        )
        return model, tokenizer, pipeline_gen

    def call_model(self, messages: list) -> str:
        """Calls the LLM model with the given messages.

        Returns:
            str: The response from the LLM.
            bool: Whether the tool was called.
        """

        model_input = self.hf_tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        output_text = self.hf_pipeline_gen(
            model_input, do_sample=True, top_p=self.top_p
        )[0]["generated_text"]
        return output_text


class AzureLLM:
    """Open LLM model with Azure API."""

    def __init__(self, llm_name, config: dict):
        self.llm_name = llm_name
        self.max_new_tokens = config["max_new_tokens"]
        self.top_p = config["llm_top_p"]

        self.open_source_client = ChatCompletionsClient(
            endpoint=os.getenv("AZURE_OPEN_SOURCE_ENDPOINT"),
            credential=AzureKeyCredential(os.getenv("AZURE_OPEN_SOURCE_API_KEY")),
        )

    def call_model(self, messages: list) -> str:

        payload = {
            "messages": messages,
            "max_tokens": self.max_new_tokens,
            "top_p": self.top,
        }
        response = self.open_source_client.complete(payload)
        output_text = response.choices[0].message.content

        return output_text


class GPTLLM:
    """GPT LLM model."""

    def __init__(self, llm_name: str, config: dict):
        self.llm_name = llm_name
        self.max_new_tokens = config["max_new_tokens"]
        self.top_p = config["llm_top_p"]

        self.client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2024-02-15-preview",
        )

    def call_model(self, messages) -> str:
        """Calls the LLM model with the given messages.

        Returns:
            str: The response from the LLM.
            bool: Whether the tool was called.
        """

        response = self.client.chat.completions.create(
            model=self.llm_name,
            messages=messages,
            top_p=self.top_p,
        )

        output_text = response.choices[0].message.content

        return output_text


class GPTLLMOpenAI:
    """GPT LLM model."""

    def __init__(self, llm_name: str, config: dict):
        self.llm_name = llm_name
        self.top_p = config["llm_top_p"]
        self.max_new_tokens = config["max_new_tokens"]

        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def call_model(self, messages) -> str:
        """Calls the LLM model with the given messages.

        Returns:
            str: The response from the LLM.
            bool: Whether the tool was called.
        """

        response = self.client.chat.completions.create(
            model=self.llm_name,
            messages=messages,
            top_p=self.top_p,
            max_tokens=self.max_new_tokens,
        )

        output_text = response.choices[0].message.content.encode('utf-8', errors='ignore').decode('utf-8')

        return output_text
