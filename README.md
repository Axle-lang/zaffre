<div align="center">

# 🔷 Zaffre

### A native UI library for Axle — soft, typographic, themeable, and nothing but [smalt](https://github.com/Axle-lang/smalt)

</div>

> **Status: work in progress, not yet compiled.** The Axle compiler was not available while this
> was written, so the code has been checked by the tools in `tools/` (imports, layers, mutability,
> and C twins of the numeric kernels checked against FreeType) and by nobody's `axle check` yet.
> `LIMITATIONS.md` lists what is built, what is unverified, and what is only planned.

Zaffre draws the interface you would expect from a good web app — rounded surfaces, soft shadows,
real typography, motion — through smalt's CPU frame, with no library outside smalt. It is written
so that the look is yours: every colour, radius, shadow and duration is a token, every widget is
made of named parts, and a theme is a value.

```rs
let mut ui = new Ui(UiDesc { });
…
ui.begin(input);
    ui.column();
        ui.heading("Preferences");
        if (ui.button("Save").clicked) { save(); }
        dark = ui.switchRow("Dark mode", dark);
    ui.end();
ui.finish(frame);
```

* **[Vision](doc/VISION.md)** — what it is for and the principles
* **[Architecture](doc/ARCHITECTURE.md)** — layers, one frame, memory, style resolution
* **[Components](doc/COMPONENTS.md)** — what exists and how far it is verified

## Building

```bash
git clone --recursive https://github.com/Axle-lang/zaffre
cd zaffre
axle build
```

The only prerequisite is the Axle compiler, as smalt requires it.

## License

MIT. The bundled fonts (`assets/fonts/`) are under the SIL Open Font License; their licences sit
beside them.
