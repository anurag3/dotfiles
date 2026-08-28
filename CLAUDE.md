# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Does

macOS setup and maintenance script: `setup.sh` applies `defaults write` preferences and symlinks/installs config for ~20 tools (Homebrew, git, zsh, Claude Code, Neovim, VSCode, Cursor, Rectangle, iTerm2, Ghostty, and more — see `SECTION_KEYS` in `setup.sh`).

## Running the Setup

```bash
bash setup.sh              # interactive: pick Setup or Maintain mode
bash setup.sh git zsh      # or list section names to run only those
```

- **Setup mode** runs macOS defaults/Xcode/Homebrew bootstrap/git/zsh/dotfiles/Ghostty automatically, asks work vs. personal (filters `Brewfile` by its `# work`/`# personal`/`# common` tags), then offers a `gum` checklist for the rest.
- **Maintain mode** audits installed brew/Cursor items against `Brewfile`/`cursor/extensions.txt` and lets you uninstall + untrack selections.
- Sudo is only requested when the `macos` or `spotlight` sections run (or via the no-args interactive path, which always includes `macos`).
- Requires bash 4+; the script re-execs itself via Homebrew's bash if the system one is too old.

## iTerm2 Color Scheme

Monokai Soda — must be manually imported from the iTerm2-Color-Schemes repo.
