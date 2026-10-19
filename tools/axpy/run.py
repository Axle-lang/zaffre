"""run.py — translate zaffre's sources to Python and load them as one module.

    python3 tools/axpy/run.py --dump out.py     write the translation
    from axpy.run import load; z = load()       the module, for the tests
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)

from axparse import parse  # noqa: E402
from axpy.emit import Emitter  # noqa: E402


def sources(extra=()):
    out = []
    for base in [os.path.join(ROOT, "src")] + list(extra):
        for dp, _, names in os.walk(base):
            for n in sorted(names):
                if n.endswith(".axle") and n != "lib.axle" and "/shell/" not in dp + "/":
                    out.append(os.path.join(dp, n))
    return sorted(out)


def translate(extra=()):
    em = Emitter()
    for p in sources(extra):
        em.add_file(parse(open(p, encoding="utf-8").read()))
    return em.emit()


def load(extra=()):
    import types
    src = translate(extra)
    mod = types.ModuleType("zaffre")
    exec(compile(src, "<zaffre>", "exec"), mod.__dict__)
    return mod


if __name__ == "__main__":
    src = translate(sys.argv[3:] if False else ())
    if len(sys.argv) > 2 and sys.argv[1] == "--dump":
        open(sys.argv[2], "w").write(src)
    else:
        load()
        print("loaded")
