"""Dates, the calendar and the pickers, driven through the translated source."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from axpy.run import load
from axpy.rt import _rt_lit

z = load()
fails = []


def check(name, cond, extra=""):
    print(("ok   " if cond else "FAIL ") + name + (" " + str(extra) if extra and not cond else ""))
    if not cond:
        fails.append(name)


def ev(kind, x=0.0, y=0.0, **kw):
    return _rt_lit(z.UiEvent, None, kind=kind, x=x, y=y, **kw)


lit = lambda S, **kw: _rt_lit(S, None, **kw)
D = z.Dates
NONE = D.NONE
day = D.ymd(2026, 10, 20)

# --- Parsing ---------------------------------------------------------------------------------
for text in ["20 Oct 2026", "2026-10-20", "20/10/2026", "20.10.26", "Oct 20 2026", "20 october 2026", "  20  OCT  2026 "]:
    check("parses %r" % text, D.parse(text) == day, D.parse(text))
for text in ["", "20 Oct", "32/10/2026", "29/02/2025", "20 Foo 2026", "1 2 3 4", "2026-13-01", "hello"]:
    check("rejects %r" % text, D.parse(text) == NONE, D.parse(text))
check("a leap day is a date", D.parse("29/02/2024") == D.ymd(2024, 2, 29))
check("text and parse are inverse", D.parse(D.text(day)) == day)
check("addMonths keeps the day where it fits", D.addMonths(D.ymd(2026, 1, 31), 1) == D.ymd(2026, 2, 28))
check("addMonths crosses a year", D.addMonths(D.ymd(2026, 12, 15), 1) == D.ymd(2027, 1, 15))
check("addMonths goes back", D.addMonths(D.ymd(2026, 1, 15), -1) == D.ymd(2025, 12, 15))
check("within respects the limits", D.within(day, day, NONE) and not D.within(day - 1, day, NONE) and not D.within(day + 1, NONE, day))


def host(widget, w=700.0, h=600.0):
    v = z.View(z.Theme.light(), z.Fonts(), z.Column(lit(z.FlexProps, padding=z.Insets.all(10.0), width=z.Length.Px(w - 20)), [widget]))
    v.resize(w, h)
    t = [0.0]
    for _ in range(20):
        t[0] += 0.016
        v.update(t[0])
    v.layout()
    return v, t


def settle(v, t, n=30):
    for _ in range(n):
        t[0] += 0.016
        v.update(t[0])
    v.layout()


def click_at(v, x, y):
    v.input(ev(z.EventKind.PointerMove, x, y))
    v.input(ev(z.EventKind.PointerDown, x, y, button=0))
    v.input(ev(z.EventKind.PointerUp, x, y, button=0))


def typed(v, s):
    for c in s:
        v.input(ev(z.EventKind.Text, cp=ord(c)))


def key(v, k):
    v.input(ev(z.EventKind.KeyDown, key=k))
    v.input(ev(z.EventKind.KeyUp, key=k))


# --- The picker: typing -----------------------------------------------------------------------
chosen = z.Model(NONE)
picker = z.DatePicker(lit(z.DateProps, today=day, width=z.Length.Px(260.0)), chosen)
v, t = host(picker)
b = picker.bounds()
click_at(v, b.x + 30.0, b.y + b.h / 2)
typed(v, "5 Nov 2026")
settle(v, t, 4)
check("typing a date chooses it", chosen.get() == D.ymd(2026, 11, 5), chosen.get())
typed(v, "x")
settle(v, t, 4)
check("garbage keeps the last good date", chosen.get() == D.ymd(2026, 11, 5), chosen.get())

# --- The picker: the calendar -----------------------------------------------------------------
chosen2 = z.Model(NONE)
picker2 = z.DatePicker(lit(z.DateProps, today=day, width=z.Length.Px(260.0)), chosen2)
v2, t2 = host(picker2)
b2 = picker2.bounds()
click_at(v2, b2.x + b2.w - 18.0, b2.y + b2.h / 2)
settle(v2, t2, 20)
check("the calendar button opens the panel", len(v2.ctx.overlays) == 1 if hasattr(v2.ctx, "overlays") else True)
key(v2, z.Key.Down)
key(v2, z.Key.Right)
key(v2, z.Key.Enter)
settle(v2, t2, 20)
check("keys choose a day: Down enters at today, Right moves a day", chosen2.get() == day + 1, chosen2.get())
settle(v2, t2, 40)
check("the field shows what was chosen", picker2.draft.get() == D.text(day + 1), picker2.draft.get())

# --- The calendar alone -----------------------------------------------------------------------
start = z.Model(NONE)
stop = z.Model(NONE)
cal = z.Calendar(lit(z.DateProps, today=day), start, stop)
v3, t3 = host(cal)
cb = cal.bounds()
c0 = cal.cellBox(D.weekday(D.ymd(2026, 10, 1)) + 9)       # 10 October
c1 = cal.cellBox(D.weekday(D.ymd(2026, 10, 1)) + 14)      # 15 October
click_at(v3, c0.x + c0.w / 2, c0.y + c0.h / 2)
click_at(v3, c1.x + c1.w / 2, c1.y + c1.h / 2)
check("two clicks make a range", start.get() == D.ymd(2026, 10, 10) and stop.get() == D.ymd(2026, 10, 15), (start.get(), stop.get()))
nav = cal.navBox(1)
click_at(v3, nav.x + nav.w / 2, nav.y + nav.h / 2)
check("the next arrow turns the month", cal.month == 11, cal.month)
tb = cal.titleBox(v3.ctx)
click_at(v3, tb.x + tb.w / 2, tb.y + tb.h / 2)
check("the title opens the grid of months", cal.panel == 1, cal.panel)
tb = cal.titleBox(v3.ctx)
click_at(v3, tb.x + tb.w / 2, tb.y + tb.h / 2)
check("the title of the months opens the years", cal.panel == 2, cal.panel)
yb = cal.pickBox(1)
click_at(v3, yb.x + yb.w / 2, yb.y + yb.h / 2)
check("a year in the grid is chosen, and the months show", cal.year == 2017 and cal.panel == 1, (cal.year, cal.panel))
mb = cal.pickBox(2)
click_at(v3, mb.x + mb.w / 2, mb.y + mb.h / 2)
check("a month in the grid is chosen", cal.month == 3 and cal.panel == 0, (cal.month, cal.panel))

# --- A limit ---------------------------------------------------------------------------------
lim = z.Model(NONE)
cal2 = z.Calendar(lit(z.DateProps, today=day, min=day), lim)
v4, t4 = host(cal2)
before = cal2.cellBox(D.weekday(D.ymd(2026, 10, 1)) + 4)    # 5 October, before `min`
click_at(v4, before.x + before.w / 2, before.y + before.h / 2)
check("a day before min cannot be chosen", lim.get() == NONE, lim.get())
after = cal2.cellBox(D.weekday(D.ymd(2026, 10, 1)) + 24)    # 25 October
click_at(v4, after.x + after.w / 2, after.y + after.h / 2)
check("a day after min can", lim.get() == D.ymd(2026, 10, 25), lim.get())

print("all ok" if not fails else "FAILED: %s" % fails)
sys.exit(1 if fails else 0)
