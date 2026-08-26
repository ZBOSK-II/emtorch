<!--
Copyright (c) 2025-2026 Warsaw University of Technology
This file is licensed under the MIT License.
See the LICENSE.txt file in the root of the repository for full details.
-->

# Troubleshooting

Solutions to common issues and questions when using emtorch.

## Installation Issues

### "Python 3.14 or later required"

**Problem:** Error message when installing or running emtorch.

**Solution:**
Check your Python version:
```bash
python3 --version
```

If you have multiple Python versions, specify the correct one:
```bash
python3.14 -m emtorch run data.bin -c config.toml
```

Or upgrade Python to version 3.14 or later.

### "pip: command not found"

**Problem:** Cannot install emtorch with pip.

**Solution:**
Try using the Python module form of pip:
```bash
python3 -m pip install emtorch
```

Or install via poetry:
```bash
poetry install
```

### "ModuleNotFoundError: No module named 'emtorch'"

**Problem:** emtorch installed but not found when running.

**Solution:**
Verify installation:
```bash
python3 -m pip list | grep emtorch
```

If not listed, reinstall:
```bash
python3 -m pip install --upgrade emtorch
```

If working from source with poetry:
```bash
poetry install
poetry shell
python3 -m emtorch run data.bin -c config.toml
```

---

## Configuration Issues

### "Invalid TOML syntax"

**Problem:** Error parsing configuration file.

**Common causes and solutions:**

1. **Missing quotes on strings:**
   ```toml
   # Wrong
   message = hello world
   
   # Correct
   message = "hello world"
   ```

2. **Using wrong section syntax:**
   ```toml
   # Wrong - using single brackets for arrays
   [actions]
   
   # Correct - using double brackets for array items
   [[actions]]
   ```

3. **Incorrect nesting:**
   ```toml
   # Wrong
   [[actions]]
   type = "echo"
   [args]  # Wrong location
   message = "test"
   
   # Correct
   [[actions]]
   type = "echo"
   name = "test"
   
   [actions.args]
   message = "test"
   ```

4. **Using wrong data types:**
   ```toml
   # Wrong
   timeout = "5"  # String instead of number
   
   # Correct
   timeout = 5    # Number
   ```

**To validate your TOML:**
```bash
# Use Python to validate
python3 -c "import tomllib; tomllib.loads(open('config.toml').read())"
```

### "Unknown subtask: <NAME>"

**Problem:** Configuration references a subtask that doesn't exist.

**Solution:**
Check available subtasks:
```bash
python3 -m emtorch subtasks
```

Verify the subtask name in your configuration matches exactly (case-sensitive):
```toml
type = "echo"      # Correct
type = "Echo"      # Wrong - incorrect case
type = "ecco"      # Wrong - typo
```

### "Missing required argument"

**Problem:** Subtask configuration missing required parameters.

**Solution:**
Check the subtask documentation:
```bash
python3 -m emtorch subtask shell
```

Example error resolution:
```toml
# Wrong - missing required 'cmd' parameter
[[actions]]
type = "shell"
name = "test"

# Correct
[[actions]]
type = "shell"
name = "test"

[actions.args]
cmd = "echo hello"
```

### "Extra parameter not allowed"

**Problem:** Configuration includes a parameter the subtask doesn't support.

**Solution:**
Check valid parameters for the subtask:
```bash
python3 -m emtorch subtask <SUBTASK_NAME>
```

Common typos:
- `comand` → `cmd`
- `commmand` → `cmd`
- `timeout_seconds` → `timeout`
- `host_name` → `host`

---

## Data File Issues

### "No such file or directory"

**Problem:** Data files not found.

**Solution:**
1. Verify files exist:
   ```bash
   ls -la test_data/
   ```

2. Use absolute paths or verify relative paths:
   ```bash
   # Check current directory
   pwd
   
   # Use absolute path
   python3 -m emtorch run /absolute/path/to/data.bin -c config.toml
   ```

3. Use glob patterns correctly:
   ```bash
   # Verify glob matches files
   ls test_data/*.bin
   
   # Use the same pattern with emtorch
   python3 -m emtorch run test_data/*.bin -c config.toml
   ```

### "Cannot read data file"

**Problem:** Data file exists but cannot be accessed.

**Solution:**
1. Check file permissions:
   ```bash
   ls -la test_data/data.bin
   ```

2. Make file readable:
   ```bash
   chmod 644 test_data/data.bin
   ```

3. Verify you own the file or have read permissions

---

## Execution Issues

### Command exits with no output

**Problem:** emtorch runs but produces no results.

**Possible causes:**

1. **No results directory exists:** Check for result files
   ```bash
   ls *.json
   ls results_*.json  # if using -o results_
   ```

2. **Configuration has no phases:** Ensure config has at least one phase
   ```toml
   # At least one of these must exist
   [[setups]]
   [[actions]]
   [[checks]]
   ```

3. **Invalid configuration path:** Verify path is correct
   ```bash
   python3 -m emtorch run data.bin -c ./configs/myconfig.toml
   ```

