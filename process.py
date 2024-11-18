import json
import re
import os

# Filename of the JSON file
json_foldername = "llms/output/nov16-gpt4o-mini"

for filename in os.listdir(json_foldername):
    if filename.endswith(".json"):
        # Extract the module number from the filename
        match = re.search(r"ideas_human_eval_(\d+)\.mlw", filename)
        if not match:
            raise ValueError("Could not extract module number from filename.")
        json_filepath = os.path.join(json_foldername, filename)
        module_number = match.group(1)
        new_module_name = f"HumanEval{module_number}"
        # new_function_name = "add"

        with open(json_filepath, 'r') as json_file:
            data = json.load(json_file)

        for idea in data.get("ideas", []):
            # Replace the module name
            idea["implementation"] = re.sub(
                r"module\s+\w+", f"module {new_module_name}", idea["implementation"]
            )
            # # Replace the result function name
            # idea["implementation"] = re.sub(
            #     r"let\s+\w+\s*\(", f"let {new_function_name}(", idea["implementation"], count=1
            # )

        # Write the updated JSON back to the file
        with open(json_filepath, 'w') as json_file:
            json.dump(data, json_file, indent=4)

        # print(f"Updated implementations in {filename} to module {new_module_name} with function name {new_function_name}.")
        print(f"Updated implementations in {filename} to module {new_module_name}")
