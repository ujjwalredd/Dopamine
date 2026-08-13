import importlib.util
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("billing", root / "billing.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

assert module.compute_total(1000, 25) == 750
assert module.checkout_api(1000, 0) == 1000
assert module.invoice_job(1000, 100) == 0
for function in (module.compute_total, module.checkout_api, module.invoice_job):
    for invalid in (-1, 101, 150):
        try:
            function(1000, invalid)
        except ValueError:
            pass
        else:
            raise AssertionError(f"{function.__name__} accepted {invalid}")
print("PASS")
