# check_import.py
import sys
import pathlib
import traceback

print("cwd:", pathlib.Path.cwd())
print("sys.executable:", sys.executable)
print("sys.version:", sys.version.replace("\n", " "))
print("sys.path (first 12):")
for p in sys.path[:12]:
    print("  ", p)

print("\nAttempting import setuptools and src.proxy_pool.proxy_pool ...")
try:
    import setuptools
    print("setuptools OK:", setuptools.__version__)
except Exception:
    print("setuptools import failed:")
    traceback.print_exc()

try:
    import src.proxy_pool.proxy_pool as m
    print("IMPORT OK:", m)
except Exception:
    print("src import failed:")
    traceback.print_exc()
