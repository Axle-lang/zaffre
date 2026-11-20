"""The weather app's own widgets, driven by events: pick an hour on the chart, a row of the table, a day of the week."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from axpy.run import load, ROOT
from axpy import rt
from axpy.rt import _rt_lit

z = load([os.path.join(ROOT, "examples", "weather", "src")])
fails = []


def check(name, cond, extra=""):
    print(("ok   " if cond else "FAIL ") + name + (" " + str(extra) if extra and not cond else ""))
    if not cond:
        fails.append(name)


def ev(kind, x=0.0, y=0.0, **kw):
    return _rt_lit(z.UiEvent, None, kind=kind, x=x, y=y, **kw)


clock = [0.0]


def settle(v, n=30):
    for _ in range(n):
        clock[0] += 0.016
        v.update(clock[0])


# the forecast itself
atlas = z.Atlas()
for p in range(atlas.count):
    for d in range(7):
        day = atlas.day(p, d)
        hrs = [atlas.hour(p, d, h) for h in range(24)]
        check("%s day %d: hi/lo are the hours' extremes" % (atlas.nameOf(p), d), abs(day.hi - max(h.temp for h in hrs)) < 1e-9 and abs(day.lo - min(h.temp for h in hrs)) < 1e-9)
        for h in hrs:
            assert 0 <= h.humidity <= 100 and 0 <= h.chance <= 100 and h.precip >= 0 and h.wind >= 0 and h.gust >= h.wind and 0 <= h.windDir < 360 and 0 <= h.cloud <= 100, (p, d)
            assert h.uv >= 0 and (not h.night or h.uv == 0), (p, d)
check("every hour of every place is in range", True)
check("the same place gives the same week", z.Atlas().hour(1, 3, 5).temp == atlas.hour(1, 3, 5).temp)
skies = {atlas.hour(p, d, h).sky.name for p in range(6) for d in range(7) for h in range(24)}
check("the model produces a variety of skies", len(skies) >= 5, skies)
check("compass names", z.compass(0.0) == "N" and z.compass(90.0) == "E" and z.compass(225.0) == "SW" and z.compass(359.0) == "N")
check("beaufort", z.beaufort(0.0) == 0 and z.beaufort(20.0) == 4 and z.beaufort(200.0) == 12)
check("fahrenheit", abs(z.temperature(100.0, True) - 212.0) < 1e-9)
check("clock", z.clock(6.7) == "06:42" and z.hourLabel(7) == "07:00")

# the widgets
place, day, hour, metric, units = (z.Model(0), z.Model(0), z.Model(14), z.Model(0), z.Model(0))
wx = z.Weather(place, day, hour, metric, units)
chart, rows, week = z.HourChart(wx), z.HourRows(wx), z.WeekList(wx)
page = z.Column(_rt_lit(z.FlexProps, None, gap=10.0, padding=z.Insets.all(10.0), width=z.Length.Px(500.0), align=z.Align.Stretch), [chart, z.Scroll(_rt_lit(z.ScrollProps, None, height=z.Length.Px(200.0), width=z.Length.Fill), rows), week])
v = z.View(z.Theme.dark(), z.Fonts(), page)
v.resize(520.0, 800.0); settle(v); v.layout()


def press(w, fx, fy):
    b = w.bounds(); x, y = b.x + b.w * fx, b.y + b.h * fy
    v.input(ev(z.EventKind.PointerMove, x, y)); v.input(ev(z.EventKind.PointerDown, x, y)); v.input(ev(z.EventKind.PointerUp, x, y))


b = chart.bounds()
pl = chart.plot()
press(chart, (pl.x + pl.w * (5.5 / 24) - b.x) / b.w, 0.5)
check("a click on the chart picks that hour", hour.get() == 5, hour.get())
v.input(ev(z.EventKind.PointerDown, pl.x + pl.w * 0.2, pl.y + 20)); v.input(ev(z.EventKind.PointerMove, pl.x + pl.w * 0.95, pl.y + 20))
check("dragging scrubs through the hours", hour.get() == 22, hour.get())
v.input(ev(z.EventKind.PointerUp, pl.x + pl.w * 0.95, pl.y + 20))
v.input(ev(z.EventKind.PointerMove, pl.x + pl.w * 0.5, pl.y + 20))
check("hovering shows an hour without picking it", chart.hot == 12 and hour.get() == 22, (chart.hot, hour.get()))

press(rows, 0.5, 3.5 / 24)
check("a click on a row of the table picks that hour", hour.get() == 3, hour.get())
press(week, 0.5, 3.5 / 7)
check("a click on a day of the week picks that day", day.get() == 3, day.get())
check("the table follows the day", wx.hourOf(3).windDir == atlas.hour(0, 3, 3).windDir)
place.set(2)
check("the place changes the whole forecast", wx.current().temp == atlas.hour(2, 3, 3).temp)
for m in range(4):
    metric.set(m); chart.load()
    check("metric %d: the axis covers the data" % m, chart.lo <= min(min(chart.vals), min(chart.vals2)) and chart.hi >= max(max(chart.vals), max(chart.vals2)), (chart.lo, chart.hi))
units.set(1); metric.set(0); chart.load()
check("imperial changes the curve's units", chart.vals[0] == z.temperature(wx.hourOf(0).temp, True))
for dark in (True, False):
    for m in range(4):
        metric.set(m)
        v.darkMode().set(dark); settle(v, 3)
        v.render(rt.Surface(520, 800).frame())
print("FAIL %d" % len(fails) if fails else "all ok")
sys.exit(1 if fails else 0)
