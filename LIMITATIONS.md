# Limitations

What Zaffre does not do, and what has not been proven. Written from what was run, not from the plan.

## 1. Verification

* **Compiler.** The first set of components compiles with Axle 0.18 and the gallery runs (the maintainer's
  build). `Segmented`, `Tabs`, `Select`, `Alert`, `Scroll`, `Tooltip`, `Dialog`, `Toast`, `Notifier`, the
  shell's new code and `examples/weather` were written without a compiler. Expect a round of fixes of the
  kinds the first round had: a struct parameter that must be `own`, an array literal that needs a named
  `let`, a default that must be a literal.
* **What was run instead.** A translator runs the real sources in Python (`tools/axpy`). It checks logic,
  never syntax: whether Axle accepts a construct is the compiler's to say.
* **Rendering** is compared with FreeType for glyph shapes (mean error under 1/255, worst case at
  overlapping contours) and for advances and kerning, and looked at for everything else.
* **Not run anywhere:** the cursor, clipboard and click paths against a real window system; the weather
  example in a window.

## 2. What is not here

* **GPU painter.** `Painter` is the seam; the CPU painter is the only implementation. A GPU one wants a
  2-D batch pipeline in smalt.
* **High-DPI.** Everything is drawn at the pixel size smalt reports; there is no scale factor yet.
* **Text.** No right-to-left, no shaping beyond pair kerning, no combining marks, no IME. A
  `TextField` is single-line; there is no text area.
* **Whole-frame redraw.** A frame repaints the tree. smalt can now present a damaged rectangle
  (`Surface::presentRegion`), but the view does not yet track one.
* **Drag and drop, file dialogs, several windows, accessibility.**
* **Data.** `examples/weather` generates its forecast: smalt has no network. The `Atlas` is the seam a
  real source would fill.

## 3. Platform notes (from smalt)

* The pointer's shape (`Window::setCursor`) and the clipboard come from smalt. On Wayland
  both depend on the compositor (cursor-shape protocol, or a built-in pointer; a data device).
* Key repeat is not synthesised on Wayland.
