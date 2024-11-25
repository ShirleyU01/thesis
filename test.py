import subprocess
result = subprocess.run(
        ['./script.sh', '-L', 'human_eval_test', 'execute', 'llms/implementation/nov16-gpt4o-samples5/human_eval_057_5.mlw', '--use=TestHumanEval139', 'test()'],
        capture_output=True,
        text=True
    )

print(result.stderr)
