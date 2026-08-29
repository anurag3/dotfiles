#!/usr/bin/env bash
set -e

if [ "${BASH_VERSINFO:-0}" -lt 4 ]; then
    for candidate in /opt/homebrew/bin/bash /usr/local/bin/bash; do
        if [ -x "$candidate" ]; then
            exec "$candidate" "$0" "$@"
        fi
    done
    echo "setup.sh needs bash 4+ (found ${BASH_VERSION:-unknown}). macOS's built-in bash is too old — run 'brew install bash' first, then re-run this script." >&2
    exit 1
fi

DOTFILES_DIR="$(cd "$(dirname "$0")" && pwd)"

# Ordered list of section keys, used for selection, help text, and execution order.
SECTION_KEYS=(macos xcode brew git zsh dotfiles claude nvim vscode rectangle vorssaint spotlight iterm2 ghostty herdr cursor statusline editor bun sublime textreplace)

declare -A SECTION_DESC=(
    [macos]="macOS defaults (keyboard, trackpad, Finder, Dock, etc.)"
    [xcode]="Xcode CLI tools"
    [brew]="Homebrew + Brewfile bundle"
    [git]="Git config"
    [zsh]="Oh My Zsh + plugins"
    [dotfiles]="Dotfiles symlinks (.zshrc, .gitconfig, etc.)"
    [claude]="Claude Code config symlinks"
    [nvim]="Neovim config symlink"
    [vscode]="VSCode settings"
    [rectangle]="Rectangle settings import"
    [vorssaint]="Vorssaint settings import"
    [spotlight]="Spotlight search categories"
    [iterm2]="iTerm2 preferences"
    [ghostty]="Ghostty config"
    [herdr]="herdr config"
    [cursor]="Cursor settings + extensions"
    [statusline]="Claude Code status line"
    [editor]="Default editor (Cursor on work, VSCode on personal)"
    [bun]="Bun install"
    [sublime]="Sublime Text settings"
    [textreplace]="Text replacements"
)

# Sections that always run automatically in Setup mode, before gum is
# available — these have no work/personal split and no picker.
BASICS_KEYS=(macos xcode git zsh dotfiles ghostty)

# Everything else, picked interactively once gum (or the tput fallback) is
# ready. Order preserved from SECTION_KEYS.
INTERACTIVE_KEYS=()
for key in "${SECTION_KEYS[@]}"; do
    is_basic=0
    for b in "${BASICS_KEYS[@]}"; do [ "$key" = "$b" ] && { is_basic=1; break; }; done
    [ "$is_basic" -eq 0 ] && INTERACTIVE_KEYS+=("$key")
done

have_gum() { command -v gum &>/dev/null; }

usage() {
    echo "Usage: $0 [section...]"
    echo
    echo "Run with no arguments for an interactive Setup/Maintain mode picker."
    echo "Setup mode runs macos/xcode/brew-bootstrap/git/zsh/dotfiles/ghostty"
    echo "automatically, asks work vs. personal, then lets you pick the rest."
    echo "Maintain mode audits installed brew/Cursor items against Brewfile and"
    echo "cursor/extensions.txt, and lets you sync untracked installs in and"
    echo "uninstall + untrack selections out."
    echo
    echo "Or list one or more section names to run only those, skipping both"
    echo "the mode picker and the machine-type prompt:"
    echo
    for key in "${SECTION_KEYS[@]}"; do
        printf "  %-12s %s\n" "$key" "${SECTION_DESC[$key]}"
    done
}

if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    usage
    exit 0
fi

