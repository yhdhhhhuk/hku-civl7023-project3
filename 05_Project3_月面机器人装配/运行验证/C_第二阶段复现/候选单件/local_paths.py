"""Resolve the existing local B modules and robot resources without handoff copies."""
from pathlib import Path
import ctypes
import os
import sys

PROJECT = Path(__file__).resolve().parents[1]
for directory in [PROJECT, PROJECT / 'B_关节与夹爪', PROJECT / 'B_基础控制与雅可比']:
    sys.path.insert(0, str(directory))


def bullet_path(path):
    """Preserve C's Windows short-path support; use native paths on macOS."""
    value = str(path)
    if os.name == 'nt' and not value.isascii():
        buffer = ctypes.create_unicode_buffer(32768)
        length = ctypes.windll.kernel32.GetShortPathNameW(value, buffer, len(buffer))
        if not length or length >= len(buffer):
            raise OSError('Cannot obtain Windows short path: ' + value)
        return buffer.value
    return value
