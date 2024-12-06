#################################################################################
# replace the placeholder with ChatGPT generation
# create new mlw in `implementation` folder

import os
import json
import re

# Define the base directory containing JSON files
json_folder = "llms/output/dec5-gpt4o-basic+all"
mlw_folder = "human_eval_test"  
result_folder = "llms/implementation/dec5-gpt4o-basic+all"
os.makedirs(result_folder, exist_ok=True)

# Iterate through JSON files in the folder
for filename in os.listdir(json_folder):
    if filename.endswith(".json"):
        # Extract the MLW file name from the JSON file name
        match = re.match(r"ideas_(human_eval_\d+)\.mlw.*\.json", filename)
        if match:
            mlw_name = match.group(1) + ".mlw"
            mlw_path = os.path.join(mlw_folder, mlw_name)
            json_path = os.path.join(json_folder, filename)

            # Read the JSON content
            with open(json_path, 'r') as json_file:
                try:
                    data = json.load(json_file)

                    # Extract the content you want to append
                    count = 1
                    for idea in data.get('ideas', []):
                        implementation = idea['implementation']
                        output_file_path = os.path.join(result_folder, f"{match.group(1)}_{count}.mlw")

                        # Append to the corresponding MLW file
                        if os.path.exists(mlw_path):
                            with open(mlw_path, 'r') as file:
                                content = file.read()
                            placeholder = "(* INSERT_CHATGPT_CODE *)"
                            if placeholder in content:
                                updated_content = content.replace(placeholder, placeholder + "\n\n" + implementation)
                            else:
                                raise ValueError("Placeholder not found in the file.")
                            with open(output_file_path, 'w') as mlw_file:
                                mlw_file.write(updated_content)
                            print(f"Content from {filename} added to {mlw_name}.")
                        else:
                            print(f"MLW file {mlw_name} does not exist. Skipping.")
                        count += 1
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON from file {filename}: {e}")
        

        



# # Read the existing MLW file
# with open('human_eval_test/human_eval_005.mlw', 'r') as file:
#     content = file.read()

# # Find the position of the placeholder and insert implementations
# placeholder = "(* Todo: Put the implementation from ChatGPT here *)"
# if placeholder in content:
#     updated_content = content.replace(placeholder, placeholder + "\n\n" + implementations_text)
# else:
#     raise ValueError("Placeholder not found in the file.")

# # Write the updated content back to the file
# with open('human_eval_test/human_eval_005.mlw', 'w') as file:
#     file.write(updated_content)

# print("Implementations added successfully!")

