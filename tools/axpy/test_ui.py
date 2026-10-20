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


_clock = [0.0]


def settle(view, n=30):
    for _ in range(n):
        _clock[0] += 0.016
        view.update(_clock[0])


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

# ── molecules ─────────────────────────────────────────────────────────────────────
seg_m, tab_m, sel_m = z.Model(0), z.Model(0), z.Model(-1)
picked = []
seg = z.Segmented(["List", "Grid", "Board"], seg_m)
sel = z.Select(_rt_lit(z.SelectProps, None, width=z.Length.Px(200.0)), ["Small", "Medium", "Large"], sel_m, lambda i: picked.append(i))
pg0 = z.Label("page zero"); pg1 = z.Label("page one")
tabs = z.Tabs(["One", "Two"], tab_m, [pg0, pg1])
rows = [z.Label("row %d" % i) for i in range(30)]
scroll = z.Scroll(_rt_lit(z.ScrollProps, None, height=z.Length.Px(120.0)), z.Column(_rt_lit(z.FlexProps, None, gap=4.0), rows))
alert = z.Alert(z.Tone.Warn, "Careful", "A rather long message that must wrap onto a second line when the box is narrow.")
page2 = z.Column(_rt_lit(z.FlexProps, None, gap=12.0, padding=z.Insets.all(20.0), width=z.Length.Px(360.0), align=z.Align.Stretch), [seg, sel, tabs, scroll, alert])
v2 = z.View(z.Theme.dark(), fonts, page2)
v2.resize(480.0, 600.0)
settle(v2); v2.layout()


def cl(v, w, fx=0.5, fy=0.5):
    b = w.bounds()
    x, y = b.x + b.w * fx, b.y + b.h * fy
    v.input(ev(z.EventKind.PointerMove, x, y)); v.input(ev(z.EventKind.PointerDown, x, y)); v.input(ev(z.EventKind.PointerUp, x, y))
    return x, y


cl(v2, seg, 0.9)
check("segmented click on the third option", seg_m.get() == 2, seg_m.get())
v2.ctx.setFocus(seg.token, True)
key(v2, z.Key.Left)
check("segmented Left moves the choice", seg_m.get() == 1, seg_m.get())
key(v2, z.Key.Left); key(v2, z.Key.Left)
check("segmented stops at the first option", seg_m.get() == 0, seg_m.get())
settle(v2, 40)
check("segmented thumb settles on the choice", abs(seg.thumb.value - 0.0) < 0.01, seg.thumb.value)

check("tabs show page zero", tabs.current() is pg0)
tb = tabs.bar; cl(v2, tb, ((tb.left[1] + tb.right[1]) / 2) / tb.bounds().w)
check("tab click chooses the second page", tab_m.get() == 1 and tabs.current() is pg1, tab_m.get())
v2.layout()
check("the page on show is laid out", pg1.bounds().w > 0 and pg1.bounds().h > 0, (pg1.bounds().w, pg1.bounds().h))

cl(v2, sel)
check("select click opens a menu overlay", v2.used == 1 and sel.isOpen.get() is True, v2.used)
v2.layout(); settle(v2, 20)
menu = v2.overlays[0]
mb = menu.sheet
check("menu sits under the field", mb.y >= sel.bounds().bottom(), (mb.y, sel.bounds().bottom()))
click_x, click_y = mb.x + 30, mb.y + 4 + 36 * 1.5
v2.input(ev(z.EventKind.PointerMove, click_x, click_y))
v2.input(ev(z.EventKind.PointerDown, click_x, click_y))
v2.input(ev(z.EventKind.PointerUp, click_x, click_y))
settle(v2, 40)
check("picking a row sets the model and tells the handler", sel_m.get() == 1 and picked == [1], (sel_m.get(), picked))
check("menu closes and is dropped", sel.isOpen.get() is False and menu.done(), (sel.isOpen.get(), menu.done()))
before = seg_m.get()
cl(v2, sel); v2.layout(); settle(v2, 20)
sb = seg.bounds()
v2.input(ev(z.EventKind.PointerDown, sb.x + sb.w * 0.9, sb.y + 5)); v2.input(ev(z.EventKind.PointerUp, sb.x + sb.w * 0.9, sb.y + 5))
settle(v2, 40)
check("a press outside closes the menu and is swallowed", sel.isOpen.get() is False and seg_m.get() == before, (sel.isOpen.get(), seg_m.get()))
cl(v2, sel); v2.layout(); settle(v2, 20)
key(v2, z.Key.Escape); settle(v2, 40)
check("Escape closes the menu", sel.isOpen.get() is False)

