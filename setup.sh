#!/usr/bin/env bash
set -e

DOTFILES_DIR="$(cd "$(dirname "$0")" && pwd)"

# Ask for the administrator password upfront and keep the session alive
sudo -v
while true; do sudo -n true; sleep 60; kill -0 "$$" || exit; done 2>/dev/null &

###############################################################################
# macOS Defaults                                                              #
###############################################################################
echo "==> Applying macOS defaults..."

# General
sudo nvram SystemAudioVolume=" "                                                 # Disable boot sound
defaults write NSGlobalDomain NSTableViewDefaultSizeMode -int 2                  # Sidebar icon size: medium
defaults write NSGlobalDomain NSNavPanelExpandedStateForSaveMode -bool true      # Expand save panel by default
defaults write NSGlobalDomain NSNavPanelExpandedStateForSaveMode2 -bool true
defaults write NSGlobalDomain PMPrintingExpandedStateForPrint -bool true         # Expand print panel by default
defaults write NSGlobalDomain PMPrintingExpandedStateForPrint2 -bool true
defaults write NSGlobalDomain NSDocumentSaveNewDocumentsToCloud -bool false      # Save to disk, not iCloud, by default
defaults write NSGlobalDomain NSAutomaticCapitalizationEnabled -bool false       # Disable auto-capitalization (annoying when coding)
defaults write NSGlobalDomain NSAutomaticDashSubstitutionEnabled -bool false     # Disable smart dashes
defaults write NSGlobalDomain NSAutomaticPeriodSubstitutionEnabled -bool false   # Disable auto period on double-space
defaults write NSGlobalDomain NSAutomaticQuoteSubstitutionEnabled -bool false    # Disable smart quotes
defaults write NSGlobalDomain NSAutomaticSpellingCorrectionEnabled -bool false   # Disable auto-correct
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister \
    -r -domain local -domain system -domain user                                 # Remove duplicates in "Open With" menu

# Keyboard
defaults write NSGlobalDomain AppleKeyboardUIMode -int 3         # Full keyboard access (Tab works in modal dialogs)
defaults write NSGlobalDomain ApplePressAndHoldEnabled -bool false # Key repeat instead of press-and-hold accent picker
defaults write NSGlobalDomain KeyRepeat -int 1                   # Fastest key repeat rate
defaults write NSGlobalDomain InitialKeyRepeat -int 10           # Short delay before repeat starts

# Trackpad
for domain in com.apple.AppleMultitouchTrackpad com.apple.driver.AppleBluetoothMultitouch.trackpad; do
    defaults write $domain Clicking -bool true               # Tap to click
    defaults write $domain DragLock -bool false              # Drag lock off
    defaults write $domain Dragging -bool false              # Three-finger drag (handled below)
    defaults write $domain TrackpadCornerSecondaryClick -int 0  # No corner right-click
    defaults write $domain TrackpadFiveFingerPinchGesture -int 2
    defaults write $domain TrackpadFourFingerHorizSwipeGesture -int 2
    defaults write $domain TrackpadFourFingerPinchGesture -int 2
    defaults write $domain TrackpadFourFingerVertSwipeGesture -int 2
    defaults write $domain TrackpadHandResting -bool true    # Ignore accidental input while typing
    defaults write $domain TrackpadHorizScroll -bool true    # Horizontal scrolling
    defaults write $domain TrackpadMomentumScroll -bool true # Inertia scrolling
    defaults write $domain TrackpadPinch -bool true          # Pinch to zoom
    defaults write $domain TrackpadRightClick -bool true     # Two-finger right-click
    defaults write $domain TrackpadRotate -bool true         # Rotate gesture
    defaults write $domain TrackpadScroll -bool true         # Scrolling
    defaults write $domain TrackpadThreeFingerDrag -bool true           # Three-finger drag
    defaults write $domain TrackpadThreeFingerHorizSwipeGesture -int 0  # Disable three-finger swipe (using four-finger)
    defaults write $domain TrackpadThreeFingerTapGesture -int 0         # Disable three-finger tap
    defaults write $domain TrackpadThreeFingerVertSwipeGesture -int 0   # Disable three-finger vertical swipe
    defaults write $domain TrackpadTwoFingerDoubleTapGesture -int 1     # Two-finger double-tap (smart zoom)
    defaults write $domain TrackpadTwoFingerFromRightEdgeSwipeGesture -int 3  # Notification Centre swipe
    defaults write $domain USBMouseStopsTrackpad -bool false # Don't disable trackpad when mouse connected
