# Migration Checklist

After running `bash setup.sh`, complete these manual steps.

## 1. Apple ID & App Store

- Sign in to App Store with your Apple ID.
- Install from App Store: Xcode, Keynote, Numbers, Pages, iMovie, GarageBand, WhatsApp.
- Sign in to iCloud in System Settings.

## 2. Secure Config Transfer (old machine → new)

> **Do this before running `setup.sh`** — Homebrew needs SSH keys to clone private/custom taps from GitHub. Without them, `brew bundle` will fail with an authentication error.

Transfer these from the old machine via AirDrop or `scp`. **Do not commit to git.**

```bash
# From old machine (adjust hostname/path as needed):
scp -r ~/.ssh/                 newmachine:~/.ssh/
scp ~/.aws/config              newmachine:~/.aws/config
scp ~/.aws/credentials         newmachine:~/.aws/credentials
scp ~/.kube/config             newmachine:~/.kube/config
scp ~/.databrickscfg           newmachine:~/.databrickscfg
scp ~/.okta_aws_login_config   newmachine:~/.okta_aws_login_config
scp ~/.okta_snowflake_login_config newmachine:~/.okta_snowflake_login_config
```

After transferring SSH keys:
```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/*
chmod 644 ~/.ssh/*.pub
```

## 3. SDKMAN

Install SDKMAN, then reinstall previous candidates. Current versions from old machine:

```bash
curl -s "https://get.sdkman.io" | bash
source "$HOME/.sdkman/bin/sdkman-init.sh"

sdk install gradle
sdk install java           # default (latest LTS) or pick specific version
sdk install sbt
sdk install scala
sdk install spark
```

Check old machine first: `sdk current` for exact version pins.

## 4. pipx Tools

```bash
pipx install gimme-aws-creds
```

## 5. Internal / Standalone CLIs

These are not in Homebrew — reinstall from internal sources:

- `infractl` — get installer from internal docs/Slack
- `gimme-snowflake-creds` — from `hginsights/tap` (already in Brewfile via `hginsights/tap/gimme-snowflake-creds`)
- `codecrafters` — from `codecrafters-io/tap` (already in Brewfile)
- Standalone `kubectl` (if you need a version different from the brew one) — grab from kubernetes.io

## 6. App Logins & Auth

- **1Password** — set up first; it unlocks other credentials.
- **Slack** — sign in to all workspaces.
- **GitHub CLI**: `gh auth login`
- **GitHub Copilot** — sign in via VSCode/Cursor.
- **Arc / Chrome** — sign in to sync bookmarks/extensions.
- **Warp** — sign in for settings sync.
- **Notion** — sign in.
- **Raycast** — sign in for cloud sync (if enabled).
- **Zed** — sign in for settings sync (if enabled).
- **Docker Desktop** — sign in.
- **Logi Options+** — sign in to restore peripheral config.
- **Obsidian** — set up vault (iCloud or manual transfer).
- **Pritunl** — add VPN profile from IT.

## 7. Ghostty Font

Ghostty config requires **MesloLGS NF** for Powerlevel10k glyphs. Install before opening Ghostty:

- Download from: https://github.com/romkatv/powerlevel10k#meslo-nerd-font-patched-for-powerlevel10k
- Install all 4 font files, then restart Ghostty.

## 8. iTerm2

Prefs are tracked in the repo (`iterm2/`). `setup.sh` points iTerm2 at that folder automatically — no manual steps needed. Just open iTerm2 after running the script.

If the color scheme doesn't carry over, manually import Monokai Soda from [iTerm2-Color-Schemes](https://github.com/mbadolato/iTerm2-Color-Schemes).

## 9. Cursor Extensions

If `cursor` CLI wasn't in PATH during `setup.sh`, install extensions manually:

```bash
# Once Cursor is open and cursor CLI is available:
xargs -L1 cursor --install-extension < ~/dotfiles/cursor/extensions.txt
```

## 10. MDM / IT-managed Apps

Wait for IT to push via JumpCloud:
- Bitdefender Endpoint Security
- JumpCloud agent
- Any company-required certificates

## 11. Verify

```bash
# Brew
brew bundle check --file=~/dotfiles/Brewfile

# Git
git config --global user.email  # should be anurag.desai@hginsights.com

# Shell
echo $ZSH_THEME  # powerlevel10k/powerlevel10k

# pyenv
pyenv versions  # should list 3.10.19

# Bun
bun --version
```
