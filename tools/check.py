#!/usr/bin/env python3
"""check.py — the checks a compiler would make first, made without one.

    python3 tools/check.py              # check src/ and examples/
    python3 tools/check.py --selftest   # plant each fault; fail if one is accepted

The Axle compiler was not on the machine this library was written on, so the dull
failures it reports first are caught here, from the text alone:

  imports     every `use crate::a::b::{X}` names a module that exists and declares X;
              every `use smalt::{X}` names a public declaration in vendor/smalt
  layers      a module imports from its own layer or below (doc/ARCHITECTURE.md)
  syntax      the whole tree parses with tools/axparse.py (the grammar of the language's documentation)
  semantics   tools/axcheck.py: names resolve, writes go to `let mut` bindings, members and
              constructors exist with the right arity, struct literals are complete, matches over an
              enum cover it, non-void functions return
  syntax      no postfix `?`; none of the reserved words the language's own
              documentation records as unusable (`free`, `of`) used as a name
  constants   a `const` / `static` initialiser is a literal (E0720)
  seam        no `extern "C"`, no `unsafe` outside the files allowed it: nothing in
              this library names an operating system or touches raw memory but smalt

It is not a type checker and says so: a wrong argument type, a missing `own`, an
ownership error all still need `axle check`.
"""
import os
import re
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import axcheck  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

# Bottom to top. A module's layer is the first path component under src/.
LAYERS = ["gfx", "text", "style", "paint", "core", "widgets", "shell"]

# Files allowed `unsafe`: none today. Raw memory is smalt's `Mem`; a hot loop that needs a typed
# pointer asks for it in smalt rather than here.
UNSAFE_OK = set()

# Methods the language and smalt's primitives provide that no `fn` in a source file declares.
BUILTIN_METHODS = {
    "min", "max", "abs", "sqrt", "sin", "cos", "pow", "round", "floorToInt", "ceilToInt",
    "truncToInt", "byteAt", "join", "await", "length", "push", "pop",
    # string, StringBuilder and the stdlib collections the library may use
    "toString", "isEmpty", "substring", "charAt", "append", "appendChar", "equals", "get", "set", "add", "size",
    "removeAt", "clear", "indexOf", "contains", "isAlive",
}

DECL = re.compile(
    r"^\s*(?:pub(?:\([a-z]+\))?\s+)?(?:extern\s+\"C\"\s+)?(?:static\s+)?"
    r"(class|struct|trait|enum|exception|fn|const)\s+(\w+)", re.M)
FN = re.compile(r"\bfn\s+(\w+)\s*\(")


def strip_comments(text):
    text = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def strip_strings(text):
    return re.sub(r'"(?:[^"\\\n]|\\.)*"', '""', text)


def code_of(path):
    return strip_strings(strip_comments(open(path, encoding="utf-8").read()))


def files_under(base):
    for dirpath, _, names in os.walk(base):
        for n in sorted(names):
            if n.endswith(".axle"):
                yield os.path.join(dirpath, n)


def matching_brace(text, i):
    depth = 0
    for j in range(i, len(text)):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                return j
    return len(text)


def members_of(text):
    """{type name: set of member names} for every class / struct / enum / trait in `text`."""
    out = {}
    for m in re.finditer(r"^\s*(?:pub(?:\([a-z]+\))?\s+)?(?:abstract\s+)?(class|struct|trait|enum)\s+(\w+)[^{;]*\{",
                         text, re.M):
        end = matching_brace(text, m.end() - 1)
        body = text[m.end():end]
        names = set(FN.findall(body))
        names |= set(re.findall(r"\bconstructor\b", body)) and {"new"} or set()
        # fields, statics and enum variants: `name :` and `Name =` / `Name,` at depth 0 of the body
        names |= set(re.findall(r"(?:^|\n)\s*(?:pub(?:\([a-z]+\))?\s+)?(?:static\s+)?(\w+)\s*:", body))
        names |= set(re.findall(r"(?:^|\n)\s*(\w+)\s*(?:=|,|\()", body))
        out.setdefault(m.group(2), set()).update(names)
    return out


