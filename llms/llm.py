from __future__ import annotations

import time
from dataclasses import dataclass

import openai
from loguru import logger

from util import Util


@dataclass
class LLM:
    model: str
    litellm_url: str | None
    master_key: str | None
    temperature: int

    def _call_llm(self, messages: MessagesIterable) -> str | None:
        logger.info(f"Calling LLM with model={self.model}")
        model = self.model
        client = openai.OpenAI(
            api_key=self.master_key,
            base_url=self.litellm_url,
        )

        retry_attempts = Util.retry_attempts
        for attempt in range(retry_attempts):
            try:
                response = client.chat.completions.create(
                    model=model,
                    response_format={"type": "json_object"},
                    messages=messages,
                    temperature=self.temperature
                )

                llm_output = response.choices[0].message.content
                if llm_output is None:
                    logger.warning("output of LLM is None")
                    return None
                return llm_output

            except openai.APITimeoutError as e:
                logger.warning(f"API timeout error: {e}. Retrying {attempt + 1}/{retry_attempts}...")
                time.sleep(Util.short_sleep)  # brief wait before retrying
            except openai.APIConnectionError as e:
                logger.warning(f"Connection error: {e}. Retrying {attempt + 1}/{retry_attempts}...")
                time.sleep(Util.short_sleep)  # brief wait before retrying
            except openai.InternalServerError as e:
                logger.warning(f"Internal server error: {e}. Retrying {attempt + 1}/{retry_attempts}...")
                time.sleep(Util.short_sleep)  # brief wait before retrying
            except openai.RateLimitError as e:
                logger.warning(f"Rate limit error: {e}. Retrying {attempt + 1}/{retry_attempts}...")
                time.sleep(Util.short_sleep * (attempt + 1) * 2)  # long wait before retrying
            except openai.UnprocessableEntityError as e:
                logger.warning(f"Unprocessable entity error: {e}. Retrying {attempt + 1}/{retry_attempts}...")
                time.sleep(Util.short_sleep)  # brief wait before retrying
            except openai.OpenAIError as e:
                # do not retry in this case
                logger.warning(f"General OpenAI API error: {e}.")
                return None

        return None
