Completion scripts for supported shells.

  $ for shell in bash zsh fish tcsh powershell; do emtorch shell-completions --shell $shell --print | grep -m 1 .; done
  #compdef emtorch
  #compdef emtorch
  function __fish_emtorch_complete
  complete "emtorch" 'p@*@`python-argcomplete-tcsh "emtorch"`@' ;
  Register-ArgumentCompleter -Native -CommandName emtorch -ScriptBlock {

Installation to default (per-user) locations.

  $ export HOME="$PWD" XDG_DATA_HOME= XDG_CONFIG_HOME=
  $ emtorch shell-completions --shell bash
  Completion script for bash installed to: */.local/share/bash-completion/completions/emtorch (glob)
  Restart your shell to enable completions.

  $ emtorch shell-completions --shell fish
  Completion script for fish installed to: */.config/fish/completions/emtorch.fish (glob)
  Restart your shell to enable completions.

  $ emtorch shell-completions --shell zsh
  Completion script for zsh installed to: */.local/share/zsh/site-functions/_emtorch (glob)
  Make sure '*/.local/share/zsh/site-functions' is in your $fpath before 'compinit' is called, e.g. add to ~/.zshrc: (glob)
    fpath=(*/.local/share/zsh/site-functions $fpath) (glob)
  Restart your shell to enable completions.

  $ find .local .config -type f | sort
  .config/fish/completions/emtorch.fish
  .local/share/bash-completion/completions/emtorch
  .local/share/zsh/site-functions/_emtorch

Shell detection, custom location and errors.

  $ SHELL=/usr/bin/fish emtorch shell-completions --print | grep -m 1 .
  function __fish_emtorch_complete

  $ SHELL=/bin/ksh emtorch shell-completions
  usage: emtorch shell-completions [-h]
                                   [--shell {bash,zsh,fish,tcsh,powershell}]
                                   [--print] [--path PATH]
  emtorch shell-completions: error: Unable to detect the shell, use --shell
  [2]

  $ emtorch shell-completions --shell tcsh
  usage: emtorch shell-completions [-h]
                                   [--shell {bash,zsh,fish,tcsh,powershell}]
                                   [--print] [--path PATH]
  emtorch shell-completions: error: No default location for tcsh completions, use --path or --print
  [2]

  $ emtorch shell-completions --shell tcsh --path custom/emtorch.tcsh
  Completion script for tcsh installed to: custom/emtorch.tcsh
  Restart your shell to enable completions.
  $ grep -c emtorch custom/emtorch.tcsh
  1

Completing command line (argcomplete protocol, as used by the installed scripts).

  $ complete() { COMP_LINE="$1" COMP_POINT=${#1} _ARGCOMPLETE=1 _ARGCOMPLETE_IFS=' ' emtorch 8>&1 9>/dev/null | sed 's/ *$//'; echo; }
  $ touch config.toml data.bin results.json

  $ complete 'emtorch '
  -h --help --version run subtasks subtask values shell-completions

  $ complete 'emtorch sh'
  shell-completions

  $ complete 'emtorch subtask ping-'
  ping-alive ping-stable

  $ complete 'emtorch run --repeat-mode '
  aabb abab

  $ complete 'emtorch run --config '
  custom/ .config/ .local/ config.toml

  $ complete 'emtorch values --format '
  csv text latex mediawiki html json

  $ complete 'emtorch values '
  -h --help --output --format --include --exclude custom/ .config/ .local/ results.json