class Index:
    def __init__(self, root):
        self.root = root
        self.src = os.path.join(root, "src")
        self.modules = {}      # logical module path (tuple) -> file
        self.decls = {}        # file -> {name}
        self.types = {}        # type name -> members
        self.methods = set(BUILTIN_METHODS)
        self.ctor_classes = set()   # classes that declare a constructor
        for f in files_under(self.src):
            rel = os.path.relpath(f, self.src)[:-5].split(os.sep)
            self.modules[tuple(rel)] = f
            text = code_of(f)
            self.decls[f] = {m.group(2) for m in DECL.finditer(text)}
            for cm in re.finditer(r"\bclass\s+(\w+)[^{]*\{", text):
                if re.search(r"\bconstructor\s*\(", text[cm.end():matching_brace(text, cm.end() - 1)]):
                    self.ctor_classes.add(cm.group(1))
            for k, v in members_of(text).items():
                self.types.setdefault(k, set()).update(v)
            self.methods |= set(FN.findall(text))


def smalt_index():
    root = os.path.join(ROOT, "vendor", "smalt")
    if not os.path.isdir(os.path.join(root, "src")):
        return None, None
    names = set()
    types = {}
    methods = set()
    for f in files_under(os.path.join(root, "src")):
        text = code_of(f)
        for m in re.finditer(
                r"^\s*pub(?:\([a-z]+\))?\s+(?:extern\s+\"C\"\s+)?(?:static\s+)?(class|struct|trait|enum|exception|fn|const)\s+(\w+)",
                text, re.M):
            if "(" not in text[m.start():m.end()].split("pub", 1)[1].split(m.group(1))[0]:
                names.add(m.group(2))
        for k, v in members_of(text).items():
            types.setdefault(k, set()).update(v)
        methods |= set(FN.findall(text))
    return (names, types), methods


def layer_of(parts):
    return LAYERS.index(parts[0]) if parts and parts[0] in LAYERS else None


_DEFAULT_NEEDS = {}


def default_needs(idx):
    """struct name -> (defining file, type names its field defaults mention).

    A struct literal that leaves fields out is completed with the defaults, and the compiler resolves
    those default expressions in the module that WRITES the literal, so that module must import every
    type a default names (E0017 `Justify` in flex.axle:44, reported once per use)."""
    if idx.src in _DEFAULT_NEEDS:
        return _DEFAULT_NEEDS[idx.src]
    out = {}
    for f in files_under(idx.src):
        text = code_of(f)
        for m in re.finditer(r"pub struct (\w+) \{(.*?)\n\}", text, re.S):
            names = set()
            for d in re.finditer(r":\s*[^=;]+=\s*([^;]+);", m.group(2)):
                names |= set(re.findall(r"\b([A-Z]\w*)::", d.group(1)))
                names |= set(re.findall(r"\b([A-Z]\w*)\s*\{", d.group(1)))
            if names:
                out[m.group(1)] = (f, names)
    _DEFAULT_NEEDS[idx.src] = out
    return out


