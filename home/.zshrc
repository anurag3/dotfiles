# Enable Powerlevel10k instant prompt. Should stay close to the top of ~/.zshrc.
# Initialization code that may require console input (password prompts, [y/n]
# confirmations, etc.) must go above this block; everything else may go below.
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi

# If you come from bash you might have to change your $PATH.
# export PATH=$HOME/bin:/usr/local/bin:$PATH

# Path to your oh-my-zsh installation.
export ZSH="$HOME/.oh-my-zsh"

# Set name of the theme to load --- if set to "random", it will
# load a random theme each time oh-my-zsh is loaded, in which case,
# to know which specific one was loaded, run: echo $RANDOM_THEME
# See https://github.com/ohmyzsh/ohmyzsh/wiki/Themes
# ZSH_THEME="robbyrussell"
ZSH_THEME="powerlevel10k/powerlevel10k"

# Set list of themes to pick from when loading at random
# Setting this variable when ZSH_THEME=random will cause zsh to load
# a theme from this variable instead of looking in $ZSH/themes/
# If set to an empty array, this variable will have no effect.
# ZSH_THEME_RANDOM_CANDIDATES=( "robbyrussell" "agnoster" )

# Uncomment the following line to use case-sensitive completion.
# CASE_SENSITIVE="true"

# Uncomment the following line to use hyphen-insensitive completion.
# Case-sensitive completion must be off. _ and - will be interchangeable.
# HYPHEN_INSENSITIVE="true"

# Uncomment one of the following lines to change the auto-update behavior
# zstyle ':omz:update' mode disabled  # disable automatic updates
# zstyle ':omz:update' mode auto      # update automatically without asking
# zstyle ':omz:update' mode reminder  # just remind me to update when it's time

# Uncomment the following line to change how often to auto-update (in days).
# zstyle ':omz:update' frequency 13

# Uncomment the following line if pasting URLs and other text is messed up.
# DISABLE_MAGIC_FUNCTIONS="true"

# Uncomment the following line to disable colors in ls.
# DISABLE_LS_COLORS="true"

# Uncomment the following line to disable auto-setting terminal title.
# DISABLE_AUTO_TITLE="true"

# Uncomment the following line to enable command auto-correction.
# ENABLE_CORRECTION="true"

# Uncomment the following line to display red dots whilst waiting for completion.
# You can also set it to another string to have that shown instead of the default red dots.
# e.g. COMPLETION_WAITING_DOTS="%F{yellow}waiting...%f"
# Caution: this setting can cause issues with multiline prompts in zsh < 5.7.1 (see #5765)
# COMPLETION_WAITING_DOTS="true"

# Uncomment the following line if you want to disable marking untracked files
# under VCS as dirty. This makes repository status check for large repositories
# much, much faster.
# DISABLE_UNTRACKED_FILES_DIRTY="true"

# Uncomment the following line if you want to change the command execution time
# stamp shown in the history command output.
# You can set one of the optional three formats:
# "mm/dd/yyyy"|"dd.mm.yyyy"|"yyyy-mm-dd"
# or set a custom format using the strftime function format specifications,
# see 'man strftime' for details.
# HIST_STAMPS="mm/dd/yyyy"

# Would you like to use another custom folder than $ZSH/custom?
# ZSH_CUSTOM=/path/to/new-custom-folder

# Which plugins would you like to load?
# Standard plugins can be found in $ZSH/plugins/
# Custom plugins may be added to $ZSH_CUSTOM/plugins/
# Example format: plugins=(rails git textmate ruby lighthouse)
# Add wisely, as too many plugins slow down shell startup.
plugins=(
  aws
  git
  terraform
  zsh-autosuggestions
  zsh-syntax-highlighting
  tmux
  kubectl
  direnv
  )

source $ZSH/oh-my-zsh.sh

timezsh() {
  shell=${1-$SHELL}
  for i in $(seq 1 10); do /usr/bin/time $shell -i -c exit; done
}

# jar_upload(){
#   sbt clean && sbt assembly
#   echo "sbt Done"
#   aws s3 cp target/scala-2.12/datagate-file-publisher.jar s3://hg-testing-code/datagate-file-publisher.jar
#   echo "Jar cp Done"
#   aws lambda update-function-code --function-name arn:aws:lambda:us-west-2:389057546498:function:datagate-dev-file-publisher --s3-bucket hg-testing-code --s3-key datagate-file-publisher.jar
#   echo "Lambda update Done"
#   aws s3 rm s3://hg-tests/test.txt
#   echo "txt rm Done"
#   aws s3 cp ~/Downloads/test.txt s3://hg-tests/
#   echo "txt cp Done"
# }

