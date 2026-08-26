<!--
Copyright (c) 2025-2026 Warsaw University of Technology
This file is licensed under the MIT License.
See the LICENSE.txt file in the root of the repository for full details.
-->

# Subtask: file-write

## Description
Writes specified contents to a file on the local filesystem. This subtask can create new files or overwrite existing ones, and optionally append to existing files. It supports configurable text encoding and template variable expansion in both the file path and contents.

## Use Cases
- Generating experiment configuration files dynamically
- Writing measurement results and summaries to output files
- Creating log files with structured data for later analysis
- Producing reports with template-based content
- Saving intermediate processing results during multi-step experiments
- Writing SSH keys, credentials, or configuration snippets to disk

## Configuration Arguments

### Required Arguments
- **path** ($-string): Path to the file to create or modify.
- **contents** ($-string): Content to write to the file.

### Optional Arguments
- **append** (boolean, default false): If true, appends content to the end of an existing file instead of overwriting it.
- **encoding** (string, default "utf-8"): Character encoding to use when writing the file.

## Result
Returns SUCCESS if the file is written successfully. Returns ERROR if the path is invalid, the directory cannot be created, or encoding fails.

## Example Configuration

```toml
[[actions]]
type = "file-write"
name = "save_results"

[actions.args]
path = "/tmp/experiment_output.txt"
contents = "Case $EMTORCH_CASE_ID completed successfully"
encoding = "utf-8"
```

```toml
[[actions]]
type = "file-write"
name = "append_log"

[actions.args]
path = "/tmp/experiment.log"
contents = "Measurement at $(date): data from $EMTORCH_DATA_FILENAME\n"
append = true
```

## Notes
- If the parent directory of the specified path does not exist, the subtask will attempt to create it.
- Template variables in both `path` and `contents` are expanded before writing.
- When `append` is true, content is added to the end of the file. If the file does not exist, it is created.
- The default encoding is UTF-8 — specify a different encoding for compatibility with legacy systems.
- For writing binary data, use the `shell` or `exec` subtask with appropriate tools.

## See Also
- [echo](./echo.md) — Write messages to log output instead of files
- [shell](./shell.md) — Use shell redirection for more complex file operations
- [sftp-get](./sftp-get.md) — Transfer generated files to remote hosts
