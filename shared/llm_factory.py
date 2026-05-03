# shared/llm_factory.py - centralized LLM construction.
# All agents should obtain LLM instances here instead of initializing their own.

import os
from shared.constants import LLM_MODEL_NAME, LLM_TEMPERATURE


def get_llm():
    """
    Select and return the configured LLM instance from LLM_PROVIDER.
    Supported providers: deepseek | qwen | openai | anthropic.
    """
    provider = os.getenv("LLM_PROVIDER", "deepseek").lower()

    if provider == "deepseek":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=os.getenv("LLM_MODEL_NAME", LLM_MODEL_NAME),
            temperature=LLM_TEMPERATURE,
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com/v1",
        )

    elif provider == "qwen":
        from langchain_community.chat_models.tongyi import ChatTongyi

        return ChatTongyi(
            model=os.getenv("LLM_MODEL_NAME", "qwen-max"),
            temperature=LLM_TEMPERATURE,
            dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"),
        )

    elif provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=os.getenv("LLM_MODEL_NAME", "gpt-4o"),
            temperature=LLM_TEMPERATURE,
            api_key=os.getenv("OPENAI_API_KEY"),
        )

    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=os.getenv("LLM_MODEL_NAME", "claude-sonnet-4-6"),
            temperature=LLM_TEMPERATURE,
            api_key=os.getenv("ANTHROPIC_API_KEY"),
        )

    else:
        raise ValueError(
            f"Unknown LLM_PROVIDER: '{provider}'. "
            "Set it in .env to deepseek / qwen / openai / anthropic."
        )
