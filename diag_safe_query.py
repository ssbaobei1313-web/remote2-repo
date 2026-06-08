import sys, importlib, inspect, os
root = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))
srcdir = os.path.join(root, "src")
if srcdir not in sys.path:
    sys.path.insert(0, srcdir)

print("PYTHONPATH first entries:", sys.path[:3])
try:
    pkg = importlib.import_module("core")
    print("import core OK, core.__file__:", getattr(pkg, "__file__", None))
except Exception as e:
    print("import core FAILED:", repr(e))

try:
    m = importlib.import_module("core.safe_query")
    print("import core.safe_query OK")
    print("module file:", getattr(m, "__file__", None))
    print("has bulk_query:", hasattr(m, "bulk_query"))
    print("names containing 'bulk':", [n for n in dir(m) if "bulk" in n])
    print("type of safe_query attr:", type(getattr(m, "safe_query", None)).__name__)
    try:
        src = inspect.getsource(m)
        print("module source starts with:", src[:300].replace("\\n","\\n"))
    except Exception as e:
        print("inspect.getsource error:", repr(e))
except Exception as e:
    print("import core.safe_query FAILED:", repr(e))