### "Timeout occurred"

**Problem:** Subtask execution times out.

**Solution:**

1. **Increase timeout:**
   ```toml
   [[actions]]
   type = "shell"
   name = "slow_command"
   
   [actions.args]
   cmd = "sleep 10"
   timeout = 15  # Increased from default 1.0
   ```

2. **Check if command is actually slow:**
   ```bash
   # Test the command directly
   time cat $EMTORCH_DATA_PATH | wc -l
   ```

3. **Use longer timeouts for remote operations:**
   ```toml
   [[actions]]
   type = "remote"
   name = "remote_command"
   
   [actions.args]
   connection = {host = "example.com", username = "user", password = "pass"}
   cmd = "long_running_script.sh"
   timeout = 30  # Remote operations often need more time
   ```

### "Connection refused" (Remote subtasks)

**Problem:** Cannot connect to remote host.

**Solutions:**

1. **Verify network connectivity:**
   ```bash
   ping -c 2 example.com
   ```

2. **Verify SSH access:**
   ```bash
   ssh user@example.com "whoami"
   ```

3. **Check credentials in configuration:**
   ```toml
   [actions.args]
   connection = {
     host = "example.com",        # Correct hostname
     username = "your_username",   # Correct username
     password = "your_password"    # Correct password
   }
   ```

4. **Verify SSH port (if not default 22):**
   ```toml
   [actions.args]
   connection = {
     host = "example.com",
     port = 2222,  # If using non-standard port
     username = "user",
     password = "pass"
   }
   ```

### "Permission denied" (Remote subtasks)

**Problem:** SSH connection succeeds but command fails.

**Solutions:**

1. **Test SSH command directly:**
   ```bash
   ssh user@example.com "/path/to/command"
   ```

2. **Verify user has permissions for the command**

3. **Use absolute paths for remote commands:**
   ```toml
   [actions.args]
   cmd = "/usr/local/bin/mycommand"  # Full path
   ```

---

## Output and Results Issues

### No result files generated

**Problem:** Configuration runs but no JSON output files created.

**Solutions:**

1. **Check output directory:**
   ```bash
   # Results created in current directory
   ls -la *.json
   
   # Or with prefix
   ls -la results_*.json
   ```

2. **Verify output prefix is correct:**
   ```bash
   # Without prefix (default: emtorch_)
   python3 -m emtorch run data.bin -c config.toml
   ls emtorch_0.json
   
   # With custom prefix
   python3 -m emtorch run data.bin -c config.toml -o results_
   ls results_0.json
   ```

3. **Check file permissions** - results directory might not be writable
   ```bash
   ls -la .
   chmod 755 .  # If directory not writable
   ```

### Result files are empty or corrupted

**Problem:** JSON result files are missing data or malformed.

**Solutions:**

1. **Verify file integrity:**
   ```bash
   python3 -c "import json; json.load(open('result_0.json'))" && echo "Valid"
   ```

2. **Check for disk space issues:**
   ```bash
   df -h  # Check available disk space
   ```

3. **Verify subtask execution succeeded:**
   Look at the "status" field in results - if all subtasks show FAILURE, check subtask configuration

### "Status: FAILURE" in results

**Problem:** Subtasks executed but returned FAILURE status.

**Solution:**
Examine the "log" field in results to understand what failed:

```bash
python3 -c "
import json
result = json.load(open('result_0.json'))
for phase in ['setups', 'actions', 'checks']:
    for task, data in result['results'].get(phase, {}).items():
        if data['status'] != 'SUCCESS':
            print(f'{task}: {data[\"status\"]}')
            print(data['log'])
"
```

Common causes:
- Command returned non-zero exit code
- File not found or permission denied
- Network timeout or connection failure
- Syntax error in command

---

## Data Collection Issues (Logger Matchers)

### "Pattern not found"

**Problem:** logger-*-matcher doesn't extract values.

**Solution:**

1. **Verify regex pattern:**
   ```python
   import re
   
   # Test your pattern
   pattern = r"Metric: (?P<value>\d+\.\d+)"
   log = "Metric: 42.5 ops/sec"
   match = re.search(pattern, log)
   print(match.group('value') if match else "No match")
   ```

2. **Check subtask name reference:**
   ```toml
   [[actions]]
   type = "shell"
   name = "measure"  # Note this name
   [actions.args]
   cmd = "echo 'Metric: 42.5'"
   
   [[checks]]
   type = "logger-float-matcher"
   name = "extract"
   [checks.args]
   subtask = "measure"  # Must match the name above
   pattern = "Metric: (?P<value>\\d+\\.\\d+)"
   value = "metric"
   ```

3. **Verify log contains the expected text:**
   Check the subtask log in results JSON to confirm output format

### "Value type mismatch"

**Problem:** Using logger-int-matcher for float values or vice versa.

**Solution:**
- Use `logger-int-matcher` for integer values: 42, 100
- Use `logger-float-matcher` for decimal values: 42.5, 1.23