done
defaults write com.apple.dock showAppExposeGestureEnabled -bool true  # Four-finger swipe down for App Exposé
defaults write NSGlobalDomain com.apple.mouse.tapBehavior -int 1        # Apply tap-to-click for current user

# Screenshots
mkdir -p ~/Documents/Screenshots
defaults write com.apple.screencapture type -string "png"                                # Save screenshots as PNG
defaults write com.apple.screencapture location -string "$HOME/Documents/Screenshots"   # Save to ~/Documents/Screenshots
killall SystemUIServer 2>/dev/null || true                                               # Restart SystemUIServer to apply screenshot location

# Finder
defaults write NSGlobalDomain AppleShowAllExtensions -bool true          # Always show file extensions
defaults write com.apple.finder NewWindowTarget -string "PfHm"          # New windows open to home directory
defaults write com.apple.finder NewWindowTargetPath -string "file://$HOME/" # Home directory path
defaults write com.apple.finder ShowPathbar -bool true                   # Show path bar at bottom
defaults write com.apple.finder ShowStatusBar -bool false                # Hide status bar
defaults write com.apple.finder ShowSidebar -bool true                   # Show sidebar
defaults write com.apple.finder SidebarWidth -int 196                   # Sidebar width
defaults write com.apple.finder FXPreferredViewStyle -string "Nlsv"     # Default to list view
defaults write com.apple.finder FXArrangeGroupViewBy -string "Name"     # Group by name
defaults write com.apple.finder _FXSortFoldersFirst -bool true           # Folders on top when sorting
defaults write com.apple.finder _FXShowPosixPathInTitle -bool false     # Don't show full path in title bar
defaults write com.apple.finder ShowExternalHardDrivesOnDesktop -bool true  # Show external drives on desktop
defaults write com.apple.finder ShowHardDrivesOnDesktop -bool false     # Hide internal drives on desktop
defaults write com.apple.finder ShowRemovableMediaOnDesktop -bool true  # Show removable media on desktop
killall Finder 2>/dev/null || true

# Dock
defaults write com.apple.dock tilesize -int 36                           # Icon size: 36px
defaults write com.apple.dock mineffect -string "scale"                  # Scale effect for minimize (faster than genie)
defaults write com.apple.dock minimize-to-application -bool true         # Minimize windows into their app icon
defaults write com.apple.dock show-process-indicators -bool true         # Show dot indicators for open apps
defaults write com.apple.dock autohide-delay -float 0                   # No delay before dock hides
defaults write com.apple.dock autohide-time-modifier -float 0           # Instant hide/show animation
defaults write com.apple.dock autohide -bool true                        # Auto-hide the dock
defaults write com.apple.dock showhidden -bool true                      # Make hidden app icons translucent
defaults write com.apple.dock show-recents -bool false                   # Don't show recent apps in dock
defaults write com.apple.dock magnification -bool true                   # Enable dock magnification on hover
defaults write com.apple.dock mru-spaces -bool false                     # Don't rearrange Spaces based on recent use
defaults write com.apple.dock expose-group-apps -bool false              # Mission Control: don't group windows by app
dockutil --add ~/Downloads --view auto --display folder --sort dateadded --replacing Downloads 2>/dev/null || true
killall Dock 2>/dev/null || true

# Activity Monitor
defaults write com.apple.ActivityMonitor OpenMainWindow -bool true       # Open main window on launch
defaults write com.apple.ActivityMonitor IconType -int 5                 # Show CPU usage graph in dock icon
defaults write com.apple.ActivityMonitor ShowCategory -int 0             # Show all processes (not just user's)
defaults write com.apple.ActivityMonitor SortColumn -string "CPUUsage"  # Sort by CPU usage
defaults write com.apple.ActivityMonitor SortDirection -int 0            # Descending (highest CPU first)

###############################################################################
# Xcode CLI Tools                                                             #
###############################################################################
echo "==> Installing Xcode CLI tools..."
xcode-select --install 2>/dev/null || true

