"""The Axle text pipeline, run, against FreeType: glyph ids, advances, kerning and coverage."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import freetype
import numpy as np
from axpy.run import load, ROOT
from axpy import rt

z = load()
TEXT = "Hamburgefonstiv QWxyz 0123456789 @&%$ àéîõü ÀÉ – ¿ ß Æ g y j"
FONTS = ["InstrumentSans-Regular.ttf", "InstrumentSans-Bold.ttf", "JetBrainsMono-Regular.ttf"]
bad = 0
for fname in FONTS:
    path = os.path.join(ROOT, "assets", "fonts", fname)
    f = z.Font.fromFile(path)
    assert f.isValid(), fname
    face = freetype.Face(path)
    for px in (11, 13, 16, 24, 48):
        face.set_char_size(int(px * 64))
        worst = 0; mean = 0.0; n = 0
        for ch in dict.fromkeys(TEXT):
            if ch == " ":
                continue
            g = f.glyphOf(ord(ch))
            gi = face.get_char_index(ord(ch))
            if g != gi:
                print("glyph mismatch", fname, ch, g, gi); bad += 1; continue
            face.load_glyph(gi, freetype.FT_LOAD_NO_HINTING | freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_NORMAL)
            bm = face.glyph.bitmap
            adv = f.advanceOf(g, px)
            if abs(adv - face.glyph.linearHoriAdvance / 65536.0) > 0.01:
                print("advance", fname, ch, px, adv, face.glyph.linearHoriAdvance / 65536.0); bad += 1
            e = f.entry(g, px, 0)
            if e < 0:
                print("no entry", ch); bad += 1; continue
            w, h = f.ew[e], f.eh[e]
            L, T = f.eleft[e], f.etop[e]
            mine = rt._heap[f.arena + f.eoff[e]: f.arena + f.eoff[e] + w * h].astype(int).reshape(h, w)
            X0 = min(L, face.glyph.bitmap_left); Y0 = min(-T, -face.glyph.bitmap_top)
            X1 = max(L + w, face.glyph.bitmap_left + bm.width); Y1 = max(-T + h, -face.glyph.bitmap_top + bm.rows)
            A = np.zeros((Y1 - Y0, X1 - X0), int); B = np.zeros_like(A)
            A[-T - Y0:-T - Y0 + h, L - X0:L - X0 + w] = mine
            if bm.rows and bm.width:
                ref = np.array(bm.buffer, dtype=int).reshape(bm.rows, bm.pitch)[:, :bm.width]
                B[-face.glyph.bitmap_top - Y0:-face.glyph.bitmap_top - Y0 + bm.rows, face.glyph.bitmap_left - X0:face.glyph.bitmap_left - X0 + bm.width] = ref
            mine, ref = A, B
            d = np.abs(mine - ref)
            if d.size:
                worst = max(worst, d.max()); mean += d.mean(); n += 1
        print("%-28s %2dpx worst %3d mean %.2f" % (fname, px, worst, mean / max(n, 1)))
print("FAIL" if bad else "ok", bad)
sys.exit(1 if bad else 0)
