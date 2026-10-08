# Smolify a book — interactive prototype

The **Bulk recording** flow from *Smoly App Design* (`781:26595`), built against the
**Smoly Material Library** (`7Js3isvjdjVoFWNoPPpWo4`).

## Running it

```bash
cd smoly-smolify-book
python3 serve.py            # http://127.0.0.1:8787/
python3 serve.py --lan      # also reachable from a phone on the same wi-fi
```

`serve.py` sends `no-store` on everything. Use it rather than `python3 -m http.server`:
that one lets the browser hold on to `components.css` and `app.js`, so edits look like
they did nothing until a hard reload. Pass a port number as an argument to change it.

It serves **only this folder**, never the parent — the project folder around it holds
client documents. `--lan` makes it reachable by anyone on the same network for as long as
it runs, so stop it with ctrl-C when you are done.

Must be served, not opened as a `file://` URL — the SVG assets and `app.js` need a real
origin.

This folder is self-contained: it can be copied, zipped or published anywhere as-is.

## Reviewing full screen

On a desktop window the prototype sits in a 390×844 device frame, which is what you want
for checking it against Figma. On a phone that frame is just in the way, so below 440px —
and whenever the page is launched from the home screen — it is dropped: the layout fills
the viewport, the drawn status bar gives way to the real one, and the app bar and nav bar
grow by the safe-area insets so nothing sits under the notch or the home indicator.

**Losing the browser bar as well** takes Add to Home Screen. Open the index on the phone,
tap Share → Add to Home Screen, then launch from the icon — `manifest.webmanifest` and the
`apple-mobile-web-app-capable` tags make it open standalone, with no address bar and no
toolbar. The index shows a one-line reminder on phone-width screens, and hides it once
you are running standalone. Android/Chrome offers the same thing as Install app.

### How the shell is sized

The frame is a 390×844 artboard on desktop only. In full-screen mode it is driven by the
viewport instead, and three rules keep it from bleeding on a device taller than 844:

- **The document never scrolls.** `html, body` are pinned to `100dvh` with
  `overflow: hidden`. `100vh` on iOS is the *toolbar-hidden* height, so a body sized to it
  is taller than what you can actually see — the page then scrolls behind the shell and
  the backdrop shows at the edges. `dvh` tracks the toolbar; `vh` is kept as a fallback
  line for older Safari.
- **`.screen` is the only scroller, and its bounce stays put.**
  `overscroll-behavior: contain` stops a rubber-band at either end chaining out to the
  document and flashing the backdrop.
