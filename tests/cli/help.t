Top level help and version.

  $ emtorch --help
  usage: emtorch [-h] [--version] COMMAND ...
  
  Experiments orchestrator for embedded systems
  
  positional arguments:
    COMMAND              emtorch command to be executed (listed below)
      run                execute the experiment using configuration
      subtasks           lists all available subcommands
      subtask            provides documentation for the given task
      values             extracts values from results
      shell-completions  installs shell completion script
  
  options:
    -h, --help           show this help message and exit
    --version            show program's version number and exit
  
  Run 'emtorch <COMMAND> --help' to get help on a specific command

  $ emtorch --version
  \d+\.\d+\.\d+.* (re)

Missing or mistyped command.

  $ emtorch
  usage: emtorch [-h] [--version] COMMAND ...
  emtorch: error: the following arguments are required: COMMAND
  [2]

  $ emtorch rnu
  usage: emtorch [-h] [--version] COMMAND ...
  emtorch: error: argument COMMAND: invalid choice: 'rnu', maybe you meant 'run'? (choose from 'run', 'subtasks', 'subtask', 'values', 'shell-completions')
  [2]
