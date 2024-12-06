import json
import re
import os
import pandas as pd


# no need for fixed prompt
def replace_function_name(code, module_name, function_name):
    # Find the last function name after the last "let" definition
    function_name_match = re.findall(r"let\s+(?:rec\s+)?(\w+)\s*\(", code, re.MULTILINE)
    if not function_name_match:
        function_name_match = re.findall(r"let rec\s+(\w+)\s*\(", code)
        if not function_name_match:
            return code  # Return the original code if no function is found
    old_function_name = function_name_match[-1]
    new_function_name = function_name
    
    # Replace all occurrences of old_function_name with new_function_name
    updated_code = code.replace(old_function_name, new_function_name)
    
    # Replace the original module content with the updated one
    updated_code = code.replace(code, updated_code)
    return updated_code


# Filename of the JSON file
json_foldername = "thesis/llms/output/nov16-gpt4o-mini"
info_filepath = "thesis/prompt/description.csv"
df = pd.read_csv(info_filepath)


for filename in os.listdir(json_foldername):
    if filename.endswith(".json"):
        # Extract the module number from the filename
        match = re.search(r"ideas_human_eval_(\d+)\.mlw", filename)
        if not match:
            raise ValueError("Could not extract module number from filename.")
        json_filepath = os.path.join(json_foldername, filename)
        module_number = match.group(1)
        new_module_name = f"HumanEval{module_number}"
        

        with open(json_filepath, 'r') as json_file:
            data = json.load(json_file)

        for idea in data.get("ideas", []):
            # Replace the module name
            idea["implementation"] = re.sub(
                r"module\s+\w+", f"module {new_module_name}", idea["implementation"]
            )
            # Replace the result function name
            function_name = df[df['filename'].str.contains(f"{module_number}", na=False)]['Function name'].tolist()[0]
            updated_implementation = replace_function_name(idea["implementation"], module_number, function_name)
            idea["implementation"] = updated_implementation

        # Write the updated JSON back to the file
        with open(json_filepath, 'w') as json_file:
            json.dump(data, json_file, indent=4)

        # print(f"Updated implementations in {filename} to module {new_module_name} with function name {new_function_name}.")
        print(f"Updated implementations in {filename} to module {new_module_name}")