# select_checklist <title> <output_array_name> <all|none> <key1> <desc1> [<key2> <desc2> ...]
# Interactive checkbox picker (↑/k ↓/j move, space toggle, a/n all/none,
# enter confirm, q abort-whole-script). <all|none> sets the starting state
# of every key — "none" for destructive/removal pickers so nothing is
# selected by accident. Writes the chosen keys, in input order, into the
# array named by <output_array_name>. An empty result is valid — the caller
# decides what that means. Uses gum for the UI when installed, otherwise
# falls back to a hand-rolled tput picker.
select_checklist() {
    local title="$1" out_name="$2" default_state="$3"
    shift 3
    local -n out_ref="$out_name"
    local -a keys=()
    local -A desc=()
    while [ "$#" -gt 0 ]; do
        keys+=("$1")
        desc["$1"]="$2"
        shift 2
    done

    if [ "${#keys[@]}" -eq 0 ]; then
        out_ref=()
        return 0
    fi

    if have_gum; then
        local -a labels=() chosen_labels=()
        local -A chosen_set=()
        local key label sel_default
        for key in "${keys[@]}"; do
            if [ -n "${desc[$key]}" ]; then
                labels+=("$key  —  ${desc[$key]}")
            else
                labels+=("$key")
            fi
        done
        if [ "$default_state" = "all" ]; then
            sel_default=$(printf '%s\x1f' "${labels[@]}")
            sel_default="${sel_default%$'\x1f'}"
            mapfile -t chosen_labels < <(gum choose --no-limit --header="$title" \
                --selected="$sel_default" --selected-delimiter=$'\x1f' "${labels[@]}")
        else
            mapfile -t chosen_labels < <(gum choose --no-limit --header="$title" "${labels[@]}")
        fi
        for label in "${chosen_labels[@]}"; do chosen_set["$label"]=1; done
        out_ref=()
        local i=0
        for key in "${keys[@]}"; do
            [ -n "${chosen_set[${labels[$i]}]:-}" ] && out_ref+=("$key")
            i=$((i + 1))
        done
        return 0
    fi

    local -A chosen
    local key cursor=0 key_count="${#keys[@]}"
    local initial=1
    [ "$default_state" = "none" ] && initial=0
    for key in "${keys[@]}"; do chosen[$key]=$initial; done

    local old_stty
    old_stty=$(stty -g)
    stty -echo -icanon
    trap 'stty "$old_stty"' EXIT

    while true; do
        clear
        echo "$title"
        echo

        local term_height
        term_height=$(tput lines 2>/dev/null) || term_height=24
        local visible_rows=$((term_height - 4))  # title (2 lines) + footer (2 lines)
        [ "$visible_rows" -lt 1 ] && visible_rows=1

        local scroll_offset=0 visible_end="$key_count"
        if [ "$key_count" -gt "$visible_rows" ]; then
            # Center the window on the cursor, clamped to the list bounds.
            scroll_offset=$((cursor - visible_rows / 2))
            [ "$scroll_offset" -lt 0 ] && scroll_offset=0
            local max_offset=$((key_count - visible_rows))
            [ "$scroll_offset" -gt "$max_offset" ] && scroll_offset=$max_offset
            visible_end=$((scroll_offset + visible_rows))
        fi

        local i
        for ((i = scroll_offset; i < visible_end; i++)); do
            key="${keys[$i]}"
            local mark=" " pointer=" "
            [ "${chosen[$key]}" = "1" ] && mark="x"
            [ "$i" -eq "$cursor" ] && pointer=">"
            printf "%s [%s] %-12s %s\n" "$pointer" "$mark" "$key" "${desc[$key]}"
        done
        echo
        echo "↑/k ↓/j move   space toggle   a all   n none   q quit   enter confirm"

        local keypress rest
        IFS= read -rsn1 keypress
        if [ "$keypress" = $'\x1b' ]; then
            IFS= read -rsn2 -t 0.05 rest || true
            keypress+="$rest"
        fi

        case "$keypress" in
            $'\x1b[A'|k|K) [ "$cursor" -gt 0 ] && cursor=$((cursor - 1)) ;;
            $'\x1b[B'|j|J) [ "$cursor" -lt $((key_count - 1)) ] && cursor=$((cursor + 1)) ;;
            ' ')
                key="${keys[$cursor]}"
                [ "${chosen[$key]}" = "1" ] && chosen[$key]=0 || chosen[$key]=1
                ;;
            a|A) for key in "${keys[@]}"; do chosen[$key]=1; done ;;
            n|N) for key in "${keys[@]}"; do chosen[$key]=0; done ;;
            q|Q)
                echo "Aborted."
                exit 0
                ;;
            "") break ;;
        esac
    done

    stty "$old_stty"
    trap - EXIT

    out_ref=()
    for key in "${keys[@]}"; do
        [ "${chosen[$key]}" = "1" ] && out_ref+=("$key")
    done
    return 0
}

