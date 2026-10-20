# Components

Status words: **built** — written, checked by the tools, exercised by the translated tests;
**compiled** — also built by `axle` (the maintainer's build of the first set). Nothing is marked
*run on hardware* yet except what the maintainer reports.

## Foundations

| | |
|---|---|
| Palette, Metrics, Theme | built; dark and light; `setDark`, `rebuild` |
| Text roles | Body, Dim, Faint, Caption, Label, H1–H3, Mono, Strong |
| Easing | `Eased` + `Rate`; every hover, press, focus, open and fade is one |
| Icons | Check, Close, Plus, Minus, four chevrons, ArrowRight, Search, Menu, Info, Warning, Dot, Sun |

## Atoms

| Component | State |
|---|---|
| `Label` (roles, wrap, elide, tint) | compiled |
| `Spacer`, `Divider` | compiled |
| `Icon` / `IconView` | compiled |
| `Button` (Primary, Secondary, Ghost, Danger, Link · sizes · icon) | compiled |
| `Checkbox`, `Switch`, `Radio` | compiled |
| `Slider` (step, decimals, label, value readout) | compiled |
| `TextField` (caret, selection, clipboard, word / line select by double / triple click) | compiled; clicks and system clipboard built |
| `Badge`, `Avatar` | compiled |
| `ProgressBar`, `Spinner` | compiled |

## Molecules

| Component | State |
|---|---|
| `Segmented` | built |
| `Tabs` / `TabBar` | built |
| `Select` + `Menu` (overlay, keyboard, flips above) | built |
| `Alert` | built |
| `Tooltip` | built |
| `Toast` (stacked, timed) | built |

## Organisms and containers

| Component | State |
|---|---|
| `Flex` / `Column` / `Row` (gap, padding, align, justify, grow) | compiled |
| `Panel` (elevations) | compiled |
| `Scroll` (wheel, draggable thumb, clipped) | built |
| `Dialog` (modal, focus trap, Escape / Enter) | built |
| `Notifier` + `Notifications` (open toasts and dialogs from a handler) | built |
| `View` (overlays, dark-mode model, timed wakes), `App` | compiled; the shell's cursor, clipboard and click code built |

## Not yet written

Accordion, pagination, number input, form field, popover, drawer, table / data grid, virtual list,
tree, text area, command palette, charts as library widgets (`examples/weather` has one), split pane,
radio group, chips with a close button, skeleton, kbd. A GPU painter. Right-to-left and shaped text.

## In `examples/weather`

Written against the public API only, as an application would: `NowCard`, `WindCard` (a compass),
`HourChart` (a spline with hover card and scrubbing, four curves), `HourRows` and `WeekList`
(pickable rows), sky icons drawn from shapes. They are the best test of whether the library's
extension points are enough, and they were.
