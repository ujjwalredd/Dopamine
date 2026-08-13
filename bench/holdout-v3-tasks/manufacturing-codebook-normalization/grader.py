import pathlib, subprocess, sys, tempfile
workspace = pathlib.Path(sys.argv[1]).resolve()
source = pathlib.Path('/Users/ujjwalreddyks/Desktop/Dopamine/bench/vendor/skillsbench/tasks/manufacturing-codebook-normalization/verifier/test_outputs.py')
text = source.read_text(encoding='utf-8')
replacements = {'/app/output': 'output', '/app/data': 'data'}
for old, relative in replacements.items():
    text = text.replace(old, str(workspace / relative))
with tempfile.TemporaryDirectory(prefix='dopamine-verifier-') as temp:
    adapted = pathlib.Path(temp) / 'test_outputs.py'
    adapted.write_text(text, encoding='utf-8')
    result = subprocess.run([sys.executable, '-m', 'pytest', '-q', str(adapted)], cwd=workspace, text=True, capture_output=True)
print(result.stdout, end='')
print(result.stderr, end='')
raise SystemExit(result.returncode)
