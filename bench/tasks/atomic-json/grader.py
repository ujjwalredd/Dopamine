import importlib.util
import pathlib
import sys
import tempfile

root = pathlib.Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("storage", root / "storage.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

with tempfile.TemporaryDirectory() as tmp:
    folder = pathlib.Path(tmp)
    target = folder / "state.json"
    original = b'{"old":true}\n'
    target.write_bytes(original)
    try:
        module.save_json(target, {"bad": object()})
    except (TypeError, OSError):
        pass
    else:
        raise AssertionError("non-serializable object accepted")
    assert target.read_bytes() == original
    assert list(folder.iterdir()) == [target]

    module.save_json(target, {"ok": [1, 2]})
    assert target.read_text(encoding="utf-8") == '{"ok": [1, 2]}'
    assert list(folder.iterdir()) == [target]
print("PASS")
