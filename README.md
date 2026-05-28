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

- Applies macOS defaults (dock, keyboard, trackpad, finder, screenshots)
- Installs Homebrew + all formulae, casks, and VSCode extensions from `Brewfile`
- Configures git (name, email, LFS, autoSetupRemote)
- Installs Oh My Zsh + Powerlevel10k theme + plugins
- Copies dotfiles: `.zshrc`, `.gitconfig`, `.tmux.conf`, `.p10k.zsh`
- Copies Claude Code config (`~/.claude/`)
- Copies VSCode and Cursor settings + installs extensions
- Copies Ghostty config
- Installs pyenv Python 3.10.19
- Installs Bun

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
├── ghostty/          # Ghostty terminal config
├── iterm2/           # iTerm2 prefs (auto-synced by iTerm2 on quit)
├── vscode/           # VSCode settings + extensions list
└── cursor/           # Cursor settings + extensions list
```

## Notes

- iTerm2 color scheme: Monokai Soda (import from `MIGRATION.md` instructions)
- Sensitive configs (SSH, AWS, Kube) are NOT tracked — see `MIGRATION.md`
