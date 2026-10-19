# Architecture

## Layers

A module imports from its own layer or below. Never above. `tools/check.py` reads every
`use crate::…` and fails the tree on one that reaches up.

```
 12 shell        the window loop: events in, a frame built when needed, presented, snapshots
 11 organisms    dialog, table, tree, text area, charts …              (functions over `Ui`)
 10 molecules    form field, select, tabs, menu, tooltip, toast …      (functions over `Ui`)
  9 atoms        text, icon, button, checkbox, switch, slider, field …  (functions over `Ui`)
  8 ui           the `Ui` context: begin / end, ids, responses, popups, focus, scroll
  7 input        pointer, keyboard, text-edit commands
  6 draw         the draw list, and the CPU painter that consumes it
  5 layout       measure / arrange: stack, flex, overlay; scroll extents
  4 tree         the node arena, widget ids, the persistent state store
  3 style        tokens, themes, recipes, transitions
  2 text         TrueType, glyph rasterisation and cache, shaping-lite, line layout
  1 gfx          colour, coverage rasteriser, shapes, shadows, gradients, the canvas
  0 (smalt)      Platform, Window, Events, Surface, Frame, Mem, AssetFile — and nothing else
```

Two rules the layers exist to keep:

* **A widget has no private access.** Layers 9–11 use `Ui` exactly as a program's own widgets do.
  A third party adds a widget by writing a function; it does not touch the core.
* **Only `shell` and the examples name smalt's window/event types.** Everything below `shell` takes
  plain values (a pointer position, a key code, a `Frame`), so the library can be driven by a
  program that already owns its window — a game painting a HUD over its own frame.

## One frame

```
events ──► Ui::begin(input)      pointer / keys / text become this frame's input
              │
  program ──► widget calls         each call appends a node, resolves its style against
              │                    the id's persistent state (hover, press, focus, animation),
              │                    and returns a Response computed from LAST frame's rectangles
              ▼
          Ui::finish()           layout (measure, arrange) → draw list → painter
              │                    animations that are not finished ask for another frame
              ▼
          Canvas (CPU)  or  a GPU painter over the same draw list
```

Hit-testing against the previous frame's layout is what makes `if (ui.button("x").clicked)` work
without callbacks: the rectangle a button had when the user pressed is the rectangle that answers.

## Memory

Every table is allocated once from a `UiDesc` (node capacity, text bytes, state slots, glyph
cache bytes) and reused. A frame allocates nothing. A table that fills answers by degrading, not
by growing: extra nodes are dropped and `Ui::overflowed()` says so, which the debug overlay shows.

## Style resolution

```
tokens ──► Theme ──► Recipe(widget) ──► Style(part, state)  ◄── instance override (StyleOverride)
```

* A **token** is a named value (colour, length, duration).
* A **theme** is a set of tokens plus the recipes built from them. `Theme::dark()`, `Theme::light()`,
  and any theme a program makes by changing tokens and calling `rebuild()`.
* A **recipe** gives each widget's *parts* (root, label, icon, track, thumb …) a style per *state*
  (rest, hover, pressed, focus, disabled, checked), varying by *variant* and *size*.
* An **override** on one call site wins last. That is the whole cascade.

## Files

```
src/gfx/      tint · mathx · coverage · canvas · shapes
src/text/     ttf · outline · glyphs · font · layout
src/style/    token · theme · style · ease
src/tree/     ids · arena · store
src/layout/   measure · flex
src/draw/     list · cpu
src/input/    pointer · keys · edit
src/ui/       ui · response · popup
src/widgets/  atoms · molecules · organisms
src/shell/    app · snapshot
tools/        check.py · c_ref/ (reference implementations the Axle is transliterated from)
```
