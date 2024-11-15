import json
import time
from datetime import datetime
from dataclasses import dataclass
from loguru import logger
from util import (
    MessageType,
    MessagesIterable,
    Ideas,
    Idea,
    Util,
)
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionFunctionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)
from llm import LLM

description = """def sum_product(numbers: List[int]) -> list [int]:
    For a given list of integers, return a tuple consisting of a sum and a product of all the integers in a list.
    Empty sum should be equal to 0 and empty product should be equal to 1.
    >>> sum_product([])
    [0, 1]
    >>> sum_product([1, 2, 3, 4])
    [10, 24]
    """

@dataclass
class IdeasGeneration():
    nb_ideas: int # number of ideas
    attempts: int # number of attempts
    llm: LLM # LLM object

    def _create_system_prompt(self):
        return """
        You are an expert software engineer with experience in software verification.
        You have extensive experience in writing code in Why3.
        You are a creative developer that can find different ways of implementing the same idea in Why3.
        You always provide an output in valid JSON.
        The resulting JSON object should be in this format:
        {
        "ideas": [
            {
            "description" : "string",
            "implementation" : "string"
            },
            {
            "description" : "string",
            "implementation" : "string"
            },
            {
            "description" : "string",
            "implementation" : "string"
            }
            ]
        }
        """

    def _create_user_prompt(self, description : str, example : str, nb_ideas: int) -> str:
        prompt_functionality_brainstorming = f"""
        Given a description of problem, it is possible to implement it in different ways. For instance, consider loops, recursions, 
        pattern matching, and different branching conditions. Here is an example of {nb_ideas} different algorithms for one example description:
        `{example}`
        According to the following description `{description}`, please generate {nb_ideas} different ways that a developer might implement 
        using why3. Try to make sure that the ways of implementation is as diverse as possible. Describe the high-level behavior 
        and expected outcomes and how you would like to implement them. 
        <instructions>
        Create a JSON object with your ideas for implementation.
        The parent object is called "ideas" that corresponds to Why3 implementation ideas.
        Each child object has the implementation idea with the following properties:
        - A property named "description" with the description of your implementation idea
        - A property named "implementation" with an implementation of your idea
        There must be {nb_ideas} children, each corresponding to one implementation idea.
        </instructions>
        """
        print(prompt_functionality_brainstorming)
        return prompt_functionality_brainstorming

    def _query_llm(self, messages: MessagesIterable) -> Ideas | None:

        current_messages = list(messages)

        retry_attempts = self.attempts
        for attempt in range(retry_attempts):
            try:
                llm_output = ""
                llm_call = self.llm._call_llm(current_messages)
                if llm_call is None:
                    return None
                llm_output = llm_call

                logger.info(f"output prompt tokens: {Util.count_tokens(llm_output, self.llm.model)}")
                logger.debug(f"LLM output in JSON: {llm_output}")

                # Parse the JSON string into a dictionary
                data = json.loads(llm_output)

                # Convert JSON into a list of Idea objects
                idea_contents = [Idea(**item) for item in data["ideas"]]

                # Access ideas
                for idea in idea_contents:
                    print(f"Description: {idea.description}")
                    print(f"Implementation:\n{idea.implementation}")
                    print("-----")

                return Ideas(ideas=idea_contents)

            except json.JSONDecodeError as e:
                logger.warning(f"Failed to decode JSON: {e}. Retrying {attempt + 1}/{retry_attempts}...")
                current_messages = list(messages)
                current_messages.append(ChatCompletionAssistantMessageParam(role="assistant", content=llm_output))
                error_message = (
                    f"The JSON is not valid. Failed to decode JSON: {e}."
                    "Please fix the issue and return a fixed JSON.")
                current_messages.append(ChatCompletionUserMessageParam(role="user", content=error_message))

            except KeyError as e:
                logger.warning(f"Missing expected key in JSON data: {e}. Retrying {attempt + 1}/{retry_attempts}...")
                current_messages = list(messages)
                current_messages.append(ChatCompletionAssistantMessageParam(role="assistant", content=llm_output))
                error_message = (f"The JSON is not valid. Missing expected key in JSON data: {e}."
                                "Please fix the issue and return a fixed JSON.")
                current_messages.append(ChatCompletionUserMessageParam(role="user", content=error_message))

            except TypeError as e:
                logger.warning(f"Unexpected type encountered: {e}. Retrying {attempt + 1}/{retry_attempts}...")
                current_messages = list(messages)
                current_messages.append(ChatCompletionAssistantMessageParam(role="assistant", content=llm_output))
                error_message = (f"The JSON is not valid. Unexpected type encountered: {e}."
                                "Please fix the issue and return a fixed JSON.")
                current_messages.append(ChatCompletionUserMessageParam(role="user", content=error_message))

            # Wait briefly before retrying
            time.sleep(Util.short_sleep)

        return None

    def _get_ideas(self) -> Ideas | None:
        system_prompt = self._create_system_prompt()

        example_file = open('prompt/example.txt', 'r')
        example = example_file.read()
        user_prompt = self._create_user_prompt(description, example, self.nb_ideas)

        logger.debug(f"user prompt tokens: {Util.count_tokens(user_prompt, self.llm.model)}")
        logger.debug(f"system prompt tokens: {Util.count_tokens(system_prompt, self.llm.model)}")

        messages: MessagesIterable = []
        system_message = ChatCompletionSystemMessageParam(role="system", content=system_prompt)
        user_message = ChatCompletionUserMessageParam(role="user", content=user_prompt)
        messages.append(system_message)
        messages.append(user_message)

        return self._query_llm(messages)

        
    def run(self):
        ideas = self._get_ideas()
        if ideas is not None:
            try:
                # Generate filename with current date and time
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filename = f"ideas_{timestamp}.json"

                with open(filename, "w") as file:
                    # Write ideas to the file in JSON format
                    json.dump(ideas.to_dict(), file, indent=4)
                print(f"Ideas successfully written to {filename}")
            except Exception as e:
                print(f"Error writing ideas to file: {e}")
        else:
            print("No ideas to write.")    







