# tests/conftest.py
import sys
from pathlib import Path

# 将项目根目录加入 sys.path，确保 pytest 能导入 src 包
ROOT = Path(__file__).resolve().parents[1]
ROOT_STR = str(ROOT)
if ROOT_STR not in sys.path:
    sys.path.insert(0, ROOT_STR)