def check_file(path, idx, smalt, smalt_methods, errors, rel_root):
    text = code_of(path)
    rel = os.path.relpath(path, rel_root)
    in_src = path.startswith(idx.src + os.sep)
    mod = tuple(os.path.relpath(path, idx.src)[:-5].split(os.sep)) if in_src else None

    def err(msg):
        errors.append("%s: %s" % (rel, msg))

    # --- imports -----------------------------------------------------------------
    for m in re.finditer(r"^\s*use\s+(crate|smalt|zaffre)::([\w:]+)(?:::\{([^}]*)\}|::(\w+))?;", text, re.M):
        root_name, pathstr, group, single = m.group(1), m.group(2), m.group(3), m.group(4)
        names = []
        if group:
            names = [n.strip() for n in group.split(",") if n.strip()]
        elif single:
            names = [single]
        if root_name == "zaffre":
            # `use zaffre::{A, B}` from an example: every name must be a declaration somewhere in src/
            allnames = set()
            for f in idx.decls.values():
                allnames |= f
            for n in ([pathstr] if not names else names):
                base = n.split(" as ")[0].strip()
                if base not in allnames:
                    err("`use zaffre::…` names `%s`, which the library does not declare" % base)
            continue
        if root_name == "smalt":
            if smalt is None:
                continue
            pub, _ = smalt
            for n in ([pathstr] if not names else names):
                base = n.split(" as ")[0].strip()
                if base not in pub:
                    err("`use smalt::…` names `%s`, which vendor/smalt does not declare pub" % base)
            continue
        parts = tuple(pathstr.split("::"))
        # `use crate::a::b::X;` (single) puts X in the path; the module is the longest existing prefix.
        full = parts + tuple(names[:1]) if single and False else parts
        target = None
        for cut in range(len(parts), 0, -1):
            if parts[:cut] in idx.modules:
                target = parts[:cut]
                break
        if target is None:
            # a directory: `use crate::gfx::{canvas, tint};` names modules inside it
            if any(k[:len(parts)] == parts for k in idx.modules):
                for n in names:
                    base = n.split(" as ")[0].strip()
                    if parts + (base,) not in idx.modules:
                        err("`%s` is not a module under crate::%s" % (base, pathstr))
                continue
            err("`use crate::%s` names no module" % pathstr)
            continue
        f = idx.modules[target]
        wanted = names if names else ([parts[-1]] if len(parts) > len(target) else [])
        for n in wanted:
            base = n.split(" as ")[0].strip()
            if base not in idx.decls[f]:
                err("`%s` is not declared in crate::%s" % (base, "::".join(target)))
        if mod is not None:
            a, b = layer_of(mod), layer_of(target)
            if a is not None and b is not None and b > a:
                err("layer violation: %s (%s) imports %s (%s)" % ("::".join(mod), LAYERS[a], "::".join(target), LAYERS[b]))

    # --- defaults ----------------------------------------------------------------
    imported = set()
    # Inside the library the defaults resolve where the struct is declared; a program using the
    # library as a dependency resolves them in its own module, so only examples/ is held to this.
    for m in re.finditer(r"^\s*use\s+[^;]*;", text, re.M | re.S) if not in_src else []:
        for w in re.findall(r"\b(\w+)\b(?:\s+as\s+(\w+))?", m.group(0)):
            imported.add(w[0])
            if w[1]:
                imported.add(w[1])
    for sname, (sfile, names) in (default_needs(idx).items() if not in_src else []):
        if os.path.abspath(sfile) == os.path.abspath(path):
            continue
        for m in re.finditer(r"\b%s\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}" % sname, text):
            if ".." in m.group(1):
                continue
            for n in sorted(names):
                if n not in imported:
                    err("`%s { … }` leaves fields to their defaults, which name `%s`: import it here" % (sname, n))
            break

    # --- syntax ------------------------------------------------------------------
    keywords = ("own", "mut", "let", "fn", "pub", "class", "struct", "enum", "trait", "static", "const", "match",
                "if", "else", "for", "while", "return", "new", "shared", "self", "super", "as", "use", "try",
                "catch", "throw", "break", "continue", "impl", "type", "dyn", "when", "readonly", "constructor", "drop",
                "do", "finally", "exception", "defer", "spawn", "await", "async", "synchronized", "extern",
                "unsafe", "is", "null", "true", "false", "of", "from")
    for kw in keywords:
        for m in re.finditer(r"\blet\s+(?:mut\s+)?%s\b(?!\s*\()|[(,]\s*%s\s*:\s*[A-Za-z(\[]|\b%s\s*(?:=(?!=)|\.(?=\w))" % (kw, kw, kw), text):
            if kw in ("self", "super") and "let" not in m.group(0):
                continue
            if kw == "mut" and re.match(r"\s*let\s+mut\b", m.group(0)):
                continue
            line = text.count("\n", 0, m.start()) + 1
            err("line %d: `%s` is a keyword and cannot name a variable or a parameter" % (line, kw))
    # an element of an array bound with a plain `let` cannot be assigned (E0004)
    for m in re.finditer(r"\blet\s+(?!mut\b)(\w+)\s*(?::[^=;]+)?=(?!=)", text):
        name = m.group(1)
        if re.search(r"(?<![.\w])%s\s*\[[^\]]*\]\s*=(?!=)" % re.escape(name), text):
            line = text.count("\n", 0, m.start()) + 1
            err("line %d: `%s` holds an array that is written to: declare it `let mut`" % (line, name))
    # a lambda inside a lambda (E0700): find each lambda's body and look for another lambda arrow in it
    arrow = re.compile(r"\(\s*(?:\w+\s*:\s*[\w<>\[\]]+(?:\s*,\s*\w+\s*:\s*[\w<>\[\]]+)*)?\s*\)\s*=>")
    for m in arrow.finditer(text):
        depth = 0
        i = m.end()
        while i < len(text):
            c = text[i]
            if c in "([{":
                depth += 1
            elif c in ")]}":
                if depth == 0:
                    break
                depth -= 1
            elif c in ",;" and depth == 0:
                break
            i += 1
        if arrow.search(text[m.end():i]):
            line = text.count("\n", 0, m.start()) + 1
            err("line %d: a lambda nested in a lambda is not supported (E0700): pass what it needs to a function" % line)
    # a derived constructor must reach its base's constructor with super(...): the base's fields start zeroed
    for m in re.finditer(r"\bclass\s+(\w+)\s*:\s*([\w\s,]+?)\s*\{", text):
        bases = [b.strip() for b in m.group(2).split(",")]
        end = matching_brace(text, m.end() - 1)
        body = text[m.end():end]
        for b in bases:
            if b in idx.ctor_classes:
                for c in re.finditer(r"\bconstructor\s*\([^)]*\)\s*\{(?!\s*super\s*\()", body):
                    line = text.count("\n", 0, m.end() + c.start()) + 1
                    err("line %d: a constructor of `%s` must begin with super(…) — its base `%s` has a constructor that sets the inherited fields" % (line, m.group(1), b))
    # a value given to an `own` parameter and moved into a field cannot be read afterwards (E0501)
    for fm in re.finditer(r"\b(?:fn|constructor)\s*(?:\w+)?\s*\(([^)]*)\)[^{;]*\{", text):
        owns = re.findall(r"\bown\s+(\w+)\s*:", fm.group(1))
        if not owns:
            continue
        end = matching_brace(text, fm.end() - 1)
        body = text[fm.end():end]
        for name in owns:
            mv = re.search(r"self\.\w+\s*=\s*%s\s*;" % re.escape(name), body)
            if mv and re.search(r"(?<![.\w])%s\b" % re.escape(name), body[mv.end():]):
                line = text.count("\n", 0, fm.end() + mv.end()) + 1
                err("line %d: `%s` was moved into a field; read it through the field afterwards (E0501)" % (line, name))
    for m in re.finditer(r"\bfn\s+(i8|i16|i32|i64|u8|u16|u32|u64|f32|f64|bool|char|string|void)\s*\(", text):
        err("`fn %s` — a primitive type's name cannot name a method" % m.group(1))
    for i, line in enumerate(text.split("\n"), 1):
        if re.search(r"\)\s*\?\s*(;|\.|\)|,)", line):
            err("line %d: a postfix `?` — the compiler refuses it" % i)
        if re.search(r"\b(?:let(?:\s+mut)?|fn)\s+(free|of|from)\b", line) or re.search(r"\b(free|of|from)\s*:\s*[A-Za-z]", line):
            err("line %d: `free` / `of` / `from` are reserved" % i)
    for m in re.finditer(r"^\s*(?:pub(?:\([a-z]+\))?\s+)?(?:static\s+)?const\s+\w+\s*:\s*[\w<>\[\]]+\s*=\s*([^;]+);", text, re.M):
        if not re.fullmatch(r"\s*-?\s*(0x[0-9A-Fa-f_]+|\d[\d_]*(\.\d+)?|true|false|\"[^\"]*\")\s*", m.group(1)):
            err("constant initialiser `%s` is not a literal (E0720)" % m.group(1).strip())
    for m in re.finditer(r"^\s*(?:pub(?:\([a-z]+\))?\s+)?static\s+(?!fn)\w+\s*:\s*[\w<>\[\]]+\s*=\s*([^;]+);", text, re.M):
        if not re.fullmatch(r"\s*-?\s*(0x[0-9A-Fa-f_]+|\d[\d_]*(\.\d+)?|true|false|\"[^\"]*\")\s*", m.group(1)):
            err("static initialiser `%s` is not a literal (E0720)" % m.group(1).strip())

    # --- seam --------------------------------------------------------------------
    if re.search(r'extern\s+"C"', strip_comments(open(path, encoding="utf-8").read())):
        err('`extern "C"` — nothing in this library names an operating system')
    if "unsafe" in text and rel.replace(os.sep, "/") not in UNSAFE_OK:
        err("`unsafe` outside the files allowed it")


