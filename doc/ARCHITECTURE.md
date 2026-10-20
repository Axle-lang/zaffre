# Architecture

## Layers

A module imports from its own layer or below, never above. `tools/check.py` reads every
`use crate::…` and fails the tree on one that reaches up.

```
  7 shell      the window loop: smalt's events in, a frame out, sleep in between          (app, keys)
  6 widgets    label, button, toggles, slider, field, flex, panel, scroll, tabs, select,  (src/widgets)
               alert, badge, progress, tooltip, dialog, toast, notify …
  5 core       the Widget trait, Control, the Context, geometry, events, Model, View      (src/core)
  4 paint      the Painter trait, and the CPU painter over a Canvas                       (src/paint)
  3 style      Palette, Metrics, style records, Theme, variants, easing                   (src/style)
  2 text       TrueType, outlines, kerning, glyph cache, fonts, typesetting, strings      (src/text)
  1 gfx        colour, distance-field shapes, the canvas, the coverage rasteriser         (src/gfx)
  0 smalt      Platform, Window, Events, Surface, Frame, Mem, AssetFile — and nothing else
```

Two rules the layers exist to keep:

* **A widget has no private access.** Everything in `widgets/` uses `Widget`, `Control`, `Context` and
  `Painter` exactly as a program's own widgets do — `examples/weather` draws a compass, a chart and a
  table that way. A third party adds a widget by writing a class.
* **Only `shell` names smalt's window and event types.** Everything below takes plain values
  (`UiEvent`, a `Frame`), so a program that already owns a window — a game painting a menu over its
  own frame — drives a `View` itself with `resize`, `input`, `update`, `render`.

## The tree

The interface is a tree of retained objects. A widget is a class that implements `Widget`:

```
measure(ctx, limits) -> Size      sizes come up, given constraints from above
arrange(ctx, area)                the box it is finally given (it gets the size it returned)
paint(ctx, painter)               draw into that box
event(ctx, e) -> bool             true when the event was used up
tick(ctx, dt) -> bool             advance animations; true while more is moving
```

`Base` keeps the box. `Control : Base` adds hover, press and focus with their eased animations and
turns pointer events into a `Gesture` (`Press`, `Click`, `Drag`, …). Containers (`Flex`/`Column`/`Row`,
`Panel`, `Scroll`, `Tabs`) hold children as `dyn Widget[]`.

Properties are structs with field defaults (`ButtonProps { label: "Save", kind: ButtonKind::Primary }`);
constructors are overloaded for the common cases. A value a program owns is a `Model<T>` shared with
the widgets bound to it. A handler is a lambda that captures only `Shared` handles.

## One frame

```
events ──► View::input(e)        overlays first (topmost down), then the tree
time   ──► View::update(now)     theme follows the dark-mode model; every widget ticks; wakes arm
           View::layout()        measure / arrange the tree and the overlays, rebuild the Tab order
           View::render(frame)   paint the page, then the overlays, through a Painter
```

The shell sleeps in the OS until something happens: nothing changed and nothing animates → wait for
an event or for the next timed wake (a caret to blink, a tooltip's delay); something animates → one
frame at a time; something changed → draw now. A focused text field asks to be woken in half a
second (`Context::wakeIn`), which the view turns into a repaint when it falls due.

## Overlays

A menu, a tooltip, a dialog, a toast is a `Widget` opened with `Context::openOverlay`. The view
lays it out over the whole interface, gives it events before the page, and drops it when `done()`.
`covers(x, y)` makes the page beneath inert under it; `modal()` also empties the Tab order of the page.
A handler has no `Context`, so it holds a `Shared<Notifier>` and a `Notifications` widget around the
root turns its requests into overlays.

## Painting

`Painter` is the one interface widgets draw through: rounded rectangles (per-corner radii, solid or
vertical-gradient brushes), strokes, soft shadows, capsule lines, text (plain, elided, spans), clips and
opacity. `CpuPainter` implements it on a `Canvas` over smalt's `Frame`. Shapes are signed-distance
fields with one pixel of anti-aliasing; shadows are smoothstep falloffs; gradients are dithered with a
4×4 Bayer matrix so they do not band. Icons are capsule segments on a 24×24 grid.

## Text

Parsed here, from the file: `head`, `maxp`, `hhea`, `hmtx`, `cmap` (4 and 12), `loca`, `glyf` with
composites, GPOS pair kerning (formats 1 and 2, through Extension). Rasterised by signed-area
accumulation. Glyphs are cached in an arena by (glyph, quarter-pixel size, one of four sub-pixel
positions). `Fonts` holds Sans, Bold, and optionally Mono (`withMono`); `Typeset` measures, elides and
wraps; `Strings` edits by byte offsets and knows words. Two fonts are embedded as generated source
(`tools/embed_fonts.py`).

## Style

```
Palette (dark | light) + Metrics ──► Theme ──► style records (Button, Field, Toggle, Slider, Panel,
                                               Badge, Progress, Item, Text) ──► the widget
```

A `Theme` rebuilds its tables of style records from the active palette and metrics (`rebuild`,
`setDark`). Variants are enums (`ButtonKind`, `ControlSize`, `Tone`, `TextRole`, `Elevation`); a
widget asks the theme for the record of its variant and draws from it. Replacing a colour or a metric
and calling `rebuild()` restyles everything; a new theme is a new `Palette`.

## Memory

Tables are allocated once and reused: the glyph cache is an arena, the focus order a fixed array, the
overlay list and the toast registry eight slots. A frame allocates nothing beyond the strings a
widget builds for its own text.

## Files

```
src/gfx/      mathx · tint · shapes · canvas · coverage
src/text/     ttf · outline · kern · font · fonts · typeset · strings · data/
src/style/    ease · variants · fill · palette · styles · theme
src/paint/    painter
src/core/     geometry · event · model · context · widget · format · view
src/widgets/  flex · label · spacer · panel · button · icon · toggle · slider · field · badge ·
              progress · scroll · segmented · tabs · alert · select · tooltip · dialog · toast · notify
src/shell/    app · keys
src/lib.axle  generated by tools/gen_lib.py
tools/        check.py · axparse.py · axcheck.py · embed_fonts.py · gen_lib.py · c_ref/ · axpy/
```
