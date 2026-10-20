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

print("all ok" if not fails else "FAILED: %s" % fails)
sys.exit(1 if fails else 0)
