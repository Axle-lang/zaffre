"""The widgets, driven by events through the translated source: press, toggle, type, drag, tab."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from axpy.run import load
from axpy import rt
from axpy.rt import _rt_lit

z = load()
fails = []


def check(name, cond, extra=""):
    print(("ok   " if cond else "FAIL ") + name + (" " + str(extra) if extra and not cond else ""))
    if not cond:
        fails.append(name)


def ev(kind, x=0.0, y=0.0, **kw):
    return _rt_lit(z.UiEvent, None, kind=kind, x=x, y=y, **kw)


def click(view, w, dx=None, dy=None):
    b = w.bounds()
    x = b.x + (b.w / 2 if dx is None else dx)
    y = b.y + (b.h / 2 if dy is None else dy)
    view.input(ev(z.EventKind.PointerMove, x, y))
    view.input(ev(z.EventKind.PointerDown, x, y, button=0))
    view.input(ev(z.EventKind.PointerUp, x, y, button=0))
    return x, y


def key(view, k, mods=0):
    view.input(ev(z.EventKind.KeyDown, key=k, mods=mods))
    view.input(ev(z.EventKind.KeyUp, key=k, mods=mods))


def typed(view, s):
    for c in s:
        view.input(ev(z.EventKind.Text, cp=ord(c)))


def settle(view, n=30):
    for _ in range(n):
        view.update(0.016)


fonts = z.Fonts()
presses = [0]
btn = z.Button(_rt_lit(z.ButtonProps, None, label="Save"), lambda: presses.__setitem__(0, presses[0] + 1))
flag = z.Model(False)
chk = z.Checkbox("Agree", flag)
sw_model = z.Model(False)
sw = z.Switch("Dark", sw_model)
vol = z.Model(0.0)
slider = z.Slider(_rt_lit(z.SliderProps, None, min=0.0, max=1.0), vol)
text = z.Model("")
changes = []
field = z.TextField(_rt_lit(z.FieldProps, None, placeholder="Name"), text, lambda s: changes.append(s))
page = z.Column(_rt_lit(z.FlexProps, None, gap=10.0, padding=z.Insets.all(20.0), width=z.Length.Px(400.0)),
                [btn, chk, sw, slider, field])
view = z.View(z.Theme.dark(), fonts, page)
view.resize(480.0, 400.0)
settle(view)
view.layout()

# press
click(view, btn)
check("button press fires once", presses[0] == 1, presses)
b = btn.bounds()
view.input(ev(z.EventKind.PointerDown, b.x + 5, b.y + 5))
view.input(ev(z.EventKind.PointerUp, b.x + 600, b.y + 5))
check("press released outside does not fire", presses[0] == 1, presses)

# toggles
click(view, chk)
check("checkbox click sets model", flag.get() is True)
click(view, chk)
check("checkbox click again clears", flag.get() is False)
click(view, sw)
check("switch click sets model", sw_model.get() is True)

# keyboard: focus by Tab, activate with Space
view.input(ev(z.EventKind.PointerMove, 470.0, 390.0))
view.ctx.clearFocus()
key(view, z.Key.Tab)
key(view, z.Key.Space)
check("tab focuses the first control and space presses it", presses[0] == 2, presses)
key(view, z.Key.Tab)
key(view, z.Key.Space)
check("second tab reaches the checkbox", flag.get() is True)

# slider
x, y = click(view, slider)
check("slider click lands near the middle", 0.3 < vol.get() < 0.7, vol.get())
sb = slider.bounds()
view.input(ev(z.EventKind.PointerDown, sb.x + sb.w * 0.25, sb.y + sb.h / 2))
view.input(ev(z.EventKind.PointerMove, sb.x + sb.w * 5, sb.y + sb.h / 2))
check("drag beyond the end clamps to max", vol.get() == 1.0, vol.get())
view.input(ev(z.EventKind.PointerUp, sb.x + sb.w * 5, sb.y))
view.input(ev(z.EventKind.PointerMove, sb.x + sb.w / 2, sb.y + sb.h / 2))
key(view, z.Key.Home) if False else None

# text field
click(view, field)
typed(view, "Ada")
check("typing fills the model", text.get() == "Ada", text.get())
typed(view, "é€")
check("non-ASCII typing", text.get() == "Adaé€", text.get())
key(view, z.Key.Backspace)
check("backspace removes one codepoint", text.get() == "Adaé", text.get())
key(view, z.Key.Left)
key(view, z.Key.Left)
typed(view, "X")
check("caret movement then insert", text.get() == "AdXaé", text.get())
key(view, z.Key.A, z.Mod.CTRL)
typed(view, "ok")
check("select all then type replaces", text.get() == "ok", text.get())
key(view, z.Key.A, z.Mod.CTRL)
key(view, z.Key.C, z.Mod.CTRL)
key(view, z.Key.End)
key(view, z.Key.V, z.Mod.CTRL)
check("copy then paste", text.get() == "okok", text.get())
check("onChange fired", changes and changes[-1] == "okok", changes[-3:])
settle(view)
view.layout()
view.render(rt.Surface(480, 400).frame())
print("FAIL %d" % len(fails) if fails else "all ok")
sys.exit(1 if fails else 0)
