import pathlib, subprocess, sys
workspace = pathlib.Path(sys.argv[1]).resolve()
verifier = pathlib.Path('/Users/ujjwalreddyks/Desktop/Dopamine/bench/vendor/skillsbench/tasks/dialogue-parser/verifier/test_outputs.py')
result = subprocess.run([sys.executable, "-m", "pytest", "-q", str(verifier)], cwd=workspace, text=True, capture_output=True)
print(result.stdout, end="")
print(result.stderr, end="")
raise SystemExit(result.returncode)
