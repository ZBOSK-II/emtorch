Listing available subtasks.

  $ emtorch subtasks
  Known Sub Tasks:
  
  \tcoap-monitor (esc)
  \tcoap-send (esc)
  \techo (esc)
  \texec (esc)
  \tfile-write (esc)
  \tlogger-float-matcher (esc)
  \tlogger-int-matcher (esc)
  \tping-alive (esc)
  \tping-stable (esc)
  \tremote (esc)
  \tsftp-get (esc)
  \tsftp-put (esc)
  \tshell (esc)
  
  Type 'emtorch subtask <TASK-NAME>' to get help on the given task's arguments

Subtask documentation.

  $ emtorch subtask echo
  
  echo
  ====
  
  Basic echo command, prints to log a provided message.
  
  
  Arguments
  ---------
    message                  - ($-string) message to write to log

  $ emtorch subtask shell
  
  shell
  =====
  
  Executes system shell command.
  
  
  Arguments
  ---------
    cmd                      - ($-string) shell command to be executed
    timeout                  - (float) execution timeout (default: 1.0)
    signal                   - (string) signal name to be sent to the program at the end of monitoring (default: None)

Missing or unknown subtask name.

  $ emtorch subtask
  usage: emtorch subtask [-h] name
  emtorch subtask: error: the following arguments are required: name
  [2]

  $ emtorch subtask unknown
  ERROR: "Unknown subtask type 'unknown'" [KeyError]
  [255]