###############################################################################
# Homebrew                                                                    #
###############################################################################
echo "==> Installing Homebrew..."
if ! command -v brew &>/dev/null; then
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    # Apple Silicon: add brew to PATH for remainder of script
    eval "$(/opt/homebrew/bin/brew shellenv)"
fi

echo "==> Running brew bundle..."
brew bundle --file="$DOTFILES_DIR/Brewfile"
brew cleanup

###############################################################################
# Git Config                                                                  #
###############################################################################
echo "==> Configuring git..."
git config --global user.name "Anurag Desai"
git config --global user.email "anurag.desai@hginsights.com"
git config --global push.autoSetupRemote true
git config --global url."git@github.com:".insteadOf "https://github.com/"  # Force SSH for GitHub (avoids HTTPS auth prompts for brew taps)
git lfs install

###############################################################################
# Oh My Zsh + Plugins                                                         #
###############################################################################
echo "==> Installing Oh My Zsh..."
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
fi

ZSH_CUSTOM="${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}"

echo "==> Installing Powerlevel10k theme..."
[ -d "$ZSH_CUSTOM/themes/powerlevel10k" ] || \
    git clone --depth=1 https://github.com/romkatv/powerlevel10k.git "$ZSH_CUSTOM/themes/powerlevel10k"

echo "==> Installing zsh plugins..."
[ -d "$ZSH_CUSTOM/plugins/zsh-autosuggestions" ] || \
    git clone https://github.com/zsh-users/zsh-autosuggestions "$ZSH_CUSTOM/plugins/zsh-autosuggestions"
[ -d "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting" ] || \
    git clone https://github.com/zsh-users/zsh-syntax-highlighting.git "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting"

###############################################################################
# Dotfiles                                                                    #
###############################################################################
echo "==> Symlinking dotfiles..."
ln -sf "$DOTFILES_DIR/home/.zshrc"     "$HOME/.zshrc"
ln -sf "$DOTFILES_DIR/home/.gitconfig" "$HOME/.gitconfig"
ln -sf "$DOTFILES_DIR/home/.tmux.conf" "$HOME/.tmux.conf"
ln -sf "$DOTFILES_DIR/home/.p10k.zsh"  "$HOME/.p10k.zsh"

mkdir -p "$HOME/.local/bin"
ln -sf "$DOTFILES_DIR/home/.local/bin/claude-workspace" "$HOME/.local/bin/claude-workspace"

###############################################################################
# Claude Code Config                                                          #
###############################################################################
echo "==> Symlinking Claude config..."
mkdir -p "$HOME/.claude"
ln -sf "$DOTFILES_DIR/claude/CLAUDE.md"             "$HOME/.claude/CLAUDE.md"
ln -sf "$DOTFILES_DIR/claude/RTK.md"                "$HOME/.claude/RTK.md"
ln -sf "$DOTFILES_DIR/claude/settings.json"         "$HOME/.claude/settings.json"
ln -sf "$DOTFILES_DIR/claude/statusline-command.sh" "$HOME/.claude/statusline-command.sh"
[ -d "$DOTFILES_DIR/claude/hooks" ] && \
    rm -rf "$HOME/.claude/hooks" && \
    ln -sf "$DOTFILES_DIR/claude/hooks"   "$HOME/.claude/hooks"
[ -d "$DOTFILES_DIR/claude/skills" ] && \
    rm -rf "$HOME/.claude/skills" && \
    ln -sf "$DOTFILES_DIR/claude/skills"  "$HOME/.claude/skills"

###############################################################################
# Neovim Config                                                               #
###############################################################################
echo "==> Symlinking Neovim config..."
mkdir -p "$HOME/.config"
rm -rf "$HOME/.config/nvim"
ln -sf "$DOTFILES_DIR/nvim" "$HOME/.config/nvim"

###############################################################################
# VSCode Settings                                                             #
###############################################################################
echo "==> Symlinking VSCode settings..."
VSCODE_USER="$HOME/Library/Application Support/Code/User"
mkdir -p "$VSCODE_USER"
ln -sf "$DOTFILES_DIR/vscode/settings.json"    "$VSCODE_USER/settings.json"
[ -f "$DOTFILES_DIR/vscode/keybindings.json" ] && \
    ln -sf "$DOTFILES_DIR/vscode/keybindings.json" "$VSCODE_USER/keybindings.json"