# select_single <title> <output_var_name> <key1> <desc1> [<key2> <desc2> ...]
# Single-choice picker (↑/k ↓/j move, enter confirm, q abort-whole-script).
# Writes the chosen key into the scalar named by <output_var_name>. Uses gum
# when installed, otherwise falls back to a hand-rolled tput picker.
select_single() {
    local title="$1" out_name="$2"
    shift 2
    local -n out_ref="$out_name"
    local -a keys=()
    local -A desc=()
    while [ "$#" -gt 0 ]; do
        keys+=("$1")
        desc["$1"]="$2"
        shift 2
    done

    local -a labels=()
    local key
    for key in "${keys[@]}"; do
        if [ -n "${desc[$key]}" ]; then
            labels+=("$key  —  ${desc[$key]}")
        else
            labels+=("$key")
        fi
    done

    if have_gum; then
        local chosen_label
        chosen_label=$(gum choose --header="$title" "${labels[@]}")
        local i=0
        for key in "${keys[@]}"; do
            [ "${labels[$i]}" = "$chosen_label" ] && { out_ref="$key"; return 0; }
            i=$((i + 1))
        done
        return 0
    fi

    local old_stty
    old_stty=$(stty -g)
    stty -echo -icanon
    trap 'stty "$old_stty"' EXIT

    local cursor=0 key_count="${#keys[@]}"
    while true; do
        clear
        echo "$title"
        echo

        local i pointer
        for ((i = 0; i < key_count; i++)); do
            pointer=" "
            [ "$i" -eq "$cursor" ] && pointer=">"
            printf "%s %s\n" "$pointer" "${labels[$i]}"
        done
        echo
        echo "↑/k ↓/j move   q quit   enter confirm"

        local keypress rest
        IFS= read -rsn1 keypress
        if [ "$keypress" = $'\x1b' ]; then
            IFS= read -rsn2 -t 0.05 rest || true
            keypress+="$rest"
        fi

        case "$keypress" in
            $'\x1b[A'|k|K) [ "$cursor" -gt 0 ] && cursor=$((cursor - 1)) ;;
            $'\x1b[B'|j|J) [ "$cursor" -lt $((key_count - 1)) ] && cursor=$((cursor + 1)) ;;
            q|Q)
                echo "Aborted."
                exit 0
                ;;
            "") break ;;
        esac
    done

    stty "$old_stty"
    trap - EXIT

    out_ref="${keys[$cursor]}"
}

select_sections_interactively() {
    local args=() key
    for key in "${INTERACTIVE_KEYS[@]}"; do
        args+=("$key" "${SECTION_DESC[$key]}")
    done

    select_checklist "Dotfiles Setup — select additional sections to run" SELECTED all "${args[@]}"

    if [ "${#SELECTED[@]}" -eq 0 ]; then
        echo "No additional sections selected."
    fi
}

if [ "$#" -eq 0 ]; then
    if [ -t 0 ]; then
        select_single "Dotfiles — choose mode" MODE \
            setup    "Set up this machine (install/configure)" \
            maintain "Maintain this machine (audit/remove brew + Cursor extensions)"
        if [ "$MODE" = "setup" ]; then
            select_single "Dotfiles Setup — machine type" MACHINE_TYPE \
                work     "Work machine (work + common tools)" \
                personal "Personal machine (personal + common tools)"
        fi
    else
        MODE="setup"
        SELECTED=("${SECTION_KEYS[@]}")
    fi
else
    MODE="setup"
    SELECTED=("$@")
    for key in "${SELECTED[@]}"; do
        if [ -z "${SECTION_DESC[$key]:-}" ]; then
            echo "Unknown section: $key" >&2
            echo >&2
            usage >&2
            exit 1
        fi
    done
fi

is_selected() {
    local key="$1"
    for s in "${SELECTED[@]}"; do
        [ "$s" = "$key" ] && return 0
    done
    return 1
}

###############################################################################
# macOS Defaults                                                              #
###############################################################################
section_macos() {
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
defaults write NSGlobalDomain InitialKeyRepeat -int 10           # Shortest delay before repeat starts

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
defaults write com.apple.dock launchanim -bool false                     # Disable app launch bounce animation
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
defaults write com.apple.dock enterMissionControlByTopWindowDrag -bool false  # Don't enter Mission Control by dragging window to top
dockutil --add ~/Downloads --view auto --display folder --sort dateadded --replacing Downloads 2>/dev/null || true
killall Dock 2>/dev/null || true

# Activity Monitor
defaults write com.apple.ActivityMonitor OpenMainWindow -bool true       # Open main window on launch
defaults write com.apple.ActivityMonitor IconType -int 5                 # Show CPU usage graph in dock icon
defaults write com.apple.ActivityMonitor ShowCategory -int 0             # Show all processes (not just user's)
defaults write com.apple.ActivityMonitor SortColumn -string "CPUUsage"  # Sort by CPU usage
defaults write com.apple.ActivityMonitor SortDirection -int 0            # Descending (highest CPU first)
}

###############################################################################
# Xcode CLI Tools                                                             #
###############################################################################
section_xcode() {
echo "==> Installing Xcode CLI tools..."
xcode-select --install 2>/dev/null || true
}

###############################################################################
# Homebrew                                                                    #
###############################################################################

