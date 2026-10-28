#!/usr/bin/env python3
"""把仓库同步到 Kodi 的皮肤目录。

换机器、换用户名都不用改脚本：目标路径按 Kodi 的标准位置推导。

    Windows: %APPDATA%\\Kodi\\addons\\skin.mistuary
    Linux:   ~/.kodi/addons/skin.mistuary
    macOS:   ~/Library/Application Support/Kodi/addons/skin.mistuary

用法：
    python tools/sync_to_kodi.py            # 同步
    python tools/sync_to_kodi.py --dry-run  # 只看目标路径和文件数
    python tools/sync_to_kodi.py --path D:/Kodi/addons/skin.mistuary   # 手动指定（便携版）

排除：.git / .workbuddy-ai / docs/scratch（Kodi 用不到）
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADDON_ID = "skin.mistuary"
EXCLUDE_DIRS = {".git", ".github", ".workbuddy-ai", "build"}
EXCLUDE_FILES = {".gitignore"}
EXCLUDE_PATHS = {Path("docs") / "scratch"}


def default_addons_dir() -> Path:
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA")
        if not base:
            raise SystemExit("找不到 %APPDATA%，请用 --path 手动指定 Kodi addons 目录")
        return Path(base) / "Kodi" / "addons"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Kodi" / "addons"
    return Path.home() / ".kodi" / "addons"


def iter_files():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        rel_dir = Path(dirpath).relative_to(ROOT)
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for name in filenames:
            rel = rel_dir / name
            if name in EXCLUDE_FILES:
                continue
            if any(rel == p or p in rel.parents for p in EXCLUDE_PATHS):
                continue
            yield rel


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", help="Kodi addons 目录（默认按平台推导）")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    addons = Path(args.path) if args.path else default_addons_dir()
    dest = addons / ADDON_ID
    files = list(iter_files())

    print(f"源   : {ROOT}")
    print(f"目标 : {dest}")
    print(f"文件 : {len(files)} 个")

    if args.dry_run:
        return 0

    if not addons.is_dir():
        print(f"\n✗ 目标父目录不存在：{addons}")
        print("  Kodi 没装在这里，或者这是便携版 —— 用 --path 指定 addons 目录")
        return 1

    copied = 0
    for rel in files:
        dst = dest / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, dst)
        copied += 1

    print(f"\n✓ 已同步 {copied} 个文件")
    print("  去 Kodi 里重载皮肤即可生效")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
