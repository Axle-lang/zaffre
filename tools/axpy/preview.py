"""Render a widget built in Python from the translated library: a quick look at one component.

    python3 tools/axpy/preview.py out.png [light]  < builder.py
The builder defines `make(z, lit)` returning a widget; `z` is the translated library and
`lit(Struct, **fields)` builds a props struct with its defaults.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from axpy.run import load
from axpy import rt
from axpy.rt import _rt_lit

out = sys.argv[1]
light = len(sys.argv) > 2 and sys.argv[2] == "light"
ns = {}
exec(sys.stdin.read(), ns)
z = load()
lit = lambda S, **kw: _rt_lit(S, None, **kw)
widget = ns["make"](z, lit)
W, H = ns.get("SIZE", (900, 700))
view = z.View(z.Theme.dark(), z.Fonts(), z.Model(not light), widget)
if light:
    view.darkMode().set(False)
screen = rt.Surface(W, H)
view.resize(float(W), float(H))
for i in range(1, 40):
    view.update(0.016 * i)
view.render(screen.frame())
from PIL import Image
Image.fromarray(screen.pixels_rgb()).save(out)
print("wrote", out)