# Parses $DOTFILES_DIR/Brewfile into:
#   BREW_TAP_LINES      - raw `tap ...` lines (always installed, never selectable)
#   BREW_CATEGORIES     - ordered category names (from `# comment` headers), skipping empty ones
#   BREW_CATEGORY_LINES - category name -> newline-joined raw `brew`/`cask`/`vscode` lines
parse_brewfile() {
    BREW_TAP_LINES=()
    BREW_CATEGORIES=()
    declare -gA BREW_CATEGORY_LINES=()

    local line current_cat=""
    while IFS= read -r line || [ -n "$line" ]; do
        case "$line" in
            "#"*)
                local hdr="${line#"# "}"
                case "$hdr" in
                    -------*) continue ;;
                esac
                current_cat="$hdr"
                ;;
            "tap "*)
                BREW_TAP_LINES+=("$line")
                ;;
            "brew "*|"cask "*|"vscode "*)
                if [ -z "${BREW_CATEGORY_LINES[$current_cat]:-}" ]; then
                    BREW_CATEGORIES+=("$current_cat")
                fi
                BREW_CATEGORY_LINES[$current_cat]+="$line"$'\n'
                ;;
        esac
    done < "$DOTFILES_DIR/Brewfile"
}

# brew_category_items <category> <out_array_name>
# Splits a category's newline-joined lines into a clean array (via nameref).
brew_category_items() {
    local -n _items_out="$2"
    mapfile -t _items_out <<< "${BREW_CATEGORY_LINES[$1]}"
    local _bci_filtered=() _bci_it
    for _bci_it in "${_items_out[@]}"; do [ -n "$_bci_it" ] && _bci_filtered+=("$_bci_it"); done
    _items_out=("${_bci_filtered[@]}")
}

