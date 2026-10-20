"""Render an example through the translated sources to a PNG.

    python3 tools/axpy/shot.py [gallery|weather] out.png [light]
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from axpy.run import load, ROOT
from axpy import rt

args = sys.argv[1:]
name = "gallery"
if args and args[0] in ("gallery", "weather"):
    name = args.pop(0)
out = args[0] if args else name + ".png"
light = len(args) > 1 and args[1] == "light"
sizes = {"gallery": (1040, 1080), "weather": (1280, 880)}

z = load([os.path.join(ROOT, "examples", name, "src")])
view = z.build()
if light:
    view.darkMode().set(False)
W, H = sizes[name]
screen = rt.Surface(W, H)
view.resize(float(W), float(H))
for i in range(1, 61):
    view.update(0.016 * i)
view.render(screen.frame())
from PIL import Image
Image.fromarray(screen.pixels_rgb()).save(out)
print("wrote", out)