- **Scroll travel comes from the screen height, not a fixed number.**
  `.contents-frame` is `min-height: calc(100% + 24px)` against `.screen`, so travel always
  works out as *(height of whatever bars are showing) + 24* — enough to bury them on any
  device, with nothing left over. It was a hard-coded 1153 (Figma's frame height), which
  left ~565px of dead cream on a 932-tall phone and would have been too little on a
  shorter one.

- **A trailing 30% keeps the last control off the nav bar.** `.screen-tail` is
  `height: 30%` of `.screen`, so at maximum scroll there is always about a third of a
  screen of cream between the bulk buttons and the nav bar. Without it the frame ended
  24px under those buttons: nothing left to scroll, and centring a newly added tile had
  nowhere to go. A percentage rather than a `vh` unit or a fixed number — the scroller has
  a definite height in both modes, so one rule gives 30% of the 844 artboard on desktop
  and 30% of the real viewport full screen.

Measured: 375×667 travel 130 vs 64 of bars; 430×932 travel 88 vs 64; 390 desktop with the
drawn status bar travel 150 vs 126. Both bars fully buried at maximum scroll in each case.
With the tail and two tiles: 764-tall scroller, 229 tail, 253 between the secondary button
and the nav bar, in both desktop and full-screen modes.

Below 440px the fixed Figma widths become fluid (`max-width` rather than `width`) so the
layout does not overflow on a 375px phone — an SE or a mini. At 390 and above every
measurement is still exactly the Figma value.

The device frame is an `outline` with a negative offset rather than a `border`, for the
same reason the audio tile uses an inset ring: a 1px border would take 2px out of the
inner width and leave the content area at 388 where Figma's frame is a true 390 with the
stroke inside it.

## Files

| File | What it holds |
|---|---|
| `index.html` | Prototype index — the entry page, one button per prototype |
| `smolify-book.html` | The flow, with the halo around the record dial while recording |
| `smolify-book-flat.html` | Identical, with the halo removed |
| `tokens.css` | Every colour, shape, spacing and type token, read from the library's variable collections |
| `components.css` | Button, Icon button, Text field, Switch, Top app bar, Navigation bar, Status chip, Audio tile, Bottom sheet, Menu |
| `app.js` | The flow state machine, waveform and overflow menu — shared by both builds |
| `assets/` | `curve-top.svg` `sheet-curve.svg` `drag-indicator.svg` `switch-handle.svg` `slider-thumb.svg` `cover.png` |
| `serve.py` | No-cache dev server, with a `--lan` mode for phone testing |
| `prefs.js` | Viewing preferences shared by the index and the prototypes |
| `decisions.html` | Design decisions, Figma conflicts and implementation conventions — the handoff doc |
| `archive/` | Superseded prototypes, kept so the index is self-contained |

### The two builds

They differ by **one attribute**: `<body data-motion="pulse">` vs `data-motion="flat">`.
The halo rule is scoped to that attribute, so nothing else diverges. If you edit one,
regenerate the other rather than hand-editing both:

```bash
sed -e 's|<body data-motion="pulse">|<body data-motion="flat">|' \
    -e 's|<title>Smoly — Smolify a book</title>|<title>Smoly — Smolify a book (no dial halo)</title>|' \
    smolify-book.html > smolify-book-flat.html
```

The `<body ` prefix matters — the halo's CSS selector also contains
`data-motion="pulse"`, and an unanchored substitution would rewrite that too and
leave the halo switched on. Check with `diff`: exactly two lines should differ.

## The flow

```
empty ──Record Front Page │ Add │ Create──▶ tile dissolves in (No audio)
                                              ▼  tile centres itself, 800ms pause
                                           sheet slides in — "Tap to start"
                                              ▼  tap dial, recording starts at once
                                           Recording ──tap dial──▶ Recorded
                                              │
                   ┌──────────────────────────┤
              tap dial ⇄ Listen back    Record next audio
                                              │
                        sheet slides out ▸ previous tile ▸ Unlinked
                        ▸ new tile dissolves in ▸ 800ms ▸ sheet returns
                                              │
                     dismiss sheet with 2+ unlinked ──▶ bulk actions
```

Chip states: **No audio** (created, nothing recorded) → **Unlinked** (recorded, no sticker)
→ **Linked**. The undo button in the sheet returns a tile to *No audio*.

**Inline playback.** Tapping the name/chip of a tile that has audio expands it into the
player from `831:28243` — scrubber, elapsed / remaining, and `replay_5` · play/pause ·
`forward_5`. One tile is open at a time; opening another, collapsing, deleting or
re-recording stops playback. Tiles still on *No audio* do not expand, since there is
nothing to play — use **Record audio** in their overflow menu.

**The bulk pair under the list** is present whenever there is a list and no sheet in the
way. The primary is always live. The secondary counts the recordings still waiting for a
sticker — `Link sticker` disabled at none, then `Link 1 sticker`, then `Link n stickers`.
Already-linked recordings are not counted.

**Changing the cover.** *Change photo* opens a menu — Photo library · Take a photo ·
Choose file — all three landing on one file input, with `capture` added for the camera
route. Picking an image swaps the cover for real, so the prototype demos with the right
book. See `decisions.html` for why the menu is drawn rather than left to the OS sheet.

## Motion and timing rules

- **The tile is always seen before the sheet.** Every entry point adds the tile, lets it
  dissolve in and centre itself, waits `SHEET_DELAY` (800ms), then opens the sheet. When a
  sheet is already up — the *Record next audio* path — it slides out first and the delay
  starts after it has cleared.
- **A new tile scrolls to the middle of the screen**, not the bottom. It is the thing the
  user just made, so it should be what they are looking at when the sheet arrives.
- **Recording starts on tap.** No lead-in.
- **The contents frame rides over both bars.** The status bar sticks at `top: 0` and the
  app bar at `top: 62` — stacked, not overlapping — and the curved contents frame scrolls
  above both. Scrolling down buries the app bar, then the status bar; scrolling back up,
  or an overscroll drag, uncovers them progressively. Both bars stay put the whole time;
  it is the content that moves. This follows the Figma structure, where the app bar is
  sticky and the contents frame is absolutely placed at `top: 64`. The arch and the body below it are one element
  (`.contents-frame`) overlapped by 1px, so no device background shows through the seam.
  The 4px of surface above the cover is **padding on `.contents`, not a margin on the
  cover** — a top margin on the first child collapses out of its parent and drags the
  whole frame 4px down the page, opening a band of device blue under the arch.
- **The nav bar is always in front.** `.screen` carries `z-index: 0` so the contents
  frame's own stacking stays inside the scroller, and the nav bar sits at `z-index: 3` —
  otherwise the scrolling content paints over the bar and clips the Create button.
- **Sheet and expand both run 300ms `ease-out`.**
- **Entrance animations clean up after themselves.** `is-entering` is removed on
  `animationend` with a timer as backstop; leaving it on means the tile leans on
  `animation-fill-mode` forever and parks at 97% and blurred if the animation never runs
  (backgrounded tab, throttled frames).

## Where the numbers came from

Everything below is read from Figma, not estimated.

**Screen** — 390 frame, 15px gutter → 360 content. Cover 360×204 (art laid in at 367 wide,
x=-3). Fields 360×56, 16px apart. Sequence toggle 40 tall, switch 52×32 offset 4. Recording
header 358×48. The list frame carries its own 12px vertical padding, so header→first tile
reads as 24px. Tile pitch 60 (52 + 8). The contents frame is 1175 tall (22 curve + 1153),
which is what gives it enough travel to scroll clear of the app bar.

**Audio tile** — card radius `corner/medium`, padding 10/16, 52 collapsed and 136
expanded. Front-page variant is the full 358; the numbered variant is a 30×30 drag handle
+ 4px + a 324 card. Label → 8px → chip. Trailing `⋯` is 20×28 with 16px of right padding.

The card's outline is an **inset box-shadow, not a `border`**. The tile's height is
content-driven, so a 1px border would add 2px and give 54 / 138 where Figma's inside
stroke gives 52 / 136 — and every nested measurement would inherit the drift.

**Inline player** (`831:28243`, Variant3) — 12 below the head row, then 72: 8 padding,
a 4-tall track on `pressed-surface-container-high` with a 12 thumb, 4 gap, the times row
(Label/Small, `-8` margin so it overlaps the transport), a 32 transport row of three
32×32 icon buttons 8 apart, 8 padding. The middle button is `secondary-container` with
the glyph in `on-secondary-container`; the outer two are `on-surface`.

**Status chip** — 32 tall, `corner/small`, padding-left 8 / padding-right 16, gap 8, 18px
icon, Label/Large. `No audio` yellow-container, `Unlinked` orange-container with the icon in
`orange`, `Linked` tertiary-container with the icon in `tertiary`.

**Bottom sheet** — 16px curved cap, 56 title bar (padding 8/24), slot padding 0/16/24 with
16px gaps. Transport row is exactly 110 tall with a 40px gap either side of the dial; the
dial is a 96 ring with a 4.8px `surface` border inside a 110 box. Action buttons 56 tall,
16px apart. Sheet heights land on 270 / 326 / 486, matching the Figma frames.

**Waveform** — the 36 bars are the literal geometry of the Figma `Sound wave` frame
(211.969 × 29.411, 3px bars on a 6px pitch), stored as a table in `app.js`. Recorded bars
are `surface-dim`; played bars are `primary`.

**Buttons** — pulled from the library component set, not inferred:
`Small/Filled` 40 tall, padding 16, Label/Large, label `--smoly-color-button-on-filled`;
`Small/Tonal` secondary-container + on-secondary-container; `XSmall/Text` 32 tall, padding
12, label **`on-primary-container` `#8f043f`** (the "Add" button — it is not `primary`);
`Medium` 56 tall, padding 24, Title/Medium.

## Things I added, and things that disagree

**Added — not in the Figma section.** Flagged so they read as proposals, not as your design:

- **The "Link N stickers" screen state.** You described it but there is no frame for it.
  Composed from the Medium button at the same 56/16 rhythm as the sheet's pair.
- **Scrim, toast, and the halo around the dial while recording** (the halo only in
  `smolify-book.html`).
- **The status bar is covered rather than scrolled away.** In the Figma structure it sits
  in the scroll flow and scrolls off entirely. Here it sticks at `top: 0` and the contents
  frame paints over it, so it is buried on the way down and uncovered on the way back —
  the bar itself never moves.

**Disagreements inside the Figma file.** I picked one and noted it rather than silently
averaging:

- **Timer format.** The Front Page sheet reads `00:00:27 / 00:20:00`; the `Recording - #1`
  sheets read `00:27 / 20:00`. The prototype uses `mm:ss / 20:00`. Worth settling in the file.
- **`smoly-ui/` is stale.** That older library in this project mirrors a different system
  (`--sm-*` names, green primary `#598300`). The current library is `--md-sys-*` with pink
  `#f15a86`. Nothing here depends on `smoly-ui/` — but it will mislead whoever opens it next.

## Tuning

Top of `app.js`:

| Constant | Default | Effect |
|---|---|---|
| `SHEET_DELAY` | `800` | ms the new tile is on screen alone before the sheet arrives |
| `SHEET_EXIT` | `320` | Sheet slide-out duration; must match the CSS transition |
| `MAX_SECONDS` | `1200` | The 20:00 ceiling in the timer |
| `WAVE_FULL_SCALE` | `27` | Seconds of audio that fill the waveform |
| `BULK_THRESHOLD` | `2` | Unlinked tiles before the bulk actions appear |

## The status bar toggle

The index has a **Viewing → iOS status bar** switch. On it draws the status bar inside
the device frame; off it leaves the job to whatever the real device shows.

The default is picked per device rather than being a fixed value: off on a phone-sized
window or when launched from the home screen, on anywhere else. Flip it and the choice
sticks in `localStorage`, which is per-device, so your desktop and your phone each keep
their own answer without knowing about each other.

The preference beats the viewport rule in both directions — status bar on a phone, or off
on a desktop for a clean screenshot. `prefs.js` loads in `<head>` and sets
`data-statusbar` on `<html>` before first paint, so there is no flash of the wrong state.

Two things to keep in step when touching this:

- **The app bar's sticky offset follows the status bar** (`top: 62` with, `top: 0`
  without). Sticky pins an element as soon as its natural position is above the
  threshold, so leaving the offset at 62 with nothing above it shoves the app bar 62px
  *down* the page and the contents frame then covers it.
