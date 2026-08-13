import importlib.util
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("app", root / "app.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

a = module.get_user_profile(" Alice ")
b = module.get_user_profile("alice")
c = module.get_user_profile("ALICE")
assert a == {"username": "alice"}
assert a is b is c
assert len(module._CACHE) == 1
print("PASS")