[ -d "$DOTFILES_DIR/vscode/snippets" ] && \
    ln -sf "$DOTFILES_DIR/vscode/snippets" "$VSCODE_USER/snippets"

###############################################################################
# Rectangle                                                                   #
###############################################################################
echo "==> Importing Rectangle settings..."
defaults import com.knollsoft.Rectangle "$DOTFILES_DIR/rectangle/com.knollsoft.Rectangle.plist"

###############################################################################
# Vorssaint                                                                   #
###############################################################################
echo "==> Importing Vorssaint settings..."
defaults import com.vorssaint.utils "$DOTFILES_DIR/vorssaint/com.vorssaint.utils.plist"

###############################################################################
# Spotlight                                                                   #
###############################################################################
# To reset Spotlight to defaults: defaults delete com.apple.Spotlight orderedItems && sudo killall mds
echo "==> Setting Spotlight search categories..."
defaults write com.apple.Spotlight orderedItems -array \
  '{ enabled = 1; name = APPLICATIONS; }' \
  '{ enabled = 1; name = "MENU_EXPRESSION"; }' \
  '{ enabled = 0; name = CONTACT; }' \
  '{ enabled = 0; name = "MENU_CONVERSION"; }' \
  '{ enabled = 1; name = "MENU_DEFINITION"; }' \
  '{ enabled = 0; name = SOURCE; }' \
  '{ enabled = 0; name = DOCUMENTS; }' \
  '{ enabled = 0; name = "EVENT_TODO"; }' \
  '{ enabled = 0; name = DIRECTORIES; }' \
  '{ enabled = 0; name = FONTS; }' \
  '{ enabled = 0; name = IMAGES; }' \
  '{ enabled = 0; name = MESSAGES; }' \
  '{ enabled = 0; name = MOVIES; }' \
  '{ enabled = 0; name = MUSIC; }' \
  '{ enabled = 0; name = "MENU_OTHER"; }' \
  '{ enabled = 0; name = PDF; }' \
  '{ enabled = 0; name = PRESENTATIONS; }' \
  '{ enabled = 0; name = "MENU_SPOTLIGHT_SUGGESTIONS"; }' \
  '{ enabled = 0; name = SPREADSHEETS; }' \
  '{ enabled = 1; name = "SYSTEM_PREFS"; }' \
  '{ enabled = 0; name = TIPS; }' \
  '{ enabled = 0; name = BOOKMARKS; }'
sudo killall mds 2>/dev/null || true
killall Spotlight 2>/dev/null || true

###############################################################################
# iTerm2 Prefs                                                                #
###############################################################################
echo "==> Configuring iTerm2 preferences..."
defaults write com.googlecode.iterm2 PrefsCustomFolder -string "$DOTFILES_DIR/iterm2"
defaults write com.googlecode.iterm2 LoadPrefsFromCustomFolder -bool true
# iTerm2 already writes directly to the PrefsCustomFolder — no symlink needed

###############################################################################
# Ghostty Config                                                              #
###############################################################################
echo "==> Symlinking Ghostty config..."
GHOSTTY_DIR="$HOME/Library/Application Support/com.mitchellh.ghostty"
mkdir -p "$GHOSTTY_DIR"
ln -sf "$DOTFILES_DIR/ghostty/config.ghostty" "$GHOSTTY_DIR/config.ghostty"

###############################################################################
# Cursor Settings                                                             #
###############################################################################
echo "==> Symlinking Cursor settings..."
CURSOR_USER="$HOME/Library/Application Support/Cursor/User"
mkdir -p "$CURSOR_USER"
ln -sf "$DOTFILES_DIR/cursor/settings.json"    "$CURSOR_USER/settings.json"
[ -f "$DOTFILES_DIR/cursor/keybindings.json" ] && \
    ln -sf "$DOTFILES_DIR/cursor/keybindings.json" "$CURSOR_USER/keybindings.json"
[ -d "$DOTFILES_DIR/cursor/snippets" ] && \
    ln -sf "$DOTFILES_DIR/cursor/snippets" "$CURSOR_USER/snippets"

