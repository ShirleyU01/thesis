#################################################################################
# compile generated implementation with testcases

import subprocess
import re
from parse_script import parse_result
import os
import pandas as pd

def parse_string(s):
    parts = s.split('_')[:-1]
    result = ''.join(part.capitalize() for part in parts)
    return result

def test(output : str) :
    if output == "Passed!":
        return
    prompt_revise = f"""
    For the given implementation, some of testcases failed.
    """
    #Here are the list of failed testcases:
    #{output} 
    #Please revise the current implementation to fix the problem.
    #"""
    return prompt_revise

def is_compile_success(text):
    lines = text.strip().split("\n")[1:]  
    invalid_lines = [line for line in lines if not (line.startswith("File") or line.startswith("WARNING") or line.startswith("warning") or line.startswith("Warning"))]
    return invalid_lines

import re

def replace_function_name(code, module_name, function_name):
    # Extract the module HumanEval005
    module_match = re.search(rf"{module_name}(.*?)end", code, re.DOTALL)
    if not module_match:
        return code  
    
    module_content = module_match.group(1)
    
    # Find the last function name after the last "let" definition
    function_name_match = re.findall(r"let\s+(\w+)\s*\(", module_content)
    if not function_name_match:
        return code  # Return the original code if no function is found
    
    old_function_name = function_name_match[-1]
    new_function_name = function_name
    
    # Replace all occurrences of old_function_name with new_function_name
    updated_module_content = module_content.replace(old_function_name, new_function_name)
    
    # Replace the original module content with the updated one
    updated_code = code.replace(module_content, updated_module_content)
    return updated_code



folder_path = "llms/implementation/apr18-gpt41-mini-all-v3"
compile_folder_path = "llms/compile/apr18-gpt41-mini-all-v3"
excel_output_path = 'llms/compile/apr18-gpt41-mini-all-v3/info.csv'
data = []
os.makedirs(compile_folder_path, exist_ok=True)

# iterate every file in the folder
for filename in os.listdir(folder_path): 
    output_text = ""
    file_path = os.path.join(folder_path, filename)
    output_file_path = os.path.join(compile_folder_path, f"{filename}_output.txt") 
    module_name = parse_string(filename)
    try:
      result = subprocess.run(
          ['why3', '-L', 'human_eval_test', 'execute', file_path, f'--use=Test{module_name}', 'test()'],
          #['./thesis/script.sh', '-L', 'human_eval_test', 'execute', file_path, f'--use=Test{module_name}', 'test()'],
          capture_output=True,
          text=True,
	  timeout=10
      )
    except subprocess.TimeoutExpired:
      output_text += f"======================={filename}=====================\n" + "TIMEOUT"
      continue
    output_text += f"======================={filename}=====================\n" + result.stderr
    if not result.stderr:
        continue
    else:
        r = parse_result(result.stdout)
        failed_test = test(r)
        if failed_test:
            output_text += "=======================TestCases=====================\n" + failed_test

    
    with open(output_file_path, 'w') as output_file:
        output_file.write(output_text)

    error_msg = ''
    for line in is_compile_success(output_text):
        error_msg += line + '\n'
    data.append({
        'Implementation': filename,
        'Compile': is_compile_success(output_text),
        'Error': error_msg  
    }) 
    print(f"Output from {filename} added to {file_path}.")

df = pd.DataFrame(data)
df.to_csv(excel_output_path, index=False)