# brewfile_line_bucket <raw_brewfile_line>
# Reads the trailing "# work|personal|common" tag off a tap/brew/cask/vscode
# line; untagged lines default to common.
brewfile_line_bucket() {
    local line="$1"
    if [[ "$line" =~ \#[[:space:]]*(work|personal|common)[[:space:]]*$ ]]; then
        echo "${BASH_REMATCH[1]}"
    else
        echo "common"
    fi
}

ensure_homebrew() {
if ! command -v brew &>/dev/null; then
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    # Apple Silicon: add brew to PATH for remainder of script
    eval "$(/opt/homebrew/bin/brew shellenv)"
fi
}

# select_brew_items [machine_type]
# Interactive category + per-category item picker, offered items limited to
# [machine_type] + common (an empty machine_type means no filtering — every
# tap/brew/cask/vscode entry is offered, matching direct `setup.sh brew`
# invocations that bypass the machine-type prompt). Writes the chosen
# tap + brew/cask/vscode lines to a temp Brewfile and sets
# BREW_FILTERED_FILE to its path.
select_brew_items() {
    local machine_type="${1:-}"
    parse_brewfile

    local -a filtered_taps=()
    local tline bucket
    for tline in "${BREW_TAP_LINES[@]}"; do
        bucket=$(brewfile_line_bucket "$tline")
        if [ -z "$machine_type" ] || [ "$bucket" = "$machine_type" ] || [ "$bucket" = "common" ]; then
            filtered_taps+=("$tline")
        fi
    done
    BREW_TAP_LINES=("${filtered_taps[@]}")

    local cat_args=() cat items
    for cat in "${BREW_CATEGORIES[@]}"; do
        brew_category_items "$cat" items
        local -a cat_items=() it
        for it in "${items[@]}"; do
            bucket=$(brewfile_line_bucket "$it")
            if [ -z "$machine_type" ] || [ "$bucket" = "$machine_type" ] || [ "$bucket" = "common" ]; then
                cat_items+=("$it")
            fi
        done
        [ "${#cat_items[@]}" -eq 0 ] && continue
        BREW_CATEGORY_LINES[$cat]=$(printf '%s\n' "${cat_items[@]}")
        cat_args+=("$cat" "(${#cat_items[@]} items)")
    done

    local chosen_categories
    select_checklist "Homebrew — select categories to install" chosen_categories all "${cat_args[@]}"

    local selected_lines=() chosen_items item_args it
    for cat in "${chosen_categories[@]}"; do
        brew_category_items "$cat" items
        item_args=()
        for it in "${items[@]}"; do item_args+=("$it" ""); done
        select_checklist "Homebrew — $cat" chosen_items all "${item_args[@]}"
        selected_lines+=("${chosen_items[@]}")
    done

    BREW_FILTERED_FILE=$(mktemp)
    # Set the EXIT trap here, after both select_checklist calls above: each of
    # those ends with its own unconditional `trap - EXIT`, so no earlier trap
    # is pending to be clobbered, and nothing below touches the EXIT trap again.
    trap 'rm -f "$BREW_FILTERED_FILE"' EXIT
    printf '%s\n' "${BREW_TAP_LINES[@]}" "${selected_lines[@]}" > "$BREW_FILTERED_FILE"
}

section_brew() {
echo "==> Installing Homebrew..."
ensure_homebrew

local brewfile="$DOTFILES_DIR/Brewfile"
if [ -t 0 ]; then
    select_brew_items "${MACHINE_TYPE:-}"
    brewfile="$BREW_FILTERED_FILE"
else
    parse_brewfile
fi

echo "==> Trusting non-official taps..."
local tap_names=() tline
for tline in "${BREW_TAP_LINES[@]}"; do
    [[ "$tline" =~ ^tap[[:space:]]+\"([^\"]+)\" ]] && tap_names+=("${BASH_REMATCH[1]}")
done
[ "${#tap_names[@]}" -gt 0 ] && brew trust --tap "${tap_names[@]}"

echo "==> Running brew bundle..."
brew bundle --file="$brewfile"
brew cleanup
}

###############################################################################
# Git Config                                                                  #
###############################################################################
section_git() {
echo "==> Configuring git..."
git config --global user.name "Anurag Desai"
git config --global user.email "anurag.desai@hginsights.com"
git config --global push.autoSetupRemote true
git config --global url."git@github.com:".insteadOf "https://github.com/"  # Force SSH for GitHub (avoids HTTPS auth prompts for brew taps)
git lfs install
}

###############################################################################
# Oh My Zsh + Plugins                                                         #
###############################################################################
section_zsh() {
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
}

###############################################################################
# Dotfiles                                                                    #
###############################################################################
section_dotfiles() {
echo "==> Symlinking dotfiles..."
ln -sf "$DOTFILES_DIR/home/.zshrc"     "$HOME/.zshrc"
ln -sf "$DOTFILES_DIR/home/.gitconfig" "$HOME/.gitconfig"
ln -sf "$DOTFILES_DIR/home/.tmux.conf" "$HOME/.tmux.conf"
ln -sf "$DOTFILES_DIR/home/.p10k.zsh"  "$HOME/.p10k.zsh"

mkdir -p "$HOME/.local/bin"
ln -sf "$DOTFILES_DIR/home/.local/bin/claude-workspace" "$HOME/.local/bin/claude-workspace"
}

###############################################################################
# Claude Code Config                                                          #
###############################################################################
section_claude() {
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
}

###############################################################################
# Neovim Config                                                               #
###############################################################################
section_nvim() {
echo "==> Symlinking Neovim config..."
mkdir -p "$HOME/.config"
rm -rf "$HOME/.config/nvim"
ln -sf "$DOTFILES_DIR/nvim" "$HOME/.config/nvim"
}

###############################################################################
# VSCode Settings                                                             #
###############################################################################
section_vscode() {
echo "==> Symlinking VSCode settings..."
VSCODE_USER="$HOME/Library/Application Support/Code/User"
mkdir -p "$VSCODE_USER"
ln -sf "$DOTFILES_DIR/vscode/settings.json"    "$VSCODE_USER/settings.json"
[ -f "$DOTFILES_DIR/vscode/keybindings.json" ] && \
    ln -sf "$DOTFILES_DIR/vscode/keybindings.json" "$VSCODE_USER/keybindings.json"
[ -d "$DOTFILES_DIR/vscode/snippets" ] && \
    ln -sf "$DOTFILES_DIR/vscode/snippets" "$VSCODE_USER/snippets"
}

###############################################################################
# Rectangle                                                                   #
###############################################################################
section_rectangle() {
echo "==> Importing Rectangle settings..."
defaults import com.knollsoft.Rectangle "$DOTFILES_DIR/rectangle/com.knollsoft.Rectangle.plist"
}

###############################################################################
# Vorssaint                                                                   #
###############################################################################
section_vorssaint() {
echo "==> Importing Vorssaint settings..."
defaults import com.vorssaint.utils "$DOTFILES_DIR/vorssaint/com.vorssaint.utils.plist"
}

###############################################################################
# Spotlight                                                                   #
###############################################################################
section_spotlight() {
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
}

###############################################################################
# iTerm2 Prefs                                                                #
###############################################################################
section_iterm2() {
echo "==> Configuring iTerm2 preferences..."
defaults write com.googlecode.iterm2 PrefsCustomFolder -string "$DOTFILES_DIR/iterm2"
defaults write com.googlecode.iterm2 LoadPrefsFromCustomFolder -bool true
# iTerm2 already writes directly to the PrefsCustomFolder — no symlink needed
}

###############################################################################
# Ghostty Config                                                              #
###############################################################################
section_ghostty() {
echo "==> Symlinking Ghostty config..."
GHOSTTY_DIR="$HOME/Library/Application Support/com.mitchellh.ghostty"
mkdir -p "$GHOSTTY_DIR"
ln -sf "$DOTFILES_DIR/ghostty/config.ghostty" "$GHOSTTY_DIR/config.ghostty"
}

###############################################################################
# herdr Config                                                                #
###############################################################################
section_herdr() {
echo "==> Symlinking herdr config..."
mkdir -p "$HOME/.config/herdr"
ln -sf "$DOTFILES_DIR/herdr/config.toml" "$HOME/.config/herdr/config.toml"
}

###############################################################################
# Cursor Settings                                                             #
###############################################################################
section_cursor() {
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
}

###############################################################################
# Claude Code Status Line                                                     #
###############################################################################
section_statusline() {
echo "==> Configuring Claude Code status line..."
CLAUDE_SETTINGS="$HOME/.claude/settings.json"
mkdir -p "$HOME/.claude"
if [ -f "$CLAUDE_SETTINGS" ]; then
    python3 -c "
import json
with open('$CLAUDE_SETTINGS') as f:
    s = json.load(f)
s['statusLine'] = {'type': 'command', 'command': '$HOME/.claude/statusline-command.sh', 'padding': 0, 'refreshInterval': 1}
with open('$CLAUDE_SETTINGS', 'w') as f:
    json.dump(s, f, indent=2)
"
else
    echo "{\"statusLine\":{\"type\":\"command\",\"command\":\"$HOME/.claude/statusline-command.sh\",\"padding\":0,\"refreshInterval\":1}}" > "$CLAUDE_SETTINGS"
fi
}

###############################################################################
# Default Editor (Cursor on work machines, VSCode on personal)               #
###############################################################################
section_editor() {
local primary_app fallback_app chosen_app bundle_id
if [ "${MACHINE_TYPE:-}" = "work" ]; then
    primary_app="Cursor"
    fallback_app="Visual Studio Code"
else
    primary_app="Visual Studio Code"
    fallback_app="Cursor"
fi

chosen_app="$primary_app"
bundle_id=$(osascript -e "id of app \"$primary_app\"" 2>/dev/null)
if [ -z "$bundle_id" ]; then
    echo "    $primary_app not found — falling back to $fallback_app."
    chosen_app="$fallback_app"
    bundle_id=$(osascript -e "id of app \"$fallback_app\"" 2>/dev/null)
fi

if [ -z "$bundle_id" ]; then
    echo "    Neither $primary_app nor $fallback_app found — skipping default editor setup."
    return
fi

echo "==> Setting $chosen_app as default text editor..."
duti -s "$bundle_id" public.plain-text all      # Plain text files
duti -s "$bundle_id" public.text all            # All text UTIs
duti -s "$bundle_id" public.source-code all     # All source code UTIs
duti -s "$bundle_id" public.shell-script all    # Shell scripts
duti -s "$bundle_id" public.json all            # JSON files
duti -s "$bundle_id" public.xml all             # XML files
duti -s "$bundle_id" public.yaml all            # YAML files
}

###############################################################################
# Bun                                                                         #
###############################################################################
section_bun() {
echo "==> Installing Bun..."
[ -d "$HOME/.bun" ] || curl -fsSL https://bun.sh/install | bash
}

###############################################################################
# Sublime Text Settings                                                       #
###############################################################################
section_sublime() {
echo "==> Symlinking Sublime Text settings..."
ST_INSTALLED="$HOME/Library/Application Support/Sublime Text/Installed Packages"
ST_USER="$HOME/Library/Application Support/Sublime Text/Packages/User"
if [ -d "$ST_USER" ]; then
    if [ ! -f "$ST_INSTALLED/Package Control.sublime-package" ]; then
        echo "    Installing Package Control loader..."
        mkdir -p "$ST_INSTALLED"
        curl -fsSL "https://packagecontrol.io/Package%20Control.sublime-package" \
            -o "$ST_INSTALLED/Package Control.sublime-package"
    fi
    ln -sf "$DOTFILES_DIR/sublime-text/Preferences.sublime-settings" "$ST_USER/Preferences.sublime-settings"
    ln -sf "$DOTFILES_DIR/sublime-text/Package Control.sublime-settings" "$ST_USER/Package Control.sublime-settings"
    echo "    Symlinks created. Packages auto-install on next ST launch."
else
    echo "    Sublime Text not found — open it once to create the User dir, then re-run."
fi
}

###############################################################################
# Text Replacements                                                           #
###############################################################################
section_textreplace() {
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
}

###############################################################################
# Basics (Setup mode — run automatically, no picker)                         #
###############################################################################
run_basics() {
section_macos
section_xcode
ensure_homebrew

echo "==> Installing gum..."
brew list gum &>/dev/null || brew install gum

echo "==> Installing Ghostty..."
brew list --cask ghostty &>/dev/null || brew install --cask ghostty
section_ghostty

section_git
section_zsh
section_dotfiles
}

###############################################################################
# Maintenance mode                                                            #
###############################################################################

# remove_brewfile_lines <raw_line...>
# Deletes exact lines from the real Brewfile in place.
remove_brewfile_lines() {
    local tmp bf_line rl skip
    tmp=$(mktemp)
    while IFS= read -r bf_line || [ -n "$bf_line" ]; do
        skip=0
        for rl in "$@"; do
            [ "$bf_line" = "$rl" ] && { skip=1; break; }
        done
        [ "$skip" -eq 1 ] || printf '%s\n' "$bf_line" >> "$tmp"
    done < "$DOTFILES_DIR/Brewfile"
    mv "$tmp" "$DOTFILES_DIR/Brewfile"
}

# Category + per-category item checklist over every current Brewfile entry
# (no work/personal filtering — maintenance sees everything). Selected
# entries are uninstalled and stripped from the Brewfile.
maintain_brewfile_removals() {
    parse_brewfile

    local cat_args=() cat items
    for cat in "${BREW_CATEGORIES[@]}"; do
        brew_category_items "$cat" items
        cat_args+=("$cat" "(${#items[@]} items)")
    done
    [ "${#cat_args[@]}" -eq 0 ] && return 0

    local chosen_categories
    select_checklist "Maintain — pick categories to review for removal" chosen_categories none "${cat_args[@]}"
    [ "${#chosen_categories[@]}" -eq 0 ] && return 0

    local to_remove=() chosen_items item_args it
    for cat in "${chosen_categories[@]}"; do
        brew_category_items "$cat" items
        item_args=()
        for it in "${items[@]}"; do item_args+=("$it" ""); done
        select_checklist "Maintain — $cat — select items to uninstall" chosen_items none "${item_args[@]}"
        to_remove+=("${chosen_items[@]}")
    done
    [ "${#to_remove[@]}" -eq 0 ] && { echo "Nothing selected for removal."; return 0; }

    echo "About to uninstall and remove from Brewfile:"
    printf '  %s\n' "${to_remove[@]}"
    local confirm
    read -rp "Proceed? [y/N] " confirm
    case "$confirm" in
        y|Y) ;;
        *) echo "Cancelled."; return 0 ;;
    esac

    local line name
    for line in "${to_remove[@]}"; do
        case "$line" in
            brew\ *)
                [[ "$line" =~ ^brew[[:space:]]+\"([^\"]+)\" ]] && name="${BASH_REMATCH[1]}"
                brew uninstall "$name" || true
                ;;
            cask\ *)
                [[ "$line" =~ ^cask[[:space:]]+\"([^\"]+)\" ]] && name="${BASH_REMATCH[1]}"
                brew uninstall --cask "$name" || true
                ;;
            vscode\ *)
                [[ "$line" =~ ^vscode[[:space:]]+\"([^\"]+)\" ]] && name="${BASH_REMATCH[1]}"
                code --uninstall-extension "$name" || true
                ;;
        esac
    done

    remove_brewfile_lines "${to_remove[@]}"
}

# Diffs installed brew formulae/casks/VSCode extensions against Brewfile
# (via `brew bundle cleanup`'s dry-run report), then lets you pick untracked
# items to append, tagged work/personal/common.
maintain_brewfile_additions() {
    echo "==> Checking for installed items missing from Brewfile..."
    local cleanup_output
    cleanup_output=$(brew bundle cleanup --file="$DOTFILES_DIR/Brewfile" 2>/dev/null)

    local missing_formulae=() missing_casks=() missing_vscode=()
    mapfile -t missing_formulae < <(awk '/^Would uninstall formulae:$/{f=1;next} /^Would /{f=0} f' <<< "$cleanup_output")
    mapfile -t missing_casks    < <(awk '/^Would uninstall casks:$/{f=1;next} /^Would /{f=0} f' <<< "$cleanup_output")
    mapfile -t missing_vscode   < <(awk '/^Would uninstall VSCode extensions:$/{f=1;next} /^Would /{f=0} f' <<< "$cleanup_output")

    echo "--- Installed but not in Brewfile ---"
    printf '%s\n' "${missing_formulae[@]}" "${missing_casks[@]}" "${missing_vscode[@]}" | grep -v '^$' || echo "  (none)"
    echo

    local item_args=() name
    for name in "${missing_formulae[@]}"; do item_args+=("brew:$name" "formula"); done
    for name in "${missing_casks[@]}";    do item_args+=("cask:$name" "cask"); done
    for name in "${missing_vscode[@]}";   do item_args+=("vscode:$name" "VSCode extension"); done
    [ "${#item_args[@]}" -eq 0 ] && return 0

    local chosen
    select_checklist "Maintain — installed but not in Brewfile — select to add" chosen none "${item_args[@]}"
    [ "${#chosen[@]}" -eq 0 ] && return 0

    local tag
    select_single "Maintain — tag for the entries you're adding" tag \
        common   "Common (both machines)" \
        work     "Work only" \
        personal "Personal only"

    grep -qxF "# Synced additions" "$DOTFILES_DIR/Brewfile" || printf '\n# Synced additions\n' >> "$DOTFILES_DIR/Brewfile"
    local entry type nm
    for entry in "${chosen[@]}"; do
        type="${entry%%:*}"
        nm="${entry#*:}"
        printf '%s "%s" # %s\n' "$type" "$nm" "$tag" >> "$DOTFILES_DIR/Brewfile"
    done

    echo "Added ${#chosen[@]} entries to Brewfile under '# Synced additions' — re-file them into the right category whenever convenient."
}

# Diffs installed Cursor extensions against cursor/extensions.txt, then lets
# you pick untracked extensions to add and tracked extensions to uninstall
# (removed from both Cursor and the tracked file). Only called when the
# `cursor` CLI is present.
maintain_cursor_extensions() {
    echo "==> Checking Cursor extension drift..."
    local installed_file tracked_file
    installed_file=$(mktemp)
    tracked_file=$(mktemp)
    cursor --list-extensions 2>/dev/null | sort > "$installed_file"
    sort "$DOTFILES_DIR/cursor/extensions.txt" > "$tracked_file"

    local untracked=() missing=()
    mapfile -t untracked < <(comm -23 "$installed_file" "$tracked_file")
    mapfile -t missing < <(comm -13 "$installed_file" "$tracked_file")
    rm -f "$installed_file" "$tracked_file"

    echo "--- Installed but not tracked ---"
    printf '%s\n' "${untracked[@]}"
    echo
    echo "--- Tracked but not installed ---"
    printf '%s\n' "${missing[@]}"
    echo

    if [ "${#untracked[@]}" -gt 0 ]; then
        local add_args=() ext chosen_add
        for ext in "${untracked[@]}"; do add_args+=("$ext" ""); done
        select_checklist "Maintain — Cursor extensions — select to add to extensions.txt" chosen_add all "${add_args[@]}"
        if [ "${#chosen_add[@]}" -gt 0 ]; then
            printf '%s\n' "${chosen_add[@]}" >> "$DOTFILES_DIR/cursor/extensions.txt"
            sort -o "$DOTFILES_DIR/cursor/extensions.txt" "$DOTFILES_DIR/cursor/extensions.txt"
            echo "Added ${#chosen_add[@]} extensions to cursor/extensions.txt."
        fi
    fi

    local ext_args=() ext
    while IFS= read -r ext || [ -n "$ext" ]; do
        [ -n "$ext" ] && ext_args+=("$ext" "")
    done < "$DOTFILES_DIR/cursor/extensions.txt"
    [ "${#ext_args[@]}" -eq 0 ] && return 0

    local chosen_ext
    select_checklist "Maintain — Cursor extensions — select to uninstall" chosen_ext none "${ext_args[@]}"
    [ "${#chosen_ext[@]}" -eq 0 ] && return 0

    echo "About to uninstall Cursor extensions:"
    printf '  %s\n' "${chosen_ext[@]}"
    local confirm
    read -rp "Proceed? [y/N] " confirm
    case "$confirm" in
        y|Y) ;;
        *) echo "Cancelled."; return 0 ;;
    esac

    for ext in "${chosen_ext[@]}"; do
        cursor --uninstall-extension "$ext" || true
    done

    local tmp
    tmp=$(mktemp)
    grep -vFxf <(printf '%s\n' "${chosen_ext[@]}") "$DOTFILES_DIR/cursor/extensions.txt" > "$tmp"
    mv "$tmp" "$DOTFILES_DIR/cursor/extensions.txt"
}

run_maintenance() {
echo "==> Checking for drift between Brewfile and installed state..."
echo "--- In Brewfile but not installed ---"
brew bundle check --file="$DOTFILES_DIR/Brewfile" --verbose 2>/dev/null | grep '^→' || echo "  (none)"
echo

maintain_brewfile_additions
maintain_brewfile_removals

if command -v cursor &>/dev/null; then
    maintain_cursor_extensions
fi

echo ""
echo "✓ Maintenance complete."
}

if [ "$MODE" = "maintain" ]; then
    run_maintenance
    exit 0
fi

# Setup mode.
if [ -n "${MACHINE_TYPE:-}" ]; then
    # No-args interactive path: basics always runs section_macos, so ask for
    # sudo upfront and keep the session alive for the whole run.
    sudo -v
    while true; do sudo -n true; sleep 60; kill -0 "$$" || exit; done 2>/dev/null &
    run_basics
    select_sections_interactively
else
    # Args path or non-interactive fallback: SELECTED is already final.
    if is_selected macos || is_selected spotlight; then
        sudo -v
        while true; do sudo -n true; sleep 60; kill -0 "$$" || exit; done 2>/dev/null &
    fi
fi

for key in "${SELECTED[@]}"; do
    "section_$key"
done

echo ""
echo "✓ Setup complete."
echo "  Next: open MIGRATION.md and work through the manual steps."
