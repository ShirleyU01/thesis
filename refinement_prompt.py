import pandas as pd
import re

# extract the implementation code chunk 
# input : the entire code
# output : the code chunk that only contains CHATGPT implementation
def extract_code(content):
    pattern = re.compile(r"\(\*\s*INSERT_CHATGPT_CODE\s*\*\)(.*?)module\s+TestHumanEval", re.DOTALL | re.IGNORECASE)
    match = pattern.search(content)

    if match:
        extracted_code = match.group(1).strip()
        # print("SUCCESS")
        return extracted_code
    else:
        return "No matching code found."

output_folder = "dec5-gpt4o-basic+all/" # the folder of GPT result that we want to do the refinement loop 
output_table_path = "llms/compile/"+ output_folder + "info.csv"

df = pd.read_csv(output_table_path)

# for those with failed testcases
# input: csv file called info.csv which contains the compile output
# output: the list of prompts for those implementations which compiled but failed on some testcases
def prompt_testcase_failed (df) :
    failed_df = df[df["Error"].astype(str).str.contains("TestCases", na=False)]
    prompt_list = []
    for _, row in failed_df.iterrows():
        implementation = row["Implementation"]
        implementation_file_path = "llms/implementation/" + output_folder + implementation
        with open(implementation_file_path, "r", encoding="utf-8") as f:
            implementation_content = f.read()
        error_info = row["Error"]
        lines = error_info.splitlines() 
        lines = lines[2:]         
        error_info = "\n".join(lines).lstrip("\n") 
        # print(implementation_content)
        # print(error_info)
        implementation_content = extract_code(implementation_content)
        prompt = f""" For this implementation 
        {implementation_content}
        The code compiles but fails on the following testcases:
        {error_info}

        Please consider those situations and fix the code.
        """
        # print(prompt)
        prompt_list.append(prompt)
    return prompt_list

# for those that cannot compile
# input: csv file called info.csv which contains the compile output
# output: the list of prompts for those implementations which failed to compile 
def prompt_compile_failed(df):
    failed_df = df[~df["Error"].astype(str).str.contains("TestCases", na=False) & 
                 (df["Complie"].astype(str) != "[]")]
    prompt_list = []
    for _, row in failed_df.iterrows():
        implementation = row["Implementation"]
        implementation_file_path = "llms/implementation/" + output_folder + implementation
        with open(implementation_file_path, "r", encoding="utf-8") as f:
            implementation_content = f.read()
        implementation_content = extract_code(implementation_content)
        error_info = row["Error"]
        prompt = f""" For this implementation 
        {implementation_content}
        The code was unable to compile in Why3, and Why3 gives the following error message:
        {error_info}

        Please consider those situations and fix the code.
        """
        # print(prompt)
        prompt_list.append(prompt)
    return prompt_list

prompt_testcase_failed (df) 
prompt_compile_failed(df)