"""ASCII-named compatibility entry for the frozen stage-3 runner."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).resolve().parent / '\u7b2c\u4e09\u9636\u6bb5\u5165\u53e3.py'), run_name='__main__')
