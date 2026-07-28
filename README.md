# Anurag's Dotfiles

macOS setup script for migrating to a new machine.

## Quickstart

```bash
git clone <repo-url> ~/dotfiles
cd ~/dotfiles
bash setup.sh
open MIGRATION.md   # complete the manual steps
```

## What `setup.sh` Does

Runs as a set of selectable sections (interactive checklist, or pass section names as args):

- Applies macOS defaults (dock, keyboard, trackpad, finder, screenshots)
- Installs Xcode CLI tools
- Installs Homebrew + all formulae, casks, and VSCode extensions from `Brewfile`
- Configures git (name, email, LFS, autoSetupRemote)
- Installs Oh My Zsh + plugins
- Copies dotfiles: `.zshrc`, `.gitconfig`, `.tmux.conf`, `.p10k.zsh`
- Copies Claude Code config (`~/.claude/`)
- Symlinks Neovim config (`~/.config/nvim`)
- Copies VSCode settings
- Imports Rectangle settings
- Imports Vorssaint settings
- Configures Spotlight search categories
- Copies iTerm2 preferences
- Copies Ghostty config
- Copies Cursor settings + installs extensions
- Configures the Claude Code status line
- Sets Cursor as the default editor
- Installs Bun
- Symlinks Sublime Text settings (bootstraps Package Control if missing)
- Applies text replacements

## What `MIGRATION.md` Covers

Things the script can't do: App Store apps, SSH/AWS/Kube config transfer, SDKMAN, app logins, iTerm2 prefs, MDM-managed apps.

## Repo Layout

```
dotfiles/
├── setup.sh          # main setup script
├── Brewfile          # all brew formulae + casks + VSCode extensions
├── MIGRATION.md      # manual migration checklist
├── home/             # dotfiles copied to ~/
│   ├── .zshrc
│   ├── .gitconfig
│   ├── .tmux.conf
│   └── .p10k.zsh
├── claude/           # ~/.claude/ subset
├── nvim/             # Neovim (LazyVim) config
├── ghostty/          # Ghostty terminal config
├── iterm2/           # iTerm2 prefs (auto-synced by iTerm2 on quit)
├── rectangle/        # Rectangle window manager prefs
├── vorssaint/        # Vorssaint prefs
├── spotlight/        # Spotlight search category prefs
├── sublime-text/     # Sublime Text + Package Control settings
├── vscode/           # VSCode settings + extensions list
└── cursor/           # Cursor settings + extensions list
```

## Notes

- iTerm2 color scheme: Monokai Soda (import from `MIGRATION.md` instructions)
- Sensitive configs (SSH, AWS, Kube) are NOT tracked — see `MIGRATION.md`
