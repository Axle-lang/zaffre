# Limitations

What Zaffre does not do, and what has not been proven. Written from what was run, not from the plan.

## 1. Verification

* **Compiler.** The library and both examples compile with Axle 0.22, the minimum: 0.22 asks for `mut` on
  every parameter written through (the `Context` and `Painter` a widget is handed among them), and 0.21
  refuses those same `mut`s as never used. On Windows both examples build and `--snap` draws a frame. For
  Linux, both pass `axle check --deep` against smalt's X11 port and its Wayland port, checked from Windows:
  nothing has been linked or run on Linux.
* **Gallery teardown.** `gallery --snap` writes the right frame, then exits with `0xC0000374` (heap
  corruption) while the program releases what it built. It did the same with Axle 0.21 before the move to
  0.22; `weather --snap` exits 0.
* **What was run before the compiler could.** An Axle → Python translator (`tools/axpy`, since removed
  from the tree) ran the real sources. It checked logic, never syntax.
* **Rendering** was compared, by the C references once in `tools/c_ref/`, with FreeType for glyph shapes (mean error under 1/255, worst case at
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
