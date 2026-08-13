import importlib.util
import pathlib
import sys
import tempfile

root = pathlib.Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("reports", root / "reports.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

with tempfile.TemporaryDirectory() as tmp:
    path = pathlib.Path(tmp) / "tx.csv"
    path.write_text("id,amount_cents,status\n1,100,completed\n2,50,failed\n3,-20,completed\n", encoding="utf-8")
    assert module.summarize_transactions(path) == {"completed_count": 2, "completed_cents": 80}

    path.write_text("id,status\n1,completed\n", encoding="utf-8")
    try:
        module.summarize_transactions(path)
    except ValueError:
        pass
    else:
        raise AssertionError("missing column accepted")

    path.write_text("id,amount_cents,status\n1,nope,completed\n", encoding="utf-8")
    try:
        module.summarize_transactions(path)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid completed amount accepted")

for forbidden in ("requirements.txt", "pyproject.toml", "Pipfile"):
    assert not (root / forbidden).exists(), f"dependency manifest added: {forbidden}"
print("PASS")
