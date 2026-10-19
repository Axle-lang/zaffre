"""Render the gallery through the translated sources to a PNG: `python3 tools/axpy/shot.py out.png [dark|light]`."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from axpy.run import load, ROOT
from axpy import rt

z = load([os.path.join(ROOT, "examples", "gallery", "src")])
view = z.build()
if len(sys.argv) > 2 and sys.argv[2] == "light":
    view.darkMode().set(False)
W, H = 1040, 1080
screen = rt.Surface(W, H)
view.resize(float(W), float(H))
for i in range(1, 61):
    view.update(0.016 * i)
view.render(screen.frame())
from PIL import Image
Image.fromarray(screen.pixels_rgb()).save(sys.argv[1] if len(sys.argv) > 1 else "gallery.png")
print("wrote")
