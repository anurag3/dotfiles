# Anurag's Dotfiles

macOS setup and maintenance for this machine: install/migrate to a new Mac, and audit/clean up brew + Cursor extensions over time.

## Quickstart

```bash
git clone <repo-url> ~/dotfiles
cd ~/dotfiles
bash setup.sh
open MIGRATION.md   # complete the manual steps
```

Running `setup.sh` with no arguments opens a mode picker:

- **Setup** — installs/configures this machine. Runs macOS defaults, Xcode CLI tools, Homebrew bootstrap, `gum`, git config, Oh My Zsh, dotfiles symlinks, and Ghostty automatically (no picker — same on every machine), then asks whether this is a **work** or **personal** machine (filters the Brewfile to that bucket + shared "common" tools) before handing off to an interactive `gum`-powered checklist for everything else (VSCode, Cursor, Rectangle, Neovim, etc.).
- **Maintain** — for a machine already set up. Reports drift between the Brewfile / `cursor/extensions.txt` and what's actually installed, then lets you pick brew formulae/casks/VSCode extensions and Cursor extensions to uninstall — removing them from the system and from the tracked file in one step.

Passing section names as args (e.g. `bash setup.sh git zsh`) skips both prompts and runs just those sections, as before.

## Brewfile Categorization

Every `tap`/`brew`/`cask`/`vscode` line in `Brewfile` is tagged `# work`, `# personal`, or `# common` (untagged lines default to common). Setup mode's Homebrew picker filters to your chosen machine type + common; Maintain mode ignores the tags and shows everything.

## What `setup.sh` Does

Sections (interactive checklist in Setup mode, or pass section names as args):

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
- Installs + copies Ghostty config
- Copies herdr config
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
├── herdr/            # herdr config (workspace/pane keybindings, etc.)
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
