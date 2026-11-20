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



lit = lambda S, **kw: _rt_lit(S, None, **kw)


def host(widget, w=600.0, h=500.0):
    v = z.View(z.Theme.dark(), z.Fonts(), z.Column(lit(z.FlexProps, padding=z.Insets.all(10.0), width=z.Length.Px(w - 20)), [widget]))
    v.resize(w, h)
    settle(v)
    v.layout()
    return v


# --- Textarea -------------------------------------------------------------------------------
tm = z.Model("one\ntwo")
ta = z.Textarea(lit(z.TextareaProps, rows=3, width=z.Length.Px(300.0)), tm)
tv = host(ta)
click(tv, ta)
key(tv, z.Key.End, mods=2)          # Ctrl+End: the end of the text
typed(tv, "!")
check("a text area takes typed text", tm.get() == "one\ntwo!", repr(tm.get()))
key(tv, z.Key.Enter)
typed(tv, "x")
check("Enter starts a new line", tm.get() == "one\ntwo!\nx", repr(tm.get()))
key(tv, z.Key.Up)
typed(tv, "-")
check("Up moves to the line above, keeping the column", tm.get() == "one\nt-wo!\nx", repr(tm.get()))
key(tv, z.Key.Home, mods=2)
typed(tv, ">")
check("Ctrl+Home goes to the start", tm.get().startswith(">one"), repr(tm.get()))

# --- Accordion ------------------------------------------------------------------------------
om = z.Model(0)
acc = z.Accordion(["A", "B", "C"], om, [z.Label("a"), z.Label("b"), z.Label("c")])
av = host(acc)
b = acc.bounds()
click(av, acc, dx=40.0, dy=20.0)
settle(av, 30)
check("clicking a title opens its section", om.get() == 1, om.get())
av.layout()
click(av, acc, dx=40.0, dy=acc.tops[1] + 20.0)
settle(av, 30)
check("opening a second section closes the first (single)", om.get() == 2, om.get())

# --- Pagination -----------------------------------------------------------------------------
pm = z.Model(0)
pg = z.Pagination(lit(z.PaginationProps, pages=10), pm)
pv = host(pg)
bb = pg.bounds()
click(pv, pg, dx=bb.w - 18.0)          # the "next" arrow
check("the next arrow goes to the next page", pm.get() == 1, pm.get())
key(pv, z.Key.Right)
check("Right moves a page when focused", pm.get() == 2, pm.get())

# --- Table sorting and picking --------------------------------------------------------------
cols = [lit(z.TableColumn, title="Name", width=z.Length.Fill, sortable=True), lit(z.TableColumn, title="N", sortable=True)]
cells = [z.Label("b"), z.Label("2"), z.Label("a"), z.Label("1"), z.Label("c"), z.Label("3")]
pick = z.Model(-1)
tb = z.Table(lit(z.TableProps), cols, cells, pick)
tb.setKeys([2.0, 2.0, 1.0, 1.0, 3.0, 3.0])
tvw = host(tb, 400.0, 300.0)
click(tvw, tb, dx=20.0, dy=20.0)       # the header of the first column
check("a sortable header orders the rows", [tb.order[i] for i in range(3)] == [1, 0, 2], [tb.order[i] for i in range(3)])
click(tvw, tb, dx=20.0, dy=20.0)
check("a second click reverses the order", [tb.order[i] for i in range(3)] == [2, 0, 1], [tb.order[i] for i in range(3)])
tvw.layout()
click(tvw, tb, dx=20.0, dy=tb.rowTop[0] + 10.0)
check("clicking a row picks its data index", pick.get() == tb.order[0], pick.get())

# --- Stepper, quantity, toggle group, rating ------------------------------------------------
sm = z.Model(2)
st = z.Stepper(["a", "b", "c", "d"], sm)
sv = host(st, 480.0, 120.0)
click(sv, st, dx=st.bounds().w * 0.125)   # the first stage, which is done
check("clicking a done stage goes back to it", sm.get() == 0, sm.get())
qm = z.Model(3)
qt = z.QuantityInput(lit(z.QuantityProps, min=0, max=4), qm)
qv = host(qt)
click(qv, qt, dx=qt.bounds().w - 10.0)
click(qv, qt, dx=qt.bounds().w - 10.0)
check("plus adds one, up to the maximum", qm.get() == 4, qm.get())
click(qv, qt, dx=10.0)
check("minus takes one away", qm.get() == 3, qm.get())
gm = z.Model(0)
tg = z.ToggleGroup(["a", "b", "c"], gm)
gv = host(tg)
click(gv, tg, dx=tg.right[1] - 5.0)
click(gv, tg, dx=tg.right[2] - 5.0)
check("toggle buttons add to the set", gm.get() == 6, gm.get())
click(gv, tg, dx=tg.right[1] - 5.0)
check("pressing one that is on turns it off", gm.get() == 4, gm.get())
rm = z.Model(0)
rt_ = z.Rating(lit(z.RatingProps), rm)
rv = host(rt_)
click(rv, rt_, dx=3 * 28.0 + 5.0)
check("clicking a star gives that score", rm.get() == 4, rm.get())
click(rv, rt_, dx=3 * 28.0 + 5.0)
check("clicking the same star takes the score back", rm.get() == 0, rm.get())