def duplicate_names(idx):
    """Two top-level declarations, public or not, with one name collide in the package (E0003: `Column` the layout and the
    table's; `doNothing` in two modules)."""
    seen = {}
    out = []
    for f in files_under(idx.src):
        mod = os.path.relpath(f, idx.src)[:-5]
        for m in re.finditer(r"^(?:pub(?:\([a-z]+\))?\s+)?(?:class|struct|enum|trait|fn|const)\s+(\w+)", code_of(f), re.M):
            name = m.group(1)
            if name in seen and seen[name] != mod:
                out.append("`%s` is declared in both %s and %s" % (name, seen[name], mod))
            seen.setdefault(name, mod)
    return out


def run(root):
    global ROOT
    idx = Index(root)
    smalt, smalt_methods = smalt_index()
    errors = duplicate_names(idx)
    for base in ("src", "examples"):
        d = os.path.join(root, base)
        if os.path.isdir(d):
            for f in files_under(d):
                check_file(f, idx, smalt, smalt_methods, errors, root)
    smalt_src = os.path.join(root, "vendor", "smalt", "src")
    errors += axcheck.check_tree(root, smalt_src if os.path.isdir(smalt_src) else None)
    return errors


def selftest():
    faults = [
        ("a bad import", "use crate::gfx::nothing::{X};\n"),
        ("a name not declared", "use crate::gfx::tint::{Nonesuch};\n"),
        ("a layer violation", "use crate::ui::ui::{Ui};\n"),
        ("a postfix ?", "fn f() : void { let x = g()?; }\n"),
        ("a reassigned let", "fn f() : void { let x : i32 = 1; x = 2; }\n"),
        ("an if-then", "fn f() : void { let x : i32 = if (true) then 1 else 2; }\n"),
        ("an undefined name", "fn f() : i32 { return nothingByThisName; }\n"),
        ("a missing return", "fn f() : i32 { let x : i32 = 1; }\n"),
        ("an incomplete struct literal", "fn f() : void { let r : RRect = RRect { x: 1.0 }; }\n"),
        ("a reserved name", "fn f() : void { let free = 1; }\n"),
        ("a method named after a type", "class A { fn u16(self) : i32 { return 1; } }\n"),
        ("a non-literal const", "const A : i32 = B + 1;\n"),
        ("extern C", 'extern "C" from "c" { fn puts(s : ptr) : i32; }\n'),
        ("an unknown member", "fn f() : void { Tint::nonesuch(1); }\n"),
        ("a keyword as a name", "fn f() : void { let mut own : i32 = 1; own = 2; }\n"),
        ("an array written through let", "fn f() : void { let v : f64[] = malloc<f64>(3 as i64); v[0] = 1.0; }\n"),
        ("a duplicate private function", "fn doNothing() : void { }\nfn doNothing() : void { }\n"),
        ("a wrong arity", "fn f() : void { let t : Tint = Tint::hex(1, 2); }\n"),
    ]
    bad = 0
    for name, body in faults:
        scratch = tempfile.mkdtemp()
        try:
            shutil.copytree(os.path.join(ROOT, "src"), os.path.join(scratch, "src"))
            os.makedirs(os.path.join(scratch, "vendor"), exist_ok=True)
            vend = os.path.join(ROOT, "vendor", "smalt")
            if os.path.isdir(vend):
                os.symlink(vend, os.path.join(scratch, "vendor", "smalt"))
            with open(os.path.join(scratch, "src", "gfx", "planted.axle"), "w") as fh:
                fh.write("use crate::gfx::tint::Tint;\nuse crate::gfx::shapes::RRect;\n" + body)
            if not run(scratch):
                sys.stderr.write("selftest: %s was accepted\n" % name)
                bad += 1
        finally:
            shutil.rmtree(scratch, ignore_errors=True)
    # the untouched tree must pass
    errs = run(ROOT)
    if errs:
        sys.stderr.write("selftest: the untouched tree fails:\n  " + "\n  ".join(errs[:10]) + "\n")
        bad += 1
    if bad == 0:
        print("selftest: all %d planted faults rejected" % len(faults))
    return bad


def main():
    if "--selftest" in sys.argv:
        sys.exit(1 if selftest() else 0)
    root = ROOT
    if "--root" in sys.argv:
        # Calibration: run the same checks over another tree (vendor/smalt compiles, so what is
        # reported there that is not about its OS imports or `unsafe` is a false positive here).
        root = os.path.abspath(sys.argv[sys.argv.index("--root") + 1])
    errors = run(root)
    for e in errors:
        sys.stderr.write(e + "\n")
    if errors:
        sys.stderr.write("check: %d problem(s)\n" % len(errors))
        sys.exit(1)
    print("check: ok")


if __name__ == "__main__":
    main()
