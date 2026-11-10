"""Resolve the existing local B modules and robot resources without handoff copies."""
from pathlib import Path
import ctypes
import os
import sys
import hashlib
import shutil

PROJECT = Path(__file__).resolve().parents[1]
for directory in [PROJECT, PROJECT / 'B_关节与夹爪', PROJECT / 'B_基础控制与雅可比']:
    sys.path.insert(0, str(directory))


def bullet_path(path):
    """Preserve C's Windows short-path support; use native paths on macOS."""
    value = str(path)
    if os.name == 'nt' and not value.isascii():
        buffer = ctypes.create_unicode_buffer(32768)
        length = ctypes.windll.kernel32.GetShortPathNameW(value, buffer, len(buffer))
        if length and length < len(buffer) and buffer.value.isascii():
            return buffer.value
        # Volumes without 8.3 names may return the original Unicode path.
        # Bullet on Windows needs ASCII; preserve all relative mesh references.
        source = Path(path).resolve()
        cache = PROJECT.parent / '.cache' / 'bullet_assets' / hashlib.sha256(str(source.parent).encode('utf8')).hexdigest()[:16]
        if not str(cache).isascii():
            raise OSError('ASCII project parent required for Bullet cache: ' + str(cache))
        shutil.copytree(source.parent, cache, dirs_exist_ok=True)
        target = cache / source.name
        if target.read_bytes() != source.read_bytes():
            raise OSError('Bullet cache copy mismatch: ' + value)
        return str(target)
    return value