- **Whichever bar is topmost carries `env(safe-area-inset-top)`** on a phone, or the
  content runs under the notch.

The archived prototype has its own markup and ignores the toggle.

## Before publishing this anywhere public

The prototype is a plain static folder, so hosting it is easy — GitHub Pages, Netlify
Drop or Vercel will all serve it as-is. Two things to clear first, neither technical:

**1. Swap the cover art.** `assets/cover.png` is the real *Very Hungry Caterpillar* cover
(Eric Carle / Penguin). Fine as internal placeholder; not something to put on a public
portfolio URL. `assets/cover-placeholder.svg` is an original stand-in drawn from the
Smoly palette. To switch, change one line in `smolify-book.html` and regenerate the flat
build:

```html
<img src="assets/cover-placeholder.svg" alt="Book cover">
```

The archived prototype under `archive/` carries its own copy of the same image — swap or
drop that too.

**2. Get the client's sign-off.** Smoly is unreleased client work. A public URL puts the
product direction, the flow and the design library on the open web, and search engines
will index it. Most client case studies run on explicit written permission, sometimes
gated until after launch. Worth asking before the link exists rather than after.

If permission is slow, the usual middle grounds are a password-protected host, a private
repo with a private Pages plan, or publishing stills and a screen recording rather than a
live prototype.

## Adding a prototype to the index

One line in `index.html`:

```html
<a class="index__item" href="your-prototype.html">Your prototype</a>
```

Archived entries use `class="index__item index__item--archived"`.
