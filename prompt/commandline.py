import subprocess

result = subprocess.run(
    ['/Users/weiranyu/Desktop/15414/thesis/script.sh', '-L', '/Users/weiranyu/Desktop/15414/thesis/human_eval_test', 'execute', '/Users/weiranyu/Desktop/15414/thesis/human_eval_test/human_eval_005.mlw', '--use=TestHumanEval005', 'test()'],
    capture_output=True,
    text=True
)
print(result.stdout)
print(result.stderr)
