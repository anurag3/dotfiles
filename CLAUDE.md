# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Does

Single-script macOS setup: `setup.sh` applies `defaults write` macOS preferences and installs dev tooling via Homebrew (git, pyenv, oh-my-zsh, keepingyouawake).

## Running the Setup

```bash
bash setup.sh
```

Requires sudo — script prompts for admin password upfront. Idempotent for most steps (Homebrew install check guards re-install).

## Pending Work (from README)

- Spaceship ZSH theme install (currently commented out in setup.sh)
- Oh-My-ZSH plugins: `zsh-syntax-highlighting`, `zsh-autosuggestions`, `colored-man-pages`
- Python 3 environment via pyenv

## iTerm2 Color Scheme

Monokai Soda — must be manually imported from the iTerm2-Color-Schemes repo.