---

## Network Issues

### "Host unreachable"

**Problem:** ping or network subtasks fail.

**Solutions:**

1. **Test network connectivity:**
   ```bash
   ping -c 2 192.168.1.1
   traceroute 192.168.1.1
   ```

2. **Check firewall rules** - emtorch may be blocked

3. **Verify IP address or hostname in configuration:**
   ```toml
   [actions.args]
   host = "192.168.1.1"  # Correct IP
   ```

### "Network timeout"

**Problem:** Network operations timeout even though network works.

**Solutions:**

1. **Increase timeout:**
   ```toml
   [actions.args]
   host = "192.168.1.1"
   timeout = 30  # Increase from default
   ```

2. **Check network latency:**
   ```bash
   ping -c 10 192.168.1.1 | tail -1  # Check avg/min/max
   ```

3. **Use larger interval for ping operations:**
   ```toml
   [actions.args]
   host = "192.168.1.1"
   interval = 2  # Seconds between pings
   ```

---

## File Transfer Issues (SFTP)

### "SFTP connection failed"

**Problem:** sftp-get or sftp-put fails.

**Solutions:**

1. **Verify SSH access first:**
   ```bash
   ssh user@example.com "ls -la /remote/path/"
   ```

2. **Check file permissions:**
   ```bash
   # On remote host
   ls -la /remote/file.txt
   ```

3. **Verify paths are absolute:**
   ```toml
   [actions.args]
   remote_path = "/absolute/path/to/remote/file.txt"  # Full path
   local_path = "/absolute/path/to/local/file.txt"    # Full path
   ```

### "File not found" (remote)

**Problem:** SFTP operation claims remote file doesn't exist.

**Solution:**
1. **Verify file exists on remote host:**
   ```bash
   ssh user@example.com "test -f /path/to/file && echo exists || echo missing"
   ```

2. **Check you have read permission:**
   ```bash
   ssh user@example.com "test -r /path/to/file && echo readable || echo not readable"
   ```

---

## CoAP Issues

### "CoAP monitor times out"

**Problem:** coap-monitor waits but receives no messages.

**Solutions:**

1. **Verify CoAP device is reachable:**
   ```bash
   ping -c 2 192.168.1.50
   ```

2. **Check listening address and port:**
   ```toml
   [monitoring.args]
   address = "192.168.1.50:5683"  # Standard CoAP port
   ```

3. **Verify device is actually sending messages**

4. **Increase observation timeout:**
   ```toml
   [monitoring.args]
   observation_timeout = 30  # Seconds to listen
   ```

### "CoAP send fails"

**Problem:** coap-send returns failure.

**Solutions:**

1. **Ensure monitor is running:**
   ```toml
   [[monitoring]]
   type = "coap-monitor"
   name = "monitor"  # This name must exist
   [monitoring.args]
   address = "192.168.1.50:5683"
   
   [[actions]]
   type = "coap-send"
   name = "send"
   [actions.args]
   monitor = "monitor"  # Must reference monitoring subtask
   ```

2. **Verify CoAP device is responding**

3. **Check message format is valid for the device**

---

## Debugging Techniques

### Enable Detailed Logging

Create a configuration with verbose output:

```toml
[delays]
between_cases = 1.0

[[setups]]
type = "echo"
name = "debug_start"

[setups.args]
message = "Starting debugging for case $EMTORCH_CASE_ID"

[[actions]]
type = "echo"
name = "debug_info"

[actions.args]
message = "Data: $EMTORCH_DATA_PATH"
```

### Test Subtasks Individually

Before building a complex configuration, test each subtask:

```bash
# Test echo
python3 -m emtorch run data.bin -c test_echo.toml

# Test shell
python3 -m emtorch run data.bin -c test_shell.toml

# Test remote
python3 -m emtorch run data.bin -c test_remote.toml
```

### Examine Result Files

View results in a readable format:

```bash
python3 -c "
import json, sys
data = json.load(open(sys.argv[1]))
print(json.dumps(data, indent=2))
" result_0.json | less
```

### Run with Single Data File

Always test configuration with one file before full run:

```bash
python3 -m emtorch run test_data/single.bin -c config.toml
```

---

## Getting More Help

- **Subtask documentation:** `python3 -m emtorch subtask <NAME>`
- **List subtasks:** `python3 -m emtorch subtasks`
- **Full help:** `python3 -m emtorch --help`
- **Configuration guide:** See [Configuration Guide](./configuration-guide.md)
- **Subtasks reference:** See [Subtasks Reference](./subtasks/index.md)

---

## Still Stuck?

If you've tried these solutions and still have issues:

1. **Check the logs carefully** - emtorch provides detailed error messages
2. **Review relevant documentation** - links above
3. **Test each component separately** - isolate the problem
4. **Check the CHANGELOG** - your issue might be fixed in a newer version

---

Remember: Most issues are related to configuration syntax or network connectivity. Start by verifying these two areas!
