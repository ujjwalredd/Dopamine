import importlib.util
import pathlib
import sys
import tempfile

root = pathlib.Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("notes", root / "notes.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

with tempfile.TemporaryDirectory() as tmp:
    parent = pathlib.Path(tmp)
    base = parent / "notes"
    nested = base / "nested"
    nested.mkdir(parents=True)
    (nested / "ok.txt").write_text("ok", encoding="utf-8")
    secret = parent / "secret.txt"
    secret.write_text("secret", encoding="utf-8")
    assert module.read_note(base, "nested/ok.txt") == "ok"

    for attack in ("../secret.txt", str(secret)):
        try:
            module.read_note(base, attack)
        except (ValueError, PermissionError):
            pass
        else:
            raise AssertionError(f"escape accepted: {attack}")

    link = base / "link.txt"
    link.symlink_to(secret)
    try:
        module.read_note(base, "link.txt")
    except (ValueError, PermissionError):
        pass
    else:
        raise AssertionError("symlink escape accepted")
print("PASS")
