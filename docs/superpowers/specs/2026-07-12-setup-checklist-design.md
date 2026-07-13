# Interactive checklist for setup.sh section selection

## Problem

`setup.sh`'s interactive menu (`select_sections_interactively` in `setup.sh:48`) requires
typing section numbers (space-separated) to toggle them, then pressing Enter on an empty
line to run. This works but isn't a real checklist UI.

## Design

Replace the number-toggle loop with keyboard-navigated checklist:

- **State**: same `CHOSEN` associative array (all sections start checked, as today), plus a
  new `cursor` index tracking the highlighted row.
- **Rendering**: redraw the list on each keystroke. The highlighted row is prefixed with
  `>`, others with a space. Checked rows show `[x]`, unchecked `[ ]`. A footer line explains
  the key bindings.
- **Input handling**: put the terminal into raw mode (`stty -echo -icanon`) for the duration
  of the loop, restoring prior settings afterward (including on early exit via `q`). Read one
  keypress at a time with `read -rsn1`, detecting the `\x1b[A` / `\x1b[B` escape sequences for
  the up/down arrow keys.
- **Key bindings**:
  - `↑`/`k`, `↓`/`j` — move cursor up/down (wrapping is not required)
  - `space` — toggle checked state of the highlighted row
  - `a` — check all sections
  - `n` — check no sections
  - `q` — abort, `exit 0` (same behavior as today)
  - `enter` — confirm and proceed with whatever's currently checked
- Everything downstream of the loop (building the `SELECTED` array from `CHOSEN`, the
  "nothing selected" exit) is unchanged.

## Scope

Single self-contained change to the `select_sections_interactively` function in `setup.sh`.
No new files, no new dependencies, no changes to non-interactive invocation (`setup.sh
<section>...` or piped stdin still bypass this function entirely).
