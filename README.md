<div align="center">

# 🔷 Zaffre

### A native UI library for [**Axle**](https://axle-lang.dev) — soft, typographic, themeable, and nothing but [smalt](https://github.com/Axle-lang/smalt)

<p align="center">
  <a href="https://axle-lang.dev"><img alt="Powered by Axle 0.22" src="https://img.shields.io/badge/powered%20by-Axle%200.22-5B4BE1?style=for-the-badge&labelColor=1b1b2b"></a>
  <a href="https://github.com/Axle-lang/smalt"><img alt="Built on smalt" src="https://img.shields.io/badge/built%20on-smalt-1D6FB8?style=for-the-badge&labelColor=1b1b2b"></a>
</p>
<p align="center">
  <img alt="Rendering: CPU" src="https://img.shields.io/badge/rendering-CPU-FF7A45?style=flat-square&labelColor=1b1b2b">
  <img alt="Dependencies: smalt only" src="https://img.shields.io/badge/dependencies-smalt%20only-2E7D32?style=flat-square&labelColor=1b1b2b">
  <img alt="Themes: light and dark" src="https://img.shields.io/badge/themes-light%20%C2%B7%20dark-9C27B0?style=flat-square&labelColor=1b1b2b">
  <img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-555555?style=flat-square&labelColor=1b1b2b">
</p>

<img src="doc/img/gallery-data-dark.png" width="49%"> <img src="doc/img/gallery-forms-light.png" width="49%">
<img src="doc/img/weather-dark.png" width="49%"> <img src="doc/img/weather-light.png" width="49%">

<sub>The gallery's data page in the dark theme and its forms page in the light one, then the weather example in both — all written by the programs themselves: <code>--snap</code> draws one frame and puts it in a file.</sub>

<br>

<sub><a href="#examples">Examples</a> · <a href="#building">Building</a> · <a href="#verification">Verification</a> · <a href="doc/VISION.md">Vision</a> · <a href="doc/ARCHITECTURE.md">Architecture</a> · <a href="doc/COMPONENTS.md">Components</a> · <a href="LIMITATIONS.md">Limitations</a> · <a href="https://github.com/Axle-lang/smalt">smalt ↗</a> · <a href="https://axle-lang.dev">Axle ↗</a></sub>

</div>

---

> **Status.** The library and its two examples build with Axle 0.22 (the minimum compiler), on Windows, and
> pass `axle check --deep` for Linux on both of smalt's ports there (X11, and Wayland);
> `axle check --deep` is the last word, and CI builds both examples on each of smalt's ports (see [Verification](#verification)).
> `LIMITATIONS.md` says what is built, what is unverified and what is missing.

Zaffre draws the interface you would expect from a good web app — rounded surfaces, soft shadows,
real typography, motion — through smalt's CPU frame, with no library outside smalt. The look is
yours: every colour, radius, shadow and duration is a token, every widget is made of named parts,
and a theme is a value.

```rs
use zaffre::{
    View, Theme, Fonts, App, AppDesc, Notifier, Notifications, Model, Widget, Button, ButtonProps,
    ButtonKind, Switch, Panel, PanelProps, Elevation, Column, Row, FlexProps, Label, TextRole, Slider,
    SliderProps, Tone,
    // Named by the defaults of the structs above, so the program names them too.
    Insets, Length, ControlSize, IconKind, Align, Justify,
};

fn main() : i32 {
    let fonts : Shared<Fonts> = share new Fonts();
    let dark = share new Model<bool>(true);
    let volume = share new Model<f64>(0.62);
    let notes = share new Notifier();

    let save = new Button(
        ButtonProps { label: "Save", kind: ButtonKind::Primary },
        () => notes.toast("Saved", Tone::Ok)
    );
    let actions : dyn Widget[] = [save, new Switch("Dark mode", dark)];
    let kids : dyn Widget[] = [
        new Label("Preferences", TextRole::H3),
        new Slider(SliderProps { label: "Volume" }, volume),
        new Row(FlexProps { gap: 10.0 }, actions),
    ];
    let column = new Column(FlexProps { gap: 14.0 }, kids);
    let card = new Panel(PanelProps { elevation: Elevation::Raised }, column);

    let view = new View(Theme::dark(), fonts, dark, new Notifications(notes, card));
    return App::run(AppDesc { title: "demo", width: 640, height: 400 }, view);
}
```

A widget tree is built from `new`, children going in a `dyn Widget[]` a parent takes; the values
widgets show are `Model`s the program holds, so nothing is synchronised by hand; handlers are lambdas
over `Shared` handles. Layout is
constraints going down and sizes coming up (`Flex`, `Panel`, `Scroll`, …); drawing goes through a
`Painter` that a CPU backend implements today and a GPU backend could implement tomorrow.

* **[Vision](doc/VISION.md)** — what it is for and the principles
* **[Architecture](doc/ARCHITECTURE.md)** — layers, one frame, memory, styles, widgets
* **[Components](doc/COMPONENTS.md)** — what exists and how far it is verified
* **[Limitations](LIMITATIONS.md)** — what is not here, and what is not proven

## Examples

| | |
|---|---|
| `examples/gallery` | every component, in an application of its own: a sidebar, a top bar, one page per section; `--snap` writes `gallery.bmp` with no window |
| `examples/weather` | a forecast app: the day hour by hour, the wind, the week ahead (generated data — smalt has no network) |

## Building

```bash
git clone --recursive https://github.com/Axle-lang/zaffre
cd zaffre
cd examples/gallery
axle run                     # or: axle build; add -- --snap for a picture with no window
```

`vendor/smalt` is a submodule pinned to smalt's `main` branch, which carries what the shell uses:
`Window::setCursor`, the system clipboard, click counts and `MouseLeft`.

## Verification

`axle check` (or `axle build`) is the compiler's word. CI ([`.github/workflows/ci.yml`](.github/workflows/ci.yml))
runs it on every push and pull request to `dev` or `main`:

| Job | What it holds |
|---|---|
| `layers` | a module never imports from a layer above its own, and nothing in zaffre is `extern` or `unsafe` |
| `windows` | the Win32 port: both examples build, and `--snap` draws a frame |
| `linux` | the X11 port: the same |
| `wayland` | the Wayland port, asked for on each example's edge to smalt and checked active; its build reports without failing the run until it has linked once |

The gallery is also the integration test: `--snap` draws a frame with no window, and a program can
feed `View::input` its own events to click, type and scroll in it.

## License

MIT. The bundled fonts (`assets/fonts/`) are under the SIL Open Font License; their licences sit
beside them.