echo "==> Installing Cursor extensions..."
if command -v cursor &>/dev/null; then
    xargs -L1 cursor --install-extension < "$DOTFILES_DIR/cursor/extensions.txt"
else
    echo "    Cursor CLI not found — install extensions manually or re-run after opening Cursor once."
fi

###############################################################################
# Claude Code Status Line                                                     #
###############################################################################
echo "==> Configuring Claude Code status line..."
CLAUDE_SETTINGS="$HOME/.claude/settings.json"
mkdir -p "$HOME/.claude"
if [ -f "$CLAUDE_SETTINGS" ]; then
    python3 -c "
import json
with open('$CLAUDE_SETTINGS') as f:
    s = json.load(f)
s['statusLine'] = {'type': 'command', 'command': 'bunx -y ccstatusline@latest', 'padding': 0, 'refreshInterval': 1}
with open('$CLAUDE_SETTINGS', 'w') as f:
    json.dump(s, f, indent=2)
"
else
    echo '{"statusLine":{"type":"command","command":"bunx -y ccstatusline@latest","padding":0,"refreshInterval":1}}' > "$CLAUDE_SETTINGS"
fi

###############################################################################
# Default Editor (Cursor)                                                     #
###############################################################################
echo "==> Setting Cursor as default text editor..."
CURSOR_BUNDLE_ID=$(osascript -e 'id of app "Cursor"' 2>/dev/null)
if [ -z "$CURSOR_BUNDLE_ID" ]; then
    echo "    Cursor not found — skipping default editor setup. Re-run after installing Cursor."
else
    duti -s "$CURSOR_BUNDLE_ID" public.plain-text all      # Plain text files
    duti -s "$CURSOR_BUNDLE_ID" public.text all            # All text UTIs
    duti -s "$CURSOR_BUNDLE_ID" public.source-code all     # All source code UTIs
    duti -s "$CURSOR_BUNDLE_ID" public.shell-script all    # Shell scripts
    duti -s "$CURSOR_BUNDLE_ID" public.json all            # JSON files
    duti -s "$CURSOR_BUNDLE_ID" public.xml all             # XML files
    duti -s "$CURSOR_BUNDLE_ID" public.yaml all            # YAML files
fi

###############################################################################
# Bun                                                                         #
###############################################################################
echo "==> Installing Bun..."
[ -d "$HOME/.bun" ] || curl -fsSL https://bun.sh/install | bash

###############################################################################
# Sublime Text Settings                                                       #
###############################################################################
echo "==> Symlinking Sublime Text settings..."
ST_USER="$HOME/Library/Application Support/Sublime Text/Packages/User"
if [ -d "$ST_USER" ]; then
    ln -sf "$DOTFILES_DIR/sublime-text/Preferences.sublime-settings" "$ST_USER/Preferences.sublime-settings"
    ln -sf "$DOTFILES_DIR/sublime-text/Package Control.sublime-settings" "$ST_USER/Package Control.sublime-settings"
    echo "    Symlinks created. Packages auto-install on next ST launch."
else
    echo "    Sublime Text not found — open it once to create the User dir, then re-run."
fi

###############################################################################
# Text Replacements                                                           #
###############################################################################
echo "==> Setting text replacements..."
defaults write -g NSUserReplacementItems -array \
  '{ replace = "->"; with = "\U2192"; }' \
  '{ replace = "@g"; with = "aadesai92@gmail.com"; }' \
  '{ replace = "@git"; with = "https://github.com/anurag3"; }' \
  '{ replace = "@h"; with = "anurag.desai@hginsights.com"; }' \
  '{ replace = "@link"; with = "https://www.linkedin.com/in/anuragdesai/"; }' \
  '{ replace = "@o"; with = "anurag.desai@outlook.com"; }' \
  '{ replace = "@w"; with = "adesai@wpi.edu"; }' \
  '{ replace = "omw"; with = "On my way!"; }' \
  '{ replace = "tix"; with = "ticket"; }' \
  '{ replace = "tixs"; with = "tickets"; }' \
  '{ replace = "txn"; with = "transaction"; }' \
  '{ replace = "txns"; with = "transactions"; }'

echo ""
echo "✓ Setup complete."
echo "  Next: open MIGRATION.md and work through the manual steps."
