import ast
import importlib.util
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
source = (root / "auth.py").read_text(encoding="utf-8")
tree = ast.parse(source)
calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
assert any(
    isinstance(call.func, ast.Attribute)
    and call.func.attr == "compare_digest"
    for call in calls
), "hmac.compare_digest not used"

spec = importlib.util.spec_from_file_location("auth", root / "auth.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
assert module.verify_token("secret", "secret") is True
assert module.verify_token("secret", "other") is False
assert module.verify_token(b"secret", "secret") is False
assert module.verify_token(None, "secret") is False
print("PASS")
