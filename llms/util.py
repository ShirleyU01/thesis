from __future__ import annotations

__all__ = ("Util",)

import json
import typing as t
from dataclasses import asdict, dataclass, field

import tiktoken
from loguru import logger
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionFunctionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)


# Define the composite message type
MessageType = (ChatCompletionSystemMessageParam |
               ChatCompletionUserMessageParam |
               ChatCompletionAssistantMessageParam |
               ChatCompletionToolMessageParam |
               ChatCompletionFunctionMessageParam)

# Define the iterable of the composite message type
MessagesIterable = list[MessageType]


@dataclass
class Idea:
    description: str
    implementation: str

@dataclass
class Ideas:
    ideas: list[Idea]

    def to_dict(self):
        return {"ideas": [asdict(idea) for idea in self.ideas]}

@dataclass
class Util:
    retry_attempts: int = field(default=3)
    short_sleep: int = field(default=5)
    long_sleep: int = field(default=30)
    limit_llm_output: int = field(default=4096)

    @staticmethod
    def count_tokens(text: str, model: str) -> int:
        try:
            # Explicitly use the cl100k_base encoder
            encoding = tiktoken.get_encoding("cl100k_base")
        except KeyError as e:
            error_message = f"Failed to get encoding for the model {model}."
            raise ValueError(error_message) from e

        tokens = encoding.encode(text)
        return len(tokens)

  