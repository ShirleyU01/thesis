import subprocess
import re
from parse_script import parse_result

result = subprocess.run(
    ['./script.sh', '-L', 'human_eval_test', 'execute', 'human_eval_test/human_eval_031.mlw', '--use=TestHumanEval031', 'test()'],
    capture_output=True,
    text=True
)
print(result.stderr)
r = parse_result(result.stdout)

def test(output : str) :
    if output == "Passed!":
        return
    prompt_revise = f"""
    For the given implementation, some of testcases failed. Here are the list of failed testcases:
    {output} 
    Please revise the current implementation to fix the problem.
    """
    return prompt_revise

print(test(r))