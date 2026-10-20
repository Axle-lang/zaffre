"""Draw every icon on a sheet: python3 tools/axpy/icons.py out.png"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from axpy.run import load
from axpy import rt

z = load()
out = sys.argv[1] if len(sys.argv) > 1 else "icons.png"
kinds = [k for k in z.IconKind.__members__.values()] if hasattr(z.IconKind, "__members__") else []
if not kinds:
    kinds = [getattr(z.IconKind, n) for n in dir(z.IconKind) if not n.startswith("_") and n != "None_"]
from axpy.rt import _rt_lit
cols = 9
cell = 72
rows = []
for r in range(0, len(kinds), cols):
    row = [z.IconView(k, 40.0) for k in kinds[r:r + cols]]
    rows.append(z.Row(_rt_lit(z.FlexProps, None, gap=32.0), row))
page = z.Column(_rt_lit(z.FlexProps, None, gap=28.0, padding=z.Insets.all(32.0)), rows)
W, H = cols * 72 + 64, len(rows) * 68 + 64
screen = rt.Surface(W, H)
view = z.View(z.Theme.light(), z.Fonts(), z.Model(False), page)
view.resize(float(W), float(H))
view.update(0.1)
view.render(screen.frame())
from PIL import Image
Image.fromarray(screen.pixels_rgb()).save(out)
print("kinds", len(kinds))