function cursor {
  open -a "/Applications/Cursor.app" "$@"
}


# User configuration

# export MANPATH="/usr/local/man:$MANPATH"

# You may need to manually set your language environment
# export LANG=en_US.UTF-8

# Preferred editor for local and remote sessions
# if [[ -n $SSH_CONNECTION ]]; then
#   export EDITOR='vim'
# else
#   export EDITOR='mvim'
# fi

# Compilation flags
# export ARCHFLAGS="-arch x86_64"

# Set personal aliases, overriding those provided by oh-my-zsh libs,
# plugins, and themes. Aliases can be placed here, though oh-my-zsh
# users are encouraged to define aliases within the ZSH_CUSTOM folder.
# For a full list of active aliases, run `alias`.
#
# Example aliases
alias zshconfig="cursor ~/.zshrc"
alias cc="claude"
alias cw="claude-workspace"
# alias ohmyzsh="mate ~/.oh-my-zsh"

alias arm="env /usr/bin/arch -arm64 /bin/zsh --login"

alias intel="env /usr/bin/arch -x86_64 /bin/zsh --login" 

# docker-compose alias
alias docker-compose="docker compose"

# Git shorthands
alias gs='git status'
alias ga='git add'
alias gd='git diff'
alias gc='git commit'
alias gp='git pull'
alias gps='git push'
alias gb='git branch'
alias gco='git checkout'
alias gcb='git checkout -b'
alias gl='git log --oneline --graph --decorate'

# HG Settings >>>>>>>>>>>>

# forward SSH keys for github push/pull on jumpbox
# if [ ! -S ~/.ssh/ssh_auth_sock ]; then
#   eval `ssh-agent`
#   ssh-add ~/.ssh/id_rsa
#   ln -sf "$SSH_AUTH_SOCK" ~/.ssh/ssh_auth_sock
# fi
# export SSH_AUTH_SOCK=~/.ssh/ssh_auth_sock
# ssh-add -l > /dev/null || ssh-add


# Pyenv Settings <<<<<<<<<<<<
# pyenv shim — translates pyenv commands to uv
pyenv() {
  case "$1" in
    install)  uv python install "${@:2}" ;;
    local)    uv python pin "${@:2}" ;;
    global)   uv python pin --global "${@:2}" ;;
    versions) uv python list ;;
    which)    uv python find "${@:2}" ;;
    virtualenv) uv venv "${@:2}" ;;
    *) command pyenv "$@" ;;
  esac
}


# Postgres libpq [For airflow docker image]
# export LDFLAGS="-L/opt/homebrew/opt/libpq/lib"
# export CPPFLAGS="-I/opt/homebrew/opt/libpq/include"
export PKG_CONFIG_PATH="/opt/homebrew/opt/libpq/lib/pkgconfig"
export CPPFLAGS="-I$(brew --prefix abseil)/include -I$(brew --prefix pybind11)/include -I$(brew --prefix re2)/include"
export CXXFLAGS="-I$(brew --prefix abseil)/include -I$(brew --prefix pybind11)/include -I$(brew --prefix re2)/include -std=c++17"
export LDFLAGS="-L$(brew --prefix re2)/lib"

# OpenSSL
# export LDFLAGS="-L/usr/local/opt/openssl/lib"
# export CPPFLAGS="-I/usr/local/opt/openssl/include"
# export PKG_CONFIG_PATH="/usr/local/opt/openssl/lib/pkgconfig"

export PATH="$HOME/.local/bin:$PATH"

# Added by LM Studio CLI (lms)
# export PATH="$PATH:/Users/anurag.desai/.lmstudio/bin"
# End of LM Studio CLI section

# bun completions
[ -s "/Users/anurag.desai/.oh-my-zsh/completions/_bun" ] && source "/Users/anurag.desai/.oh-my-zsh/completions/_bun"

# bun
export BUN_INSTALL="$HOME/.bun"
export PATH="$BUN_INSTALL/bin:$PATH"
# To customize prompt, run `p10k configure` or edit ~/.p10k.zsh.
[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh


fpath=(/Users/anurag.desai/.docker/completions $fpath)
autoload -Uz compinit
compinit
# End of Docker CLI completions

#THIS MUST BE AT THE END OF THE FILE FOR SDKMAN TO WORK!!!
[[ -s "/Users/anurag.desai/.sdkman/bin/sdkman-init.sh" ]] && source "/Users/anurag.desai/.sdkman/bin/sdkman-init.sh"