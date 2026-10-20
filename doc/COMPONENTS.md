## Foundations

| | |
|---|---|
| Palette, Metrics, Theme | built; dark and light; `setDark`, `rebuild`. Tokens follow a web design system: page / surface / surface-2, four greys of text, a hairline and a strong line, six hues (500–800), and one *soft tone* recipe per colour (wash, hover, border, ink) that badges, alerts, toasts, selected rows and secondary buttons all draw from. |
| Radius roles | inline 6, control 8, surface 12, overlay 16, pill |
| Control heights | 32 / 36 / 40 / 48 / 56 (`Metrics::compact()`: 28 … 48) |
| Elevations | Flat, Raised, Lifted, Overlay, Floating — each two shadow layers, a tight one and a wide one |
| Focus | a 2 px ring offset by 2 px; bordered fields take a 3 px halo instead (red when invalid) |
| Text roles | Body, Dim, Faint, Caption, Label, H1–H3, Mono, Strong |
| Easing | `Eased` + `Rate`; every hover, press, focus, open and fade is one |
| Icons | 44 stroked icons on a 24-unit grid (`doc/img/icons.png`) |
| Cursors | Arrow, Hand, Beam, ResizeH/V, Wait, NotAllowed, Move |

## Atoms

`Label`, `Spacer`, `Divider`, `LabeledDivider`, `Icon`, `IconDisc`, `Button` (nine kinds · five sizes ·
icon, icon-only · loading · disabled · block), `Checkbox`, `Switch`, `Radio`, `Slider`, `TextField`
(icon, clearable, invalid), `Textarea`, `Select`, `Segmented`, `ToggleGroup`, `Rating`,
`QuantityInput`, `Badge` (six tones · subtle or solid · three sizes · dot), `StatusPill`, `Tag`,
`Dot`, `Kbd`, `Avatar` (presence dot), `AvatarGroup`, `ProgressBar`, `ProgressRing`, `Spinner`,
`Skeleton` (ten shapes), `Sparkline`.

## Molecules

`FormField` (label, hint, error), `Alert`, `Banner`, `Callout`, `Tabs` / `TabBar`, `Breadcrumb`,
`Pagination`, `Stepper`, `Accordion` (cards or flush, single or multiple), `Tooltip`, `Toast`,
`Stat`, `EmptyState`, `ItemList`, `DescriptionList`, `Timeline`, `Band`.

## Organisms and containers

`Flex` / `Column` / `Row`, `Panel`, `Card` (header, body, footer, pressable), `Scroll`, `Table`
(widget cells, column widths, sortable headers, picked row), `Sidebar`, `Navbar`, `TopBar`,
`AppShell`, `PageStack`, `LineChart`, `BarChart`, `DonutChart`, `BarList` (with `ChartKit`:
scale, grid, hover card, series colours).

## Overlays

`Select` menu, `MenuButton` / `DropdownMenu` (icons, shortcuts, separators, danger rows),
`Popover`, `Dialog`, `Sheet` (modal and drawers from either edge), `CommandPalette`, `Tooltip`,
`Toast`. A handler opens dialogs, sheets, toasts and the palette through `Notifier` +
`Notifications`; a popover builds its content from a function each time it opens.

## Application

`View` (overlays, dark-mode model, timed wakes), `App` (window loop, cursors, clipboard, clicks).

## Added since

`Calendar` (single day or range) and `DatePicker` (with `Dates`: days since 1970, no calendar library),
`Combobox` and `MultiSelect` (search, chips), `InputOTP`, `TagsInput`, `CodeBlock` (highlighting, line
numbers, copy button), `CodeWindow`, `CopyCommand`, `InlineCode`, `TextLink`, `Split` (draggable
divider), `Grid`, `Collapsible`, `Toolbar`, `OverlayBadge`, `HoverCard`, `UserMenu`.

Later still: `DatePicker` rebuilt as a typed field (`Dates::parse` reads "20 Oct 2026", "2026-10-20",
"20/10/2026"; a calendar button, Down key, min/max, red once left with a bad date), `Calendar` with a
month and year grid, range preview, keyboard ring, Today/Clear footer and a `framed` look,
`DateRangePicker` (presets column + calendar), `ButtonGroup`, `SplitButton`, `SortableList` (drag or
Space + arrows, shared `Order`), `TransferList`, `LatencyIndicator`, `Eyebrow`. Toasts take a title and a
detail (`notes.notify`) and sit bottom-right with a dismiss cross. Dialog follows the web layout
(header, body, footer band, close cross). Labels, buttons, tabs and badges use a Medium weight.

## Not yet written

Virtual list, tree, file input, a GPU painter, right-to-left and shaped text.

## In `examples/weather`

Written against the public API only, as an application would: `NowCard`, `WindCard` (a compass),
`HourChart` (a spline with hover card and scrubbing, four curves), `HourRows` and `WeekList`
(pickable rows), sky icons drawn from shapes. They are the best test of whether the library's
extension points are enough, and they were.