# --- Sidebar --------------------------------------------------------------------------------
items = [lit(z.SidebarItem, label="Group", heading=True), lit(z.SidebarItem, label="One"), lit(z.SidebarItem, label="Two")]
nm = z.Model(1)
sb = z.Sidebar(lit(z.SidebarProps, title="App"), items, nm)
sbv = z.View(z.Theme.dark(), z.Fonts(), sb)
sbv.resize(400.0, 400.0); settle(sbv); sbv.layout()
click(sbv, sb, dx=50.0, dy=sb.tops[2] + 10.0)
check("clicking an item chooses it", nm.get() == 2, nm.get())
click(sbv, sb, dx=50.0, dy=sb.tops[0] + 10.0)
check("a heading cannot be chosen", nm.get() == 2, nm.get())

# --- Tag, banner ----------------------------------------------------------------------------
closed = [0]
tag = z.Tag(lit(z.TagProps, text="x", removable=True), lambda: closed.__setitem__(0, 1))
tgv = host(tag)
click(tgv, tag, dx=tag.bounds().w - 8.0)
check("a tag's cross runs its handler", closed[0] == 1)
ban = z.Banner(lit(z.BannerProps, dismissible=True), "hello")
bv = host(ban, 600.0, 200.0)
click(bv, ban, dx=ban.bounds().w - 20.0)
check("a banner's cross dismisses it", ban.gone)

# --- Dropdown menu --------------------------------------------------------------------------
picked = []
entries = [lit(z.MenuEntry, label="Edit"), lit(z.MenuEntry, separator=True), lit(z.MenuEntry, label="Delete", danger=True)]
mb = z.MenuButton(lit(z.ButtonProps, label="Actions"), entries, lambda i: picked.append(i))
mv = host(mb, 600.0, 400.0)
click(mv, mb)
settle(mv, 5); mv.layout(); settle(mv, 30)
menus = [o for o in mv.overlays[:mv.used] if isinstance(o, z.ActionMenu) and not o.done()]
check("a menu button opens its menu", len(menus) == 1)
m = menus[0]
mv.layout()
x = m.sheet.x + 40.0
y = m.sheet.y + m.tops[2] + 12.0
mv.input(ev(z.EventKind.PointerMove, x, y)); mv.input(ev(z.EventKind.PointerDown, x, y, button=0)); mv.input(ev(z.EventKind.PointerUp, x, y, button=0))
settle(mv, 40)
check("choosing an entry tells the handler its index", picked == [2], picked)
check("and closes the menu", m.done())

# --- Sheet ----------------------------------------------------------------------------------
notes = z.Notifier()
page = z.Notifications(notes, z.Label("page"))
shv = z.View(z.Theme.dark(), z.Fonts(), page)
shv.resize(600.0, 400.0); settle(shv); shv.layout()
notes.openSheet(lit(z.SheetProps, title="Edit", side=z.SheetSide.Right), lambda: z.Label("content"))
settle(shv, 5); shv.layout(); settle(shv, 30)
sheets = [o for o in shv.overlays[:shv.used] if isinstance(o, z.Sheet) and not o.done()]
check("a request opens a sheet", len(sheets) == 1)
key(shv, z.Key.Escape); settle(shv, 60)
check("Escape closes the sheet", sheets[0].done())

# --- Form field -----------------------------------------------------------------------------
ff = z.FormField(lit(z.FieldLabel, label="Name"), z.TextField(lit(z.FieldProps), z.Model("")))
check("a field has no error at first", not ff.hasError())
ff.setError("Required")
check("setError shows an error", ff.hasError())

# --- Command palette ------------------------------------------------------------------------
ran = []
cmds = [lit(z.MenuEntry, label="Open file"), lit(z.MenuEntry, label="Save all"), lit(z.MenuEntry, label="Close window")]
notes.openCommands(cmds, lambda i: ran.append(i))
settle(shv, 5); shv.layout(); settle(shv, 20); shv.layout()
pals = [o for o in shv.overlays[:shv.used] if isinstance(o, z.CommandPalette) and not o.done()]
check("a request opens a command palette", len(pals) == 1)
check("it lists every command at first", pals[0].shownCount == 3, pals[0].shownCount)
typed(shv, "SAVE")
shv.layout()
check("typing filters, ignoring case", pals[0].shownCount == 1 and pals[0].shown[0] == 1, (pals[0].shownCount, pals[0].shown[0]))
key(shv, z.Key.Enter); settle(shv, 40)
check("Enter runs the highlighted command with its original index", ran == [1], ran)

print("FAIL %d" % len(fails) if fails else "all ok")
sys.exit(1 if fails else 0)
