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
   and `tools/check.py` enforces that. A widget is a function over `Ui`; a custom widget is written
   exactly the way the built-in ones are, with no privileged access.
3. **Style is data, not code.** Tokens → theme → per-widget recipes (variants × sizes × states) →
   per-instance override. Three levels, a fixed order, no cascade and no specificity.
4. **Idle is free.** The loop sleeps in the OS; a frame is built when something changed or something
   is animating; a frame allocates nothing.
5. **One description, two painters.** The widgets emit a draw list. The CPU painter is the reference
   (exact, deterministic, testable by comparing images); a GPU painter is a second consumer of the
   same list, checked against the first.
6. **Say what is not true.** `LIMITATIONS.md` is written from the compiler's answers, not from the
   plan. A component is marked as built, built-and-unverified, or planned.

## The shape of the API: immediate description, retained state

The program redescribes the interface whenever something changed:

```rs
ui.begin(frame);
    ui.column(Gap::md());
        ui.heading("Preferences");
        if (ui.button("Save").clicked) { save(); }
        dark = ui.switchRow("Dark mode", dark);
        volume = ui.slider("Volume", volume, 0.0, 1.0);
    ui.end();
ui.finish();
```

There are no callbacks, because a callback needs a closure and the library does not assume Axle
has one. The library keeps what must outlive a frame — hover and press animations, scroll
offsets, focus, the caret — keyed by a stable id, so the description can be thrown away and
rebuilt without anything jumping.

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

Nothing in smalt blocks the CPU painter. These improve it, and are smalt's to add:

- present a damaged rectangle instead of the whole frame;
- the pointer's shape (netaudit finds its own window by title to set one);
- a clipboard;
- the window's scale factor;
- key repeat on Wayland (the shell synthesises it until then).

A GPU painter wants a 2-D batch pipeline in smalt's `gpu` layer (instanced distance-field quads
and a glyph atlas). Zaffre will not own Vulkan.
