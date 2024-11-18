import re
import os

file_folder = 'human_eval_test'

for filename in os.listdir(file_folder):
    if filename.endswith(".mlw"):
        file_path = os.path.join(file_folder, filename)
        with open(file_path, 'r') as file:
            content = file.read()
            updated_content = re.sub(
                r'\(\* Todo: Put the implementation from ChatGPT here \*\)(.|\n)*?(?=module TestHumanEval)',
                '',
                content
            )
        with open(file_path, 'w') as file:
            file.write(updated_content)


print("Content between markers deleted successfully.")
