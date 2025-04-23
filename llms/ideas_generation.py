import os
import json
import time
import csv
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
    description: str # description of the problem
    filename: str # filename
    function_name: str
    module_name: str
    signature: str
    level: int
    verified_file: str

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

    def _create_system_prompt_verification(self):
        return """
        You are an expert software engineer with experience in software verification.
        You have extensive experience in writing code in Why3.
        You have a background in formal methods and are an expert in verification.
        Given an implementation of a function in Why3 and a contract it must satisfy, you always verify the code.
        You can verify the code by adding variants, invariants, lemmas, ghost code, and assertions.
        The code must be verified automatically by SMT solvers.
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

    def idea_diversity(self, description : str, example : str, nb_ideas: int) -> str:
        prompt_functionality_brainstorming = f"""<instructions-diversity>
        Given a description of problem, it is possible to implement it in different ways. For instance, consider loops, recursions,
        pattern matching, and different branching conditions. Here is an example of {nb_ideas} different algorithms for one example description:
        `{example}`
        </instructions-diversity>
        """
        #print(prompt_functionality_brainstorming)
        return prompt_functionality_brainstorming

    def implement(self) -> str:
        prompt_implementation = f"""
        Implement the functionality described above using why3. Ensure that the implementation
        is syntax-error free, clear, and easy to test. The implementation should focus on
        achieving the high-level behavior described, while not implementating specification."""
        print(prompt_implementation)
        return prompt_implementation

    def implement(self, int_lib : str, int_function : str, list_lib : str, list_function : str) -> str:
        prompt_implementation = f"""
        <instructions-library-syntax>
        When implementing code in Why3 ensure that the implementation
        is syntax-error free, clear, and easy to test. Pay attention to correct library usage. For instance,
        if the implementation uses function length from list module, please include it correctly as `use list.Length`.
        
        To provide a boarder sense of available libraries, functions, and correct way of using them, here are two tables
        for why3 library List and Int, which summarizes function name (Function), function module (Module), 
        function type (Type), function description (Description), and correct way of import (Import Statement):
        
        why3 library List information:
        `{list_lib}`
        
        why3 library int information:
        `{int_lib}`
        
        Consider the min line in the library int:
        min,MinMax,int -> int -> int,Returns the smaller of two integers.,use int.MinMax        
        How to read this line is as follows: 
        min - function name that you can use in your program
        MinMax - module where the function exists
        int -> int -> int - this function takes as input two integers and returns an integer
        Returns the smaller of two integers. - description of what the function does
        use int.MinMax - import you must use if you want to use the min function in your program

        When importing the corresponding modules you should only use the following list functions:
        `{list_function}

        When importing the corresponding modules you should only use the following int functions:
        `{int_function}

        Remove unnecessary comments and don't implement specification. The implementation should focus on
        achieving the high-level behavior described.
        </instructions-library-syntax>
        """
        return prompt_implementation

    def _create_user_prompt_verification(self, description : str, implementation : str, function_name: str) -> str:
        implementation_file = open(implementation, 'r')
        implementation_output = implementation_file.read()

        prompt_verification = f"""
        <instructions-verification>
        Consider the following implementation in Why3:
        <implementation>
        {implementation_output}
        </implementation>
        This code implements `{description}`.
        This implementation is assumed to be correct since it passed a set of test cases.
        You want to verify this code such that the `{function_name}` satisfies the postconditions defined by the ensures clauses.
        Do not change the implementation.
        Do not change the postcondition of `{function_name}`.
        If needed, you can add variants to `{function_name}` to prove termination.
        Variants can only be added after a function declaration if it is recursive.
        Variants can only be added to loops if they are while loops.
        If neded, if you can also add loop invariants and assertions to `{function_name}`.
        You can add pre- and postconditions to other functions.
        You can also add lemmas and ghost code if needed to prove the corresponding lemmas.
        Only add lemmas if you think it is necessary since they may be hard to prove.
        If you are declaring a ghost variable you can use `let ghost`.
        Note that lemmas must be proven automatically by SMT solvers.
        Return the full code with the specifications to automatically verify it.
        </instructions-verification>
        """
        
        prompt_json_instructions = f"""
        <instructions-json>
        Create a JSON object with your verified code.
        The parent object is called "ideas" that corresponds to Why3 verified code.
        Each child object has the verified code with the following properties:
        - A property named "description" with the description of your verification idea
        - A property named "implementation" with the verified code
        There must be 1 children, each corresponding to one verified code.
        </instructions-json>
        """

        # syntax_example_file = open('../prompt/syntax.txt', 'r')
        # syntax_example = syntax_example_file.read()

        # prompt_syntax = f"""
        # <instructions-syntax>
        # When implementing code in Why3 please take into consideration the following syntax:
        # {syntax_example}
        # </instructions-syntax>
        # """

        verification_example_file = open('../prompt/example-verified.txt', 'r')
        verification_example = verification_example_file.read()

        prompt_examples = f"""
        <instructions-verification-examples>
        {verification_example}
        </instructions-verificaton-examples>
        """
        
        #print(prompt_functionality_brainstorming)
        prompt_all = prompt_verification + prompt_json_instructions
        if self.level == 6:
            prompt_all = prompt_verification + prompt_json_instructions + prompt_examples
            print("Prompt options: Verification Basic + Example")
        else:
            prompt_all = prompt_verification + prompt_json_instructions
            print("Prompt options: Verification Basic")
        print(prompt_all)
        return prompt_all    

    def _create_user_prompt(self, description : str, example : str, function_name: str, module_name: str, signature: str, nb_ideas: int) -> str:
        prompt_implementation_diversity = self.idea_diversity(description, example, nb_ideas)
        
        prompt_implementation = f"""
        <instructions-implementation>
        According to the following description `{description}`, please generate {nb_ideas} different ways that a developer might implement
        using why3. Try to make sure that the ways of implementation is as diverse as possible. Describe the high-level behavior
        and expected outcomes and how you would like to implement them.
        The function to be implemented must be called `{function_name}` and must be inside of a module called `{module_name}`.
        Note that the signature of the function `{function_name}` is `{signature}`.
        You must use either this signature of their recursive version.
        </instructions-implementation>
        """
        
        prompt_json_instructions = f"""
        <instructions-json>
        Create a JSON object with your ideas for implementation.
        The parent object is called "ideas" that corresponds to Why3 implementation ideas.
        Each child object has the implementation idea with the following properties:
        - A property named "description" with the description of your implementation idea
        - A property named "implementation" with an implementation of your idea
        There must be {nb_ideas} children, each corresponding to one implementation idea.
        </instructions-json>
        """

        unique_int_functions = set()
        int_lib_file = open('../prompt/lib_summary_int.csv', 'r')
        int_lib = csv.reader(int_lib_file)
        int_lib_str = ''
        for row in int_lib:
            int_lib_str += ', '.join(row) + '\n'
            unique_int_functions.add(row[0])

        unique_list_functions = set()
        list_lib_file = open('../prompt/lib_summary_list.csv', 'r')
        list_lib = csv.reader(list_lib_file)
        list_lib_str = ''
        for row in list_lib:
            list_lib_str += ', '.join(row) + '\n'
            unique_list_functions.add(row[0])
  
        int_functions = ",".join(sorted(unique_int_functions))   
        list_functions = ",".join(sorted(unique_list_functions))   

        prompt_library = self.implement(int_lib_str, int_functions, list_lib_str, list_functions)
        
        syntax_example_file = open('../prompt/syntax.txt', 'r')
        syntax_example = syntax_example_file.read()

        prompt_syntax = f"""
        <instructions-syntax>
        When implementing code in Why3 please take into consideration the following syntax:
        {syntax_example}
        </instructions-syntax>
        """
        

        #print(prompt_functionality_brainstorming)
        prompt_all = prompt_implementation + prompt_json_instructions
        if self.level == 1:
            prompt_all = prompt_implementation + prompt_json_instructions + prompt_syntax
            print("Prompt options: Basic + Syntax")
        elif self.level == 2:
            prompt_all = prompt_implementation + prompt_json_instructions + prompt_library
            print("Prompt options: Basic + Library")
        elif self.level == 3:
            prompt_all = prompt_implementation + prompt_json_instructions + prompt_implementation_diversity
            print("Prompt options: Basic + Diversity")
        elif self.level == 4:
            prompt_all = prompt_implementation + prompt_json_instructions + prompt_syntax + prompt_library + prompt_implementation_diversity
            print("Prompt options: Basic + Syntax + Library + Diversity")
        else:
            prompt_all = prompt_implementation + prompt_json_instructions
            print("Prompt options: Basic")
        print(prompt_all)
        return prompt_all

    import os

    def _write_string_to_file(self, directory, filename, content):
        # Ensure the directory exists
        os.makedirs(directory, exist_ok=True)
        
        # Full file path
        file_path = os.path.join(directory, filename)

        # Write the string to the file
        with open(file_path, 'w') as f:
            f.write(content)

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
                    directory = os.path.dirname(self.verified_file)
                    filename = "verified_" + os.path.basename(self.verified_file)
                    # Example usage
                    self._write_string_to_file(directory, filename, idea.implementation)
                    #print(f"filename: {self.verified_file}")
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

    def _get_ideas(self, description, example) -> Ideas | None:
        system_prompt = self._create_system_prompt()
        user_prompt = self._create_user_prompt(description, example, self.function_name, self.module_name, self.signature, self.nb_ideas)

        logger.debug(f"user prompt tokens: {Util.count_tokens(user_prompt, self.llm.model)}")
        logger.debug(f"system prompt tokens: {Util.count_tokens(system_prompt, self.llm.model)}")

        messages: MessagesIterable = []
        system_message = ChatCompletionSystemMessageParam(role="system", content=system_prompt)
        user_message = ChatCompletionUserMessageParam(role="user", content=user_prompt)
        messages.append(system_message)
        messages.append(user_message)

        return self._query_llm(messages)

    def _get_verification(self, description, implementation) -> Ideas | None:
        system_prompt = self._create_system_prompt_verification()
        user_prompt = self._create_user_prompt_verification(description, implementation, self.function_name)

        logger.debug(f"user prompt tokens: {Util.count_tokens(user_prompt, self.llm.model)}")
        logger.debug(f"system prompt tokens: {Util.count_tokens(system_prompt, self.llm.model)}")

        messages: MessagesIterable = []
        system_message = ChatCompletionSystemMessageParam(role="system", content=system_prompt)
        user_message = ChatCompletionUserMessageParam(role="user", content=user_prompt)
        messages.append(system_message)
        messages.append(user_message)

        return self._query_llm(messages)

        
    def run(self):
        example_file = open('../prompt/example.txt', 'r')
        example = example_file.read()
        
        ideas = self._get_ideas(self.description, example)
        if ideas is not None:
            try:
                # Generate filename with current date and time
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filename = f"ideas_{self.filename}_{timestamp}.json"

                with open(filename, "w") as file:
                    # Write ideas to the file in JSON format
                    json.dump(ideas.to_dict(), file, indent=4)
                print(f"Ideas successfully written to {filename}")
            except Exception as e:
                print(f"Error writing ideas to file: {e}")
        else:
            print("No ideas to write.")

    def run_verification(self, implementation):
        self.verified_file = implementation
        ideas = self._get_verification(self.description, implementation)
        if ideas is not None:
            try:
                # Generate filename with current date and time
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filename = f"ideas_{self.filename}_{timestamp}.json"

                with open(filename, "w") as file:
                    # Write ideas to the file in JSON format
                    json.dump(ideas.to_dict(), file, indent=4)
                print(f"Ideas successfully written to {filename}")
            except Exception as e:
                print(f"Error writing ideas to file: {e}")
        else:
            print("No ideas to write.")        







