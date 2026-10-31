# -*- coding: utf-8 -*-
"""检查 / 清理 Kodi 收藏夹里的同名重复条目。

用法（**先退出 Kodi**，否则 Kodi 退出时会把内存里的列表写回去，覆盖你的修改）：

    python tools/dedupe_favourites.py            # 只报告，不改文件
    python tools/dedupe_favourites.py --fix      # 去掉同名重复（保留第一条），改前自动备份

为什么需要它：Kodi 的「添加到收藏夹」是内置动作，皮肤无法拦截。
同名的两个不同节点（例如 Emby 的「标签-华语电影」和「合集-华语电影」）各收藏一次，
列表里就会出现两张同名卡；皮肤只能照条目数渲染，没法去重。
"""
import argparse
import os
import shutil
import sys
import time
import xml.etree.ElementTree as ET


def favourites_path():
    if sys.platform.startswith("win"):
        base = os.path.join(os.environ.get("APPDATA", ""), "Kodi")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support/Kodi")
    else:
        base = os.path.expanduser("~/.kodi")
    return os.path.join(base, "userdata", "favourites.xml")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", action="store_true", help="去掉同名重复（保留第一条）")
    ap.add_argument("--path", default=None, help="手动指定 favourites.xml")
    args = ap.parse_args()

    path = args.path or favourites_path()
    if not os.path.exists(path):
        print("找不到收藏夹文件：%s" % path)
        return 1

    tree = ET.parse(path)
    root = tree.getroot()
    items = list(root)

    print("收藏夹：%s" % path)
    print("条目数：%d" % len(items))

    seen = {}
    dup = []
    for i, el in enumerate(items):
        name = el.get("name", "")
        action = (el.text or "").strip()
        seen.setdefault(name, []).append(i)
        print("  [%d] %-20s %s" % (i, name, action))

    for name, idxs in seen.items():
        if len(idxs) > 1:
            dup.append((name, idxs))

    if not dup:
        print("\n没有同名重复条目。")
        return 0

    print("\n同名重复：")
    for name, idxs in dup:
        print("  「%s」出现 %d 次（第 %s 条）" % (name, len(idxs), "、".join(str(i) for i in idxs)))
        for i in idxs:
            print("      -> %s" % (items[i].text or "").strip())

    if not args.fix:
        print("\n只报告，未改动。加 --fix 去掉重复（保留每组第一条）。")
        return 0

    drop = set()
    for name, idxs in dup:
        drop.update(idxs[1:])

    backup = "%s.bak-%s" % (path, time.strftime("%Y%m%d-%H%M%S"))
    shutil.copy2(path, backup)
    print("\n已备份：%s" % backup)

    for i in sorted(drop, reverse=True):
        root.remove(items[i])
    tree.write(path, encoding="utf-8", xml_declaration=True)
    print("已删除 %d 条重复，剩余 %d 条。重启 Kodi 生效。" % (len(drop), len(root)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
