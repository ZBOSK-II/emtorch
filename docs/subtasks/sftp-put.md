<!--
Copyright (c) 2025-2026 Warsaw University of Technology
This file is licensed under the MIT License.
See the LICENSE.txt file in the root of the repository for full details.
-->

# Subtask: sftp-put

## Description
Uploads a file to a remote host using SFTP (SSH File Transfer Protocol). This subtask connects to a remote machine with the provided credentials and transfers a file from the local filesystem to a remote path. Used for deploying experiment scripts, configuration files, firmware, or other assets to target devices.

## Use Cases
- Deploying experiment scripts and tools to remote devices
- Uploading firmware binaries for over-the-air updates
- Distributing configuration files to multiple test nodes
- Transferring input data files needed by remote experiments
- Placing SSH keys or credentials on remote hosts

## Configuration Arguments

### Required Arguments
- **local_path** ($-string): Path on the local filesystem of the file to upload.
- **remote_path** ($-string): Destination path on the remote filesystem.
- **connection** (object): SFTP connection configuration containing:
  - **host** (string): Remote host address (IP or hostname).
  - **port** (int, default 22): SSH port number.
  - **username** (string): SSH login username.
  - **password** (string): SSH login password.

### Optional Arguments
- **timeout** (float, default 5.0): Operation timeout in seconds.

## Result
Returns SUCCESS if the file is uploaded successfully. Returns FAILURE or ERROR if the local file does not exist, the connection fails, or the transfer times out.

## Example Configuration

```toml
[[setups]]
type = "sftp-put"
name = "deploy_script"

[setups.args]
local_path = "./experiment_script.sh"
remote_path = "/home/pi/experiment/run.sh"
connection = { host = "192.168.1.100", port = 22, username = "pi", password = "raspberry" }
timeout = 10
```

```toml
[[actions]]
type = "sftp-put"
name = "upload_firmware"

[actions.args]
local_path = "$EMTORCH_DATA_PATH/firmware.bin"
remote_path = "/tmp/firmware_update.bin"
connection = { host = "10.0.0.50", username = "root", password = "admin123" }
timeout = 30
```

## Notes
- The remote directory must already exist — the subtask does not create parent directories.
- If a file already exists at `remote_path`, it will be overwritten.
- Template variables in path arguments are expanded before execution.
- For downloading files from remote hosts, use the complementary `sftp-get` subtask.
- Combine with the `remote` subtask to upload scripts, then execute them remotely.

## See Also
- [sftp-get](./sftp-get.md) — Download files from remote hosts
- [remote](./remote.md) — Execute commands on remote hosts via SSH
