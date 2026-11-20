"""Render an example through the translated sources to a PNG.

    python3 tools/axpy/shot.py [gallery|weather] out.png [light]
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from axpy.run import load, ROOT
from axpy import rt

args = sys.argv[1:]
page = 1
height = None
for a in list(args):
    if a.startswith("page="):
        page = int(a[5:]); args.remove(a)
    elif a.startswith("height="):
        height = int(a[7:]); args.remove(a)
name = "gallery"
if args and args[0] in ("gallery", "weather"):
    name = args.pop(0)
out = args[0] if args else name + ".png"
light = len(args) > 1 and args[1] == "light"
sizes = {"gallery": (1360, 900), "weather": (1280, 880)}

z = load([os.path.join(ROOT, "examples", name, "src")])
view = z.buildOn(page) if name == "gallery" else z.build()
if light:
    view.darkMode().set(False)
W, H = sizes[name]
if height:
    H = height
screen = rt.Surface(W, H)
view.resize(float(W), float(H))
for i in range(1, 61):
    view.update(0.016 * i)
view.render(screen.frame())
from PIL import Image
Image.fromarray(screen.pixels_rgb()).save(out)
print("wrote", out)
