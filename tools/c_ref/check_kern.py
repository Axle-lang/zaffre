#!/usr/bin/env python3
"""check_kern.py — GPOS pair kerning in the C twin against HarfBuzz, for every pair of a character set."""
import ctypes, os, sys
import uharfbuzz as hb

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
lib = ctypes.CDLL(os.path.join(HERE, "build", "libzt.so"))
lib.zt_open.argtypes = [ctypes.c_char_p, ctypes.c_int]
CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,:;!?'\"()-/@&%+AVTYWo"
fails = pairs = nonzero = 0
for fname in ["InstrumentSans-Regular.ttf", "InstrumentSans-Bold.ttf", "JetBrainsMono-Regular.ttf"]:
    data = open(os.path.join(ROOT, "assets", "fonts", fname), "rb").read()
    assert lib.zt_open(data, len(data)) == 1
    font = hb.Font(hb.Face(data))
    for a in CHARS:
        for b in CHARS:
            buf = hb.Buffer(); buf.add_str(a + b); buf.guess_segment_properties()
            hb.shape(font, buf, {"kern": True, "liga": False, "calt": False, "clig": False, "mark": False, "mkmk": False})
            ga, gb = lib.zt_glyph(ord(a)), lib.zt_glyph(ord(b))
            want = buf.glyph_positions[0].x_advance - lib.zt_advance(ga)
            got = lib.zt_kern(ga, gb)
            pairs += 1
            nonzero += want != 0
            if want != got:
                fails += 1
                if fails < 12:
                    print("kern differs", fname, repr(a + b), "harfbuzz", want, "mine", got)
print("pairs: %d (non-zero in harfbuzz: %d), differences: %d" % (pairs, nonzero, fails))
sys.exit(1 if fails else 0)
