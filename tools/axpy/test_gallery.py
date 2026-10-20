"""Drive every page of the gallery as a user would: move the pointer over it, press everywhere, type,
and press Escape — and fail on any exception, a hover that never reaches a widget, or a page that
asks for no hand cursor anywhere."""
import os, sys, traceback
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from axpy.run import load, ROOT
from axpy import rt
from axpy.rt import _rt_lit

z = load([os.path.join(ROOT, "examples", "gallery", "src")])
fails = []


def ev(kind, x=0.0, y=0.0, **kw):
    return _rt_lit(z.UiEvent, None, kind=kind, x=x, y=y, **kw)


names = ["", "overview", "buttons", "forms", "feedback", "navigation", "data", "layout", "overlays"]
clock = [0.0]


def tick(view, n=3):
    for _ in range(n):
        clock[0] += 0.016
        view.update(clock[0])


for page in range(1, 9):
    view = z.buildOn(page)
    view.resize(1360.0, 900.0)
    tick(view, 5)
    view.layout()
    hands = 0
    try:
        for y in range(10, 900, 36):
            for x in range(10, 1360, 48):
                view.input(ev(z.EventKind.PointerMove, float(x), float(y)))
                if view.cursor() != z.Cursor.Arrow:
                    hands += 1
        for y in range(10, 900, 70):
            for x in range(10, 1360, 90):
                view.input(ev(z.EventKind.PointerMove, float(x), float(y)))
                view.input(ev(z.EventKind.PointerDown, float(x), float(y), button=0))
                view.input(ev(z.EventKind.PointerUp, float(x), float(y), button=0))
                tick(view, 2)
                view.layout()
                # whatever opened (dialog, menu, sheet, palette): type a little, then close it
                view.input(ev(z.EventKind.Text, cp=ord("a")))
                view.input(ev(z.EventKind.KeyDown, key=z.Key.Escape))
                tick(view, 20)
        sfc = rt.Surface(1360, 900)
        view.render(sfc.frame())
        print("ok   page %-10s %d hover points asked for a cursor" % (names[page], hands))
        if hands == 0:
            fails.append(page)
    except Exception:
        traceback.print_exc()
        print("FAIL page", names[page])
        fails.append(page)

print("FAIL %d" % len(fails) if fails else "all ok")
sys.exit(1 if fails else 0)