sbx = scroll.bounds()
v2.input(ev(z.EventKind.PointerMove, sbx.x + 20, sbx.y + 20))
v2.input(ev(z.EventKind.Wheel, sbx.x + 20, sbx.y + 20, wheel=2.0))
settle(v2, 60); v2.layout()
check("wheel scrolls the content", scroll.position() > 100.0, scroll.position())
check("scrolled rows moved up", rows[0].bounds().y < sbx.y - 50, rows[0].bounds().y)
v2.input(ev(z.EventKind.Wheel, sbx.x + 20, sbx.y + 20, wheel=1000.0)); settle(v2, 200); v2.layout()
check("scroll stops at the end", abs(scroll.position() - (scroll.contentH - sbx.h)) < 0.5, (scroll.position(), scroll.contentH - sbx.h))
check("alert wraps to the width offered", alert.bounds().h > 60.0, alert.bounds().h)
v2.render(rt.Surface(480, 600).frame())

# ── hover, and a caret that blinks ───────────────────────────────────────────────
import numpy as np
fails2 = []
hb = z.Button(_rt_lit(z.ButtonProps, None, label="Hover me", kind=z.ButtonKind.Primary))
hd = z.Button(_rt_lit(z.ButtonProps, None, label="Danger", kind=z.ButtonKind.Danger))
hm = z.Model("")
hf = z.TextField(_rt_lit(z.FieldProps, None, placeholder="Type"), hm)
hp = z.Column(_rt_lit(z.FlexProps, None, gap=16.0, padding=z.Insets.all(20.0)), [hb, hd, hf])
hv = z.View(z.Theme.dark(), fonts, hp)
hv.resize(300.0, 220.0); settle(hv); hv.layout()


def shot(v):
    s = rt.Surface(300, 220); v.render(s.frame()); return s.pixels_rgb().astype(int)


def region(img, b):
    return img[int(b.y):int(b.y + b.h), int(b.x):int(b.x + b.w)]


for name, w in (("primary", hb), ("danger", hd)):
    rest = region(shot(hv), w.bounds())
    b = w.bounds()
    hv.input(ev(z.EventKind.PointerMove, b.x + b.w / 2, b.y + b.h / 2)); settle(hv, 30)
    hot = region(shot(hv), w.bounds())
    diff = np.abs(rest - hot).mean()
    check("%s button looks different under the pointer" % name, diff > 3.0, round(float(diff), 2))
    hv.input(ev(z.EventKind.PointerMove, 290.0, 210.0)); settle(hv, 30)

# the caret: focused, idle, the loop must be told to draw again when the blink comes due
click(hv, hf); settle(hv, 40)
hv.render(rt.Surface(300, 220).frame())
check("a focused field asks to be woken", 0.0 < hv.waitSeconds() <= 0.51, hv.waitSeconds())
frames = []
t = _clock[0]
for k in range(6):
    t += 0.26
    hv.update(t)
    if hv.needsFrame():
        frames.append(round(t, 2)); hv.render(rt.Surface(300, 220).frame())
check("the blink repaints about twice a second", 2 <= len(frames) <= 4, frames); print("frames", frames)
a = shot(hv)
fb = hf.bounds()
seen = set()
for k in range(8):
    t += 0.5; hv.update(t); seen.add(region(shot(hv), fb).tobytes())
check("the caret is drawn in one phase and not the other", len(seen) == 2, len(seen))

# double and triple click in a field
dm = z.Model("alpha beta gamma")
df = z.TextField(_rt_lit(z.FieldProps, None), dm)
dv = z.View(z.Theme.dark(), fonts, z.Column(_rt_lit(z.FlexProps, None, padding=z.Insets.all(10.0), width=z.Length.Px(300.0)), [df]))
dv.resize(320.0, 80.0); settle(dv); dv.layout()
b = df.bounds()
px = b.x + 12 + 7 * 6.5     # inside "beta"
def press(clicks):
    dv.input(ev(z.EventKind.PointerMove, px, b.y + b.h / 2))
    dv.input(ev(z.EventKind.PointerDown, px, b.y + b.h / 2, clicks=clicks))
    dv.input(ev(z.EventKind.PointerUp, px, b.y + b.h / 2))
press(1)
press(2)
sel = dm.get()[min(df.anchor, df.caret):max(df.anchor, df.caret)]
check("double click selects the word", sel.strip() == "beta", repr(sel))
press(3)
check("triple click selects the line", min(df.anchor, df.caret) == 0 and max(df.anchor, df.caret) == len(dm.get().encode()))

