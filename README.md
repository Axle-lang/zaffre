<div align="center">

# 🔷 Zaffre

### A native UI library for Axle — soft, typographic, themeable, and nothing but [smalt](https://github.com/Axle-lang/smalt)

<img src="doc/img/weather-dark.png" width="49%"> <img src="doc/img/weather-light.png" width="49%">

*The weather example, in both themes — `examples/weather`.*

</div>

> **Status.** The library builds with Axle 0.18 and its gallery runs (the maintainer's own build, on
> Windows). Everything added since — the weather app, tooltip, dialog, toast, and the shell's use of
> smalt's new cursor, clipboard and click APIs — has been written without a compiler and checked by
> the tools in `tools/` (see [Verification](#verification)). `LIMITATIONS.md` says what is built, what
> is unverified and what is missing.

Zaffre draws the interface you would expect from a good web app — rounded surfaces, soft shadows,
real typography, motion — through smalt's CPU frame, with no library outside smalt. The look is
yours: every colour, radius, shadow and duration is a token, every widget is made of named parts,
and a theme is a value.

```rs
let dark = new shared Model<bool>(true);
let volume = new shared Model<f64>(0.62);
let notes = new shared Notifier();

let rowKids : dyn Widget[] = [
    new Button(ButtonProps { label: "Save", kind: ButtonKind::Primary }, () => notes.toast("Saved", Tone::Ok)),
    new Switch("Dark mode", dark),
];
let card = new Panel(PanelProps { elevation: Elevation::Raised }, new Column(FlexProps { gap: 14.0 }, [
    new Label("Preferences", TextRole::H3),
    new Slider(SliderProps { label: "Volume" }, volume),
    new Row(FlexProps { gap: 10.0 }, rowKids),
]));

let view = new View(Theme::dark(), fonts, dark, new Notifications(notes, card));
App::run(AppDesc { title: "demo", width: 640, height: 400 }, view);
```

A widget tree is a nested expression of `new`; the values widgets show are `Model`s the program
holds, so nothing is synchronised by hand; handlers are lambdas over `Shared` handles. Layout is
constraints going down and sizes coming up (`Flex`, `Panel`, `Scroll`, …); drawing goes through a
`Painter` that a CPU backend implements today and a GPU backend could implement tomorrow.

* **[Vision](doc/VISION.md)** — what it is for and the principles
* **[Architecture](doc/ARCHITECTURE.md)** — layers, one frame, memory, styles, widgets
* **[Components](doc/COMPONENTS.md)** — what exists and how far it is verified
* **[Limitations](LIMITATIONS.md)** — what is not here, and what is not proven

## Examples

| | |
|---|---|
| `examples/gallery` | every component on one page; `--snap` writes `gallery.bmp` with no window |
| `examples/weather` | a forecast app: the day hour by hour, the wind, the week ahead (generated data — smalt has no network) |

## Building

```bash
git clone --recursive https://github.com/Axle-lang/zaffre
cd zaffre
axle run -p gallery          # or: axle build
```

`vendor/smalt` is a submodule pinned to smalt's `dev` branch, which carries what the shell uses and
`main` does not yet: `Window::setCursor`, the system clipboard, click counts and `MouseLeft`.

## Verification

There is no `axle` in the environment this was written in, so the code is held by tools, and they are
the reason it mostly compiles first time:

| Tool | What it holds |
|---|---|
| `tools/check.py` | imports resolve, layers never reach upward, no `extern`/`unsafe`, reserved words, names, mutability, member and arity checks (`axparse.py` + `axcheck.py`, calibrated on smalt's own sources) |
| `tools/c_ref/` | C twins of the rasteriser and the kerning reader, checked against FreeType and HarfBuzz |
| `tools/axpy/` | an Axle → Python translator that **runs the real sources**: `test_text.py` (glyphs, advances, coverage vs FreeType), `test_ui.py` (clicks, Tab, typing, drags, menus, dialogs…), `test_weather.py`, and `shot.py` (renders an example to a PNG) |
| `tools/gen_lib.py --check` | `src/lib.axle` names every module |

It is a translator, not the compiler: it cannot say whether Axle accepts a construct, only whether
the logic does what it should. `axle check` remains the last word.

## License

MIT. The bundled fonts (`assets/fonts/`) are under the SIL Open Font License; their licences sit
beside them.
