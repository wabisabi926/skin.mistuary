"""xbt_tool 解包边界测试：路径穿越、绝对路径、畸形容器。

运行：python -m unittest discover -s tools -p 'test_*.py'
"""

import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # xbt_tool.py 与本文件同目录

import xbt_tool  # noqa: E402
from PIL import Image  # noqa: E402  xbt_tool 顶层已依赖 PIL


def build_xbt(entries, fmt=None):
    """把 [(name, w, h, bgra_bytes)] 拼成 XBT v2 容器（未压缩帧）。"""
    if fmt is None:
        fmt = xbt_tool.XB_FMT_A8R8G8B8
    count = len(entries)
    offset = 9 + sum(264 + 40 for _ in entries)
    metas = []
    for name, w, h, raw in entries:
        metas.append((name, w, h, len(raw), len(raw), offset))
        offset += len(raw)

    out = bytearray(b"XBTF2" + struct.pack("<I", count))
    for name, w, h, packed, unpacked, off in metas:
        out += name.encode("utf-8")[:255].ljust(256, b"\x00")
        out += struct.pack("<II", 0, 1)                 # loop, 帧数
        out += struct.pack("<III", w, h, fmt)
        out += struct.pack("<QQ", packed, unpacked)
        out += struct.pack("<I", 0)                     # duration
        out += struct.pack("<Q", off)
    for _, _, _, raw in entries:
        out += raw
    return bytes(out)


class SafeTargetTests(unittest.TestCase):
    def test_rejects_parent(self):
        with tempfile.TemporaryDirectory() as tmp:
            for bad in ("../escaped.png", "a/../../b.png", "..\\escaped.png"):
                with self.assertRaises(ValueError, msg=bad):
                    xbt_tool._safe_target(tmp, bad)

    def test_rejects_absolute(self):
        with tempfile.TemporaryDirectory() as tmp:
            for bad in ("/abs.png", "\\\\server\\share\\x.png", "C:/x.png"):
                with self.assertRaises(ValueError, msg=bad):
                    xbt_tool._safe_target(tmp, bad)

    def test_rejects_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                xbt_tool._safe_target(tmp, "")

    def test_allows_nested(self):
        with tempfile.TemporaryDirectory() as tmp:
            got = xbt_tool._safe_target(tmp, "shapes/round4.png")
            self.assertTrue(got.endswith("round4.png"))
            self.assertTrue(got.startswith(str(Path(tmp).resolve())))


class UnpackBoundaryTests(unittest.TestCase):
    def _write(self, tmp, data):
        path = Path(tmp) / "in.xbt"
        path.write_bytes(data)
        return str(path)

    def test_rejects_traversal_entry(self):
        data = build_xbt([("../escaped.png", 1, 1, b"\x00\x00\x00\xff")])
        with tempfile.TemporaryDirectory() as tmp:
            src = self._write(tmp, data)
            out = Path(tmp) / "extracted"
            with self.assertRaises(ValueError):
                xbt_tool.unpack(src, str(out))
            self.assertFalse((Path(tmp) / "escaped.png").exists())

    def test_unpacks_nested_entry(self):
        data = build_xbt([("shapes/ok.png", 1, 1, b"\x00\x00\x00\xff")])
        with tempfile.TemporaryDirectory() as tmp:
            src = self._write(tmp, data)
            out = Path(tmp) / "extracted"
            xbt_tool.unpack(src, str(out))
            self.assertTrue((out / "shapes" / "ok.png").exists())

    def test_unpacks_opaque_jpeg_entry(self):
        """media/ 下确实有 .jpg（osd/nara/music-background.jpg）。

        XBT 里的帧统一是 RGBA，直接 save 会让 Pillow 走 JPEG 编码器并抛
        "cannot write mode RGBA as JPEG"。全不透明时应转 RGB 存回 .jpg。
        """
        data = build_xbt([("osd/bg.jpg", 1, 1, b"\x00\x00\x00\xff")])
        with tempfile.TemporaryDirectory() as tmp:
            src = self._write(tmp, data)
            out = Path(tmp) / "extracted"
            xbt_tool.unpack(src, str(out))
            got = out / "osd" / "bg.jpg"
            self.assertTrue(got.exists())
            with Image.open(got) as im:
                self.assertEqual(im.mode, "RGB")

    def test_jpeg_entry_with_alpha_falls_back_to_png(self):
        """带真实透明的条目存不进 JPEG，应改存同名 .png 而不是崩掉。"""
        data = build_xbt([("osd/bg.jpg", 1, 1, b"\x00\x00\x00\x80")])
        with tempfile.TemporaryDirectory() as tmp:
            src = self._write(tmp, data)
            out = Path(tmp) / "extracted"
            xbt_tool.unpack(src, str(out))
            self.assertFalse((out / "osd" / "bg.jpg").exists())
            got = out / "osd" / "bg.png"
            self.assertTrue(got.exists())
            with Image.open(got) as im:
                self.assertEqual(im.mode, "RGBA")

    def test_rejects_truncated_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = self._write(tmp, b"XBTF2\x01")
            with self.assertRaises(ValueError):
                xbt_tool.unpack(src, str(Path(tmp) / "out"))

    def test_rejects_truncated_entry(self):
        data = build_xbt([("a.png", 1, 1, b"\x00\x00\x00\xff")])[:200]
        with tempfile.TemporaryDirectory() as tmp:
            src = self._write(tmp, data)
            with self.assertRaises(ValueError):
                xbt_tool.unpack(src, str(Path(tmp) / "out"))

    def test_rejects_huge_dimension(self):
        data = build_xbt([("a.png", 99999, 1, b"\x00\x00\x00\xff")])
        with tempfile.TemporaryDirectory() as tmp:
            src = self._write(tmp, data)
            with self.assertRaises(ValueError):
                xbt_tool.unpack(src, str(Path(tmp) / "out"))

    def test_rejects_frame_offset_outside_file(self):
        data = bytearray(build_xbt([("a.png", 1, 1, b"\x00\x00\x00\xff")]))
        # 帧数据的 data_off 指向文件之外（条目头 9 起，data_off 在 +32 处）
        struct.pack_into("<Q", data, 9 + 256 + 8 + 12 + 8 + 4, 10 ** 9)
        with tempfile.TemporaryDirectory() as tmp:
            src = self._write(tmp, bytes(data))
            with self.assertRaises(ValueError):
                xbt_tool.unpack(src, str(Path(tmp) / "out"))


if __name__ == "__main__":
    unittest.main()