# ── overlays: tooltip, toast, dialog ───────────────────────────────────────────────
notes = z.Notifier()
log = []
tip_btn = z.Button("Hover me")
toast_btn = z.Button("Toast", lambda: notes.toast("Saved", z.Tone.Ok))
ask_btn = z.Button("Ask", lambda: notes.ask(_rt_lit(z.DialogProps, None, title="Delete?", message="This cannot be undone, so think twice before agreeing to it.", confirm="Delete", danger=True), lambda: log.append("yes"), lambda: log.append("no")))
behind = z.Button("Behind", lambda: log.append("behind"))
opage = z.Column(_rt_lit(z.FlexProps, None, gap=10.0, padding=z.Insets.all(20.0), width=z.Length.Px(360.0)), [z.Tooltip("A short note", tip_btn), toast_btn, ask_btn, behind])
ov = z.View(z.Theme.dark(), fonts, z.Notifications(notes, opage))
ov.resize(480.0, 420.0); settle(ov); ov.layout()

def at(w, fx=0.5, fy=0.5):
    b = w.bounds(); return b.x + b.w * fx, b.y + b.h * fy

x, y = at(tip_btn)
ov.input(ev(z.EventKind.PointerMove, x, y)); settle(ov, 20)
check("no tooltip before the delay", ov.used == 0, ov.used)
settle(ov, 40)
check("a tooltip opens after the pointer rests", ov.used == 1, ov.used)
tipo = ov.overlays[0]
ov.layout()
check("the tooltip sits below its widget", tipo.sheet.y >= tip_btn.bounds().bottom(), (tipo.sheet.y, tip_btn.bounds().bottom()))
ov.input(ev(z.EventKind.PointerMove, 470.0, 410.0)); settle(ov, 40)
check("the tooltip goes when the pointer leaves", tipo.done())
ov.layout()

click(ov, toast_btn); settle(ov, 5); ov.layout()
check("a handler's toast request opens a toast", any(isinstance(o, z.Toast) for o in ov.overlays[:ov.used]) and not notes.pending())
click(ov, toast_btn); settle(ov, 5); ov.layout()
toasts = [o for o in ov.overlays[:ov.used] if isinstance(o, z.Toast) and not o.done()]
check("two toasts stack", len(toasts) == 2 and abs(toasts[0].sheet.y - toasts[1].sheet.y) >= 44, [t.sheet.y for t in toasts])
settle(ov, 400)
check("toasts leave by themselves", all(o.done() for o in ov.overlays[:ov.used] if isinstance(o, z.Toast)) and ov.ctx.toastCount == 0, ov.ctx.toastCount)

click(ov, ask_btn); settle(ov, 5); ov.layout(); settle(ov, 40)
dlg = [o for o in ov.overlays[:ov.used] if isinstance(o, z.Dialog) and not o.done()]
check("a dialog opens", len(dlg) == 1)
d = dlg[0]
check("the dialog is modal: Tab order holds only its buttons", ov.ctx.orderCount == 2, ov.ctx.orderCount)
bx, by = at(behind)
ov.input(ev(z.EventKind.PointerMove, bx, by)); ov.input(ev(z.EventKind.PointerDown, bx, by)); ov.input(ev(z.EventKind.PointerUp, bx, by))
check("a click on the page behind does nothing", "behind" not in log and not behind.hovered, log)
key(ov, z.Key.Escape); settle(ov, 40)
check("Escape cancels", log == ["no"] and d.done(), (log, d.done()))
click(ov, ask_btn); settle(ov, 5); ov.layout(); settle(ov, 40)
d2 = [o for o in ov.overlays[:ov.used] if isinstance(o, z.Dialog) and not o.done()][0]
key(ov, z.Key.Enter); settle(ov, 40)
check("Enter confirms", log == ["no", "yes"] and d2.done(), log)
click(ov, ask_btn); settle(ov, 5); ov.layout(); settle(ov, 40)
d3 = [o for o in ov.overlays[:ov.used] if isinstance(o, z.Dialog) and not o.done()][0]
cb = d3.kid[0].kids[2].kids[2]       # the confirm button of the card's last row
click(ov, cb); settle(ov, 40)
check("clicking the confirm button confirms", log == ["no", "yes", "yes"] and d3.done(), log)
click(ov, ask_btn); settle(ov, 5); ov.layout(); settle(ov, 60)
sfc = rt.Surface(480, 420); ov.render(sfc.frame())
import numpy as _np
from PIL import Image as _Image
_Image.fromarray(sfc.pixels_rgb()).save("/tmp/dialog.png")
print("FAIL %d" % len(fails) if fails else "all ok")
sys.exit(1 if fails else 0)
