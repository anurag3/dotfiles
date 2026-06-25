# LazyVim Cheat Sheet — Cursor → Nvim

**Leader key = `<Space>`** (press and wait to see which-key hints for any prefix)

---

## Navigation (Cursor's Cmd+P / sidebar)

| Cursor | nvim | Notes |
|--------|------|-------|
| `Cmd+P` (file picker) | `<leader><space>` or `<leader>sf` | Snacks picker |
| `Cmd+Shift+F` (global search) | `<leader>sg` | Live grep |
| `Cmd+Shift+E` (file explorer) | `<leader>e` | Snacks file tree |
| `Cmd+Shift+P` (command palette) | `:` + tab or `<leader>:` | Command history |
| Recent files | `<leader>fr` | — |
| Open buffers (like tabs) | `<leader>fb` | — |
| Symbols in file | `<leader>ss` | LSP symbols |
| Workspace symbols | `<leader>sS` | — |

---

## Tabs / Buffers (Cursor tabs = nvim buffers)

| Cursor | nvim | Notes |
|--------|------|-------|
| Next tab | `<Shift-l>` | — |
| Prev tab | `<Shift-h>` | — |
| Close tab | `<leader>bd` | — |
| New file | `:enew` | — |
| Switch to buffer # | `<leader>1..9` | bufferline |

---

## Code (LSP via mason + nvim-lspconfig)

| Cursor | nvim | Notes |
|--------|------|-------|
| Go to definition | `gd` | — |
| Go to references | `gr` | — |
| Go to implementation | `gI` | — |
| Hover docs | `K` | — |
| Signature help | `gK` | — |
| Rename symbol | `<leader>cr` | — |
| Code action / quick fix | `<leader>ca` | — |
| Format document | `<leader>cf` | conform.nvim |
| Inline diagnostics | `<leader>cd` | — |
| Next / prev diagnostic | `]d` / `[d` | — |
| Problems panel | `<leader>xx` | trouble.nvim |
| Buffer diagnostics | `<leader>xX` | — |

---

## Find & Replace (grug-far.nvim)

| Cursor | nvim | Notes |
|--------|------|-------|
| Find in file | `<leader>/` | — |
| Find & replace (project) | `<leader>sr` | grug-far |
| Find word under cursor | `<leader>sw` | — |

---

## Git (gitsigns + lazygit)

| Cursor | nvim | Notes |
|--------|------|-------|
| Source control panel | `<leader>gg` | Opens lazygit |
| Next / prev hunk | `]h` / `[h` | — |
| Stage hunk | `<leader>ghs` | — |
| Reset hunk | `<leader>ghr` | — |
| Blame line | `<leader>ghb` | — |
| Diff this | `<leader>ghd` | — |

---

## Terminal

| Cursor | nvim | Notes |
|--------|------|-------|
| Toggle terminal | `<Ctrl-/>` | — |
| Terminal (project root) | `<leader>ft` | — |
| Exit terminal mode | `<Esc><Esc>` | Back to normal mode |

---

## Flash.nvim (no Cursor equivalent — very powerful)

This replaces clicking to move your cursor:

- `s` in normal mode → type 2 chars of destination → jump label appears → press label to jump
- `S` → jump by treesitter node (select functions, blocks, etc.)
- Works with operators: `ys<flash>` to surround, `d<flash>` to delete to a spot

---

## Windows / Splits

| Action | nvim |
|--------|------|
| Move between splits | `<Ctrl-h/j/k/l>` |
| Split vertical | `<leader>w\|` |
| Split horizontal | `<leader>w-` |
| Close window | `<leader>wd` |
| Maximize toggle | `<leader>wm` |

---

## Comments (ts-comments.nvim)

| Action | nvim |
|--------|------|
| Toggle line comment | `gcc` |
| Toggle block comment | `gbc` |
| Comment selection | `gc` in visual |

---

## Python (venv-selector + pyright)

- `<leader>cv` — select Python virtualenv

---

## SQL (vim-dadbod)

- `<leader>Db` — DB UI browser
- `<leader>Dq` — new query
- Run query: `<leader>S` in a SQL buffer, or visual select + `<leader>S`

---

## Plugin Manager

- `<leader>l` — open Lazy (update/install plugins)
- `<leader>cm` — open Mason (install LSP servers, linters, formatters)

---

## Sessions (persistence.nvim)

- `<leader>qs` — restore session for current directory
- `<leader>ql` — restore last session

---

## Essential vim motions

Highest-ROI things to internalize coming from a GUI editor:

| Motion | Action |
|--------|--------|
| `w` / `b` | Forward / back one word |
| `0` / `$` | Start / end of line |
| `gg` / `G` | Top / bottom of file |
| `Ctrl-d` / `Ctrl-u` | Half-page down / up |
| `ci"` | Change inside quotes (works with any delimiter) |
| `yiw` | Yank (copy) word |
| `dap` | Delete paragraph |
| `v` + motion | Visual select |
| `.` | Repeat last change |
| `u` / `Ctrl-r` | Undo / redo |

---

> **Tip:** Press `<Space>` and pause — which-key shows every available command under that prefix. That's your in-editor reference.
