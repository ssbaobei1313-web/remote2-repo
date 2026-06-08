import sys
import pathlib
import traceback

print('cwd:', pathlib.Path.cwd())
print('sys.path (first 12):')
for p in sys.path[:12]:
    print('  ', p)

try:
    import src.proxy_pool.proxy_pool as m
    print('IMPORT OK:', m)
except Exception:
    traceback.print_exc()
