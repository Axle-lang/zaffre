#!/usr/bin/env python3
"""check_ttf.py — the C twin of the TrueType pipeline against FreeType.

For every glyph of a string at several sizes: the codepoint -> glyph mapping, the advance, and the
rasterised coverage (unhinted) must agree with FreeType's. Coverage is allowed a small error
(both rasterisers are exact-area, but they flatten curves differently); anything bigger fails.

Known, accepted difference: where two contours of one glyph overlap inside a single pixel (an accent
touching its base, the crossing of an 8), signed-area accumulation adds the two coverages and clamps,
so that one pixel reads darker than FreeType's, which has a dedicated overlap path. The test allows a
large per-pixel maximum for exactly that and holds the mean tight.
"""
import ctypes, os, sys
import freetype

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
lib = ctypes.CDLL(os.path.join(HERE, "build", "libzt.so"))
lib.zt_raster.argtypes = [ctypes.c_int, ctypes.c_double, ctypes.c_double] + [ctypes.POINTER(ctypes.c_int)] * 4 + [ctypes.c_char_p, ctypes.c_int]
lib.zt_open.argtypes = [ctypes.c_char_p, ctypes.c_int]

TEXT = "Hamburgefonstiv QWxyz 0123456789 @&%$ àéîõü ÀÉ – ¿ ß ſ Æ ﬁ g y j"
FONTS = ["InstrumentSans-Regular.ttf", "InstrumentSans-Bold.ttf", "JetBrainsMono-Regular.ttf"]
SIZES = [11, 13, 16, 24, 48]


def mine(g, px, sub=0.0):
    w, h, l, t = (ctypes.c_int() for _ in range(4))
    buf = ctypes.create_string_buffer(400 * 400)
    ok = lib.zt_raster(g, px, sub, ctypes.byref(w), ctypes.byref(h), ctypes.byref(l), ctypes.byref(t), buf, len(buf))
    assert ok
    return w.value, h.value, l.value, t.value, bytes(buf.raw[: w.value * h.value])


def place(canvas, cw, ch, ox, oy, w, h, left, top, data, base):
    """Blit a (w,h) bitmap whose origin is `left` right of / `top` above the baseline."""
    for j in range(h):
        for i in range(w):
            x = base[0] + left + i + ox
            y = base[1] - top + j + oy
            if 0 <= x < cw and 0 <= y < ch:
                canvas[y * cw + x] = data[j * w + i]


worst = 0.0
fails = 0
total = 0
for fname in FONTS:
    path = os.path.join(ROOT, "assets", "fonts", fname)
    data = open(path, "rb").read()
    assert lib.zt_open(data, len(data)) == 1, fname
    face = freetype.Face(path)
    upm = lib.zt_units()
    assert upm == face.units_per_EM
    assert lib.zt_ascent() == face.ascender and lib.zt_descent() == face.descender, (lib.zt_ascent(), face.ascender)
    for px in SIZES:
        face.set_char_size(int(px * 64))
        for ch in dict.fromkeys(TEXT):
            if ch == " ":
                continue
            cp = ord(ch)
            g = lib.zt_glyph(cp)
            gi = face.get_char_index(cp)
            if g != gi:
                print("glyph index differs", fname, ch, g, gi); fails += 1; continue
            if g == 0:
                continue
            face.load_glyph(gi, freetype.FT_LOAD_NO_HINTING | freetype.FT_LOAD_NO_AUTOHINT | freetype.FT_LOAD_RENDER)
            adv_ft = face.glyph.metrics.horiAdvance
            adv_me = lib.zt_advance(g) * px * 64.0 / upm
            if abs(adv_ft - adv_me) > 1.5:
                print("advance differs", fname, ch, px, adv_ft, adv_me); fails += 1
            bm = face.glyph.bitmap
            fw, fh = bm.width, bm.rows
            fdata = bytes(bm.buffer) if fh else b""
            # FreeType pitch may exceed width
            fpix = bytearray(fw * fh)
            for j in range(fh):
                fpix[j * fw:(j + 1) * fw] = bytes(bm.buffer[j * bm.pitch: j * bm.pitch + fw])
            w, h, l, t, mdata = mine(g, float(px))
            S = 120
            a = bytearray(S * S); b = bytearray(S * S)
            base = (30, 80)
            place(a, S, S, 0, 0, fw, fh, face.glyph.bitmap_left, face.glyph.bitmap_top, fpix, base)
            place(b, S, S, 0, 0, w, h, l, t, mdata, base)
            diff = [abs(x - y) for x, y in zip(a, b)]
            mx = max(diff)
            mean = sum(diff) / max(1, sum(1 for x, y in zip(a, b) if x or y))
            total += 1
            worst = max(worst, mean)
            if mx > 125 or mean > 8.0:
                fails += 1
                print("coverage differs: %s %r px=%d max=%d mean=%.2f" % (fname, ch, px, mx, mean))
print("glyphs compared: %d, worst mean abs error per inked pixel: %.2f/255, failures: %d" % (total, worst, fails))
sys.exit(1 if fails else 0)
