# Zaffre — vision

A native UI library for [Axle](https://axle-lang.dev), built on [smalt](https://github.com/Axle-lang/smalt)
and on nothing else. It should look like the web at its best — rounded, soft, typographic — and
none of the Windows 95 it is replacing.

*Zaffre* is the roasted cobalt ore that is fused with glass and ground to make *smalt*. The
library sits one step upstream of the pigment it paints with.

## What it is for

| For | Means |
|---|---|
| A tool (netaudit, an inspector, a launcher) | Forms, tables, trees, dialogs, a theme that does not look like a toolkit's default |
| A game's menus and HUD (voxel-axle) | The same widgets over a frame that something else drew |
| A program that wants *its own* look | Every colour, radius, shadow, font, duration and spacing is a token; every widget's parts take a style; a theme is a value or a file |

## Principles

1. **Nothing outside smalt.** No C library, no font loader, no image decoder. TrueType is parsed here,
   glyphs are rasterised here, icons are paths here. The only bundled data is two fonts under the
   SIL OFL, and they can be replaced.
2. **Modular all the way down.** Each layer (see `ARCHITECTURE.md`) imports only the ones below it,
   and `tools/check.py` enforces that. A widget is a class that implements `Widget`; a custom widget is
   written exactly the way the built-in ones are, with no privileged access.
3. **Style is data, not code.** Palette and metrics → theme → per-widget style records (variants ×
   sizes), rebuilt when either changes. No cascade and no specificity.
4. **Idle is free.** The loop sleeps in the OS; a frame is built when something changed or something
   is animating; a frame allocates nothing.
5. **One interface, two painters.** Widgets draw through `Painter`. The CPU painter is the reference
   (exact, deterministic, testable by comparing images); a GPU painter would be a second implementation,
   checked against the first.
6. **Say what is not true.** `LIMITATIONS.md` is written from the compiler's answers, not from the
   plan. A component is marked as built, built-and-unverified, or planned.

## The shape of the API: a tree of objects, values in models

The interface is a tree of retained widgets built as one nested expression, and the values it shows
live in `Model`s the program owns:

```rs
let volume = new shared Model<f64>(0.62);
let card = new Panel(PanelProps { }, new Column(FlexProps { gap: 14.0 }, [
    new Label("Preferences", TextRole::H3),
    new Slider(SliderProps { label: "Volume" }, volume),
    new Button("Save", () => notes.toast("Saved", Tone::Ok)),
]));
```

Handlers are lambdas over `Shared` handles; the widgets read their model when they paint, so choosing
something anywhere changes everything that depends on it. State that outlives a frame — hover and
press animations, scroll offsets, focus, the caret — lives in the widgets, which are not rebuilt.
An immediate-mode `ui.button("Save")` style was considered and set aside: it cannot use what Axle is
good at (classes, traits, enums, generics, overloaded constructors).

## What is in it

The levels follow atomic design. Each level may use the ones before it and nothing after.

| Level | Contents |
|---|---|
| 0 Foundations | colour, type scale, spacing, radius, elevation, motion, icon set — the *tokens* |
| 1 Atoms | box/stack, text, icon, image, divider, spacer, badge, avatar, spinner, progress, skeleton, kbd · button, checkbox, radio, switch, slider, text field, chip, link |
| 2 Molecules | form field, search field, select, number input, tabs, segmented control, menu, tooltip, popover, toast, alert, accordion, pagination, list item, stat card |
| 3 Organisms | dialog, drawer, sidebar, table / data grid, virtual list, tree, command palette, calendar, colour picker, text area, charts, split pane |
| 4 Templates | app shell, settings page, dashboard |
| 5 Applications | netaudit and voxel-axle, rewritten on it — the tests that count |

`doc/COMPONENTS.md` is the live status of each.

## What it needs from smalt

The pointer's shape, the system clipboard, click counts, a damaged-rectangle present and the pointer
leaving the window are in smalt's `dev` branch and used by the shell. Still missing: the window's scale
factor, key repeat on Wayland, and a 2-D batch pipeline for a GPU painter (instanced distance-field
quads and a glyph atlas) — Zaffre will not own Vulkan.
