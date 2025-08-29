import os
import sys


# 将项目根目录加入 sys.path，便于 "from backend..." 导入
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)




