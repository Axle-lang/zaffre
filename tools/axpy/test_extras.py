"""Sortable list, transfer list, button group and split button, driven through the translated source."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from axpy.run import load
from axpy.rt import _rt_lit

z = load()
fails = []
lit = lambda S, **kw: _rt_lit(S, None, **kw)


def check(name, cond, extra=""):
    print(("ok   " if cond else "FAIL ") + name + (" " + str(extra) if extra and not cond else ""))
    if not cond:
        fails.append(name)


def ev(kind, x=0.0, y=0.0, **kw):
    return _rt_lit(z.UiEvent, None, kind=kind, x=x, y=y, **kw)


def host(widget, w=700.0, h=500.0):
    v = z.View(z.Theme.light(), z.Fonts(), z.Column(lit(z.FlexProps, padding=z.Insets.all(10.0), width=z.Length.Px(w - 20)), [widget]))
    v.resize(w, h)
    for i in range(1, 21):
        v.update(0.016 * i)
    v.layout()
    return v


def at(v, kind, x, y, **kw):
    v.input(ev(kind, x, y, **kw))


# --- Sortable ------------------------------------------------------------------------------
order = z.Order(4)
sl = z.SortableList(lit(z.SortableProps), ["a", "b", "c", "d"], order)
v = host(sl)
b = sl.bounds()
row = lambda k: b.y + k * 46.0 + 20.0
at(v, z.EventKind.PointerMove, b.x + 100, row(0))
at(v, z.EventKind.PointerDown, b.x + 100, row(0), button=0)
at(v, z.EventKind.PointerMove, b.x + 100, row(1))
at(v, z.EventKind.PointerMove, b.x + 100, row(2))
at(v, z.EventKind.PointerUp, b.x + 100, row(2), button=0)
got = [order.at(k) for k in range(4)]
check("dragging the first row down two places reorders", got == [1, 2, 0, 3], got)
order2 = z.Order(3)
order2.relocate(2, 0)
check("relocate moves back", [order2.at(k) for k in range(3)] == [2, 0, 1])

# --- Transfer ------------------------------------------------------------------------------
chosen = z.Model(0)
tl = z.TransferList(lit(z.TransferProps), ["r", "w", "x"], chosen)
v = host(tl)
def click(box):
    x, y = box.x + box.w / 2, box.y + box.h / 2
    at(v, z.EventKind.PointerMove, x, y)
    at(v, z.EventKind.PointerDown, x, y, button=0)
    at(v, z.EventKind.PointerUp, x, y, button=0)
click(tl.rowBox(0, 0))
click(tl.rowBox(0, 1))
click(tl.arrowBox(0))
check("ticked rows are carried to the right", chosen.get() == 0b011, chosen.get())
click(tl.rowBox(1, 0))
click(tl.arrowBox(1))
check("and back again", chosen.get() == 0b010, chosen.get())

# --- Group and split -----------------------------------------------------------------------
hits = []
b1 = z.Button(lit(z.ButtonProps, label="One"), lambda: hits.append(1))
b2 = z.Button(lit(z.ButtonProps, label="Two"), lambda: hits.append(2))
g = z.ButtonGroup([b1, b2])
v = host(g)
click(b2.bounds())
check("a button in a group still fires", hits == [2], hits)
picked = []
sp = z.SplitButton(lit(z.ButtonProps, label="Go"), lambda: hits.append(9), [lit(z.MenuEntry, label="A"), lit(z.MenuEntry, label="B")], lambda i: picked.append(i))
v = host(sp)
click(sp.main.bounds())
check("the main action fires", hits[-1] == 9, hits)
click(sp.caret.bounds())
for i in range(1, 30):
    v.update(1.0 + 0.016 * i)
check("the caret asks for a menu", sp.isOpen.get() is True)

# --- Times and the time picker ---------------------------------------------------------------
T = z.Times
for text, want in [("14:30", T.at(14, 30)), ("1430", T.at(14, 30)), ("2:30 pm", T.at(14, 30)), ("9", T.at(9, 0)), ("12 am", 0), ("12:05 PM", T.at(12, 5)), ("9.05", T.at(9, 5))]:
    check("parses time %r" % text, T.parse(text) == want, T.parse(text))
for text in ["", "25:00", "12:60", "13 pm", "x", "1:2:3"]:
    check("rejects time %r" % text, T.parse(text) == T.NONE, T.parse(text))
check("24-hour text", T.text(T.at(7, 5), True) == "07:05")
check("12-hour text", T.text(T.at(0, 5), False) == "12:05 AM" and T.text(T.at(15, 0), False) == "3:00 PM")
at_ = z.Model(T.NONE)
tp = z.TimePicker(lit(z.TimeProps, width=z.Length.Px(240.0)), at_)
v = host(tp)
bb = tp.bounds()
at(v, z.EventKind.PointerMove, bb.x + 30, bb.y + bb.h / 2)
at(v, z.EventKind.PointerDown, bb.x + 30, bb.y + bb.h / 2, button=0)
at(v, z.EventKind.PointerUp, bb.x + 30, bb.y + bb.h / 2, button=0)
for c in "2:45 pm":
    v.input(ev(z.EventKind.Text, cp=ord(c)))
for i in range(1, 6):
    v.update(2.0 + 0.016 * i)
check("typing a time chooses it", at_.get() == T.at(14, 45), at_.get())
panel = z.TimePanel(lit(z.TimeProps, h24=False), z.Model(T.at(14, 45)), z.Model(True))
check("a 12-hour panel has three columns", panel.columns() == 3)
check("and selects the matching entries", [panel.selectedOf(c) for c in range(3)] == [1, 9, 1], [panel.selectedOf(c) for c in range(3)])

# --- Tree ----------------------------------------------------------------------------------
nodes = [lit(z.TreeNode, label="a", depth=0), lit(z.TreeNode, label="a1", depth=1), lit(z.TreeNode, label="a2", depth=1), lit(z.TreeNode, label="b", depth=0)]
pick = z.Model(-1)
tr = z.TreeView(lit(z.TreeProps), nodes, pick)
v = host(tr)
check("a closed tree shows its roots", tr.shownCount == 2, tr.shownCount)
r = tr.rowBox(0)
at(v, z.EventKind.PointerMove, r.x + 100, r.y + 10)
at(v, z.EventKind.PointerDown, r.x + 100, r.y + 10, button=0)
at(v, z.EventKind.PointerUp, r.x + 100, r.y + 10, button=0)
check("clicking a branch picks and opens it", pick.get() == 0 and tr.shownCount == 4, (pick.get(), tr.shownCount))
v.input(ev(z.EventKind.KeyDown, key=z.Key.Down)); 
check("Down moves to the next visible row", pick.get() == 1, pick.get())
v.input(ev(z.EventKind.KeyDown, key=z.Key.Left))
check("Left on a leaf steps out to its branch", pick.get() == 0, pick.get())
v.input(ev(z.EventKind.KeyDown, key=z.Key.Left))
check("Left on an open branch closes it", tr.shownCount == 2, tr.shownCount)

# --- Colours and the range slider ---------------------------------------------------------
C = z.Colors
for text, want in [("#4f46e5", 0x4F46E5), ("4F46E5", 0x4F46E5), ("#46e", 0x4466EE), ("fff", 0xFFFFFF)]:
    check("parses colour %r" % text, C.parse(text) == want, hex(C.parse(text)) if C.parse(text) >= 0 else -1)
for text in ["", "#12", "#12345", "#1234567", "#gg0000", "red"]:
    check("rejects colour %r" % text, C.parse(text) == C.NONE, C.parse(text))
check("colour text", C.text(0x4F46E5) == "#4F46E5" and C.text(C.NONE) == "")
lo, hi = z.Model(20.0), z.Model(70.0)
rs = z.RangeSlider(lit(z.SliderProps, min=0.0, max=100.0, step=5.0, width=z.Length.Px(300.0)), lo, hi)
v = host(rs)
b = rs.bounds()
st = v.ctx.theme.slider(z.ControlSize.Md)
def drag(x0, x1):
    y = b.y + b.h - 10
    at(v, z.EventKind.PointerMove, x0, y)
    at(v, z.EventKind.PointerDown, x0, y, button=0)
    at(v, z.EventKind.PointerMove, x1, y)
    at(v, z.EventKind.PointerUp, x1, y, button=0)
drag(rs.xOf(st, 70.0), rs.xOf(st, 90.0))
check("dragging the high thumb moves it", hi.get() == 90.0 and lo.get() == 20.0, (lo.get(), hi.get()))
drag(rs.xOf(st, 20.0), rs.xOf(st, 95.0))
check("the low thumb stops one step under the high one", lo.get() == 85.0, lo.get())
cm = z.Model(C.NONE)
cp = z.ColorPicker(lit(z.ColorProps, width=z.Length.Px(240.0)), cm)
v = host(cp)
bb = cp.bounds()
at(v, z.EventKind.PointerMove, bb.x + 60, bb.y + bb.h / 2)
at(v, z.EventKind.PointerDown, bb.x + 60, bb.y + bb.h / 2, button=0)
at(v, z.EventKind.PointerUp, bb.x + 60, bb.y + bb.h / 2, button=0)
for ch in "#4f46e5":
    v.input(ev(z.EventKind.Text, cp=ord(ch)))
for i in range(1, 5):
    v.update(3.0 + 0.016 * i)
check("typing a hex code chooses the colour", cm.get() == 0x4F46E5, cm.get())
grid = z.SwatchGrid(z.Model(C.NONE), z.Model(True))
check("the grid has fifty swatches", len(grid.colors) == 50, len(grid.colors))

print("all ok" if not fails else "FAILED: %s" % fails)
sys.exit(1 if fails else 0)
