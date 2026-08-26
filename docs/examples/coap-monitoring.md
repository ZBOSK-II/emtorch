<!--
Copyright (c) 2025-2026 Warsaw University of Technology
This file is licensed under the MIT License.
See the LICENSE.txt file in the root of the repository for full details.
-->

# Tutorial: CoAP Device Monitoring

## Overview

This tutorial teaches you how to use emtorch to test and monitor IoT devices that communicate using the Constrained Application Protocol (CoAP). You will learn how to set up a `coap-monitor` subtask to listen for incoming CoAP messages, use the `coap-send` subtask to send messages to devices, coordinate background monitoring with foreground actions, and interpret the captured CoAP responses. By the end of this guide you will be able to build automated experiments that interact with CoAP-enabled embedded devices — including sensors, actuators, and other constrained IoT hardware.

## Prerequisites

**Software:**
- Python 3.14 or later with emtorch installed
- (Optional) A CoAP client tool like `coap-client` from the [libcoap](https://github.com/obgm/libcoap) package for manual testing
- Network access to a CoAP-enabled device or a CoAP simulator

**Knowledge:**
- Basic understanding of emtorch concepts (cases, phases, subtasks) — complete the [Basic Experiment Tutorial](./basic-experiment.md) first if needed
- Familiarity with UDP/IP networking (CoAP runs over UDP)
- No prior CoAP experience required — this tutorial explains the basics

**Hardware/Setup:**
- A CoAP-enabled IoT device on your network (e.g., ESP32 with CoAP server, Raspberry Pi running a CoAP endpoint, or a cloud-based CoAP service)
- OR a local CoAP test server for simulation (see notes below)
- The device's IP address and CoAP port (default: 5683)

> **CoAP in Brief:** CoAP (Constrained Application Protocol, RFC 7252) is a UDP-based protocol designed for IoT devices. It is similar to HTTP but optimized for low-power, constrained networks. CoAP uses a request/response model with methods like GET, POST, PUT, and DELETE. Unlike HTTP, CoAP runs over UDP and supports built-in discovery, multicast, and observation (subscription to resource changes).

## Scenario

You are developing an IoT environmental monitoring system with multiple wireless sensor nodes. Each node exposes sensor readings via CoAP resources. Your testing workflow needs to:

1. Monitor the CoAP traffic from a sensor node to capture unsolicited notifications (e.g., periodic temperature reports).
2. Send specific CoAP requests (GET, POST) to query sensor values or change device configuration.
3. Verify that the device responds correctly within expected time bounds.
4. Collect and analyse the captured messages for validation.

The experiment will run against multiple data files representing different query payloads or expected response patterns.

## Step 1: Prepare Test Data

Create a project directory with data files that describe the CoAP queries to send.

```bash
mkdir -p ~/emtorch-coap-tutorial
cd ~/emtorch-coap-tutorial
mkdir -p queries
```

Create three query definition files, each representing a different interaction with the CoAP device.

**File `queries/get_temperature.txt`:**

```
METHOD=GET
RESOURCE=/sensors/temperature
EXPECTED_CODE=2.05
DESCRIPTION=Query current temperature reading
```

**File `queries/get_humidity.txt`:**

```
METHOD=GET
RESOURCE=/sensors/humidity
EXPECTED_CODE=2.05
DESCRIPTION=Query current humidity reading
```

**File `queries/set_interval.txt`:**

```
METHOD=PUT
RESOURCE=/config/report_interval
PAYLOAD=30
EXPECTED_CODE=2.04
DESCRIPTION=Set reporting interval to 30 seconds
```

Create them from the command line:

```bash
cat > queries/get_temperature.txt << 'EOF'
METHOD=GET
RESOURCE=/sensors/temperature
EXPECTED_CODE=2.05
DESCRIPTION=Query current temperature reading
EOF

cat > queries/get_humidity.txt << 'EOF'
METHOD=GET
RESOURCE=/sensors/humidity
EXPECTED_CODE=2.05
DESCRIPTION=Query current humidity reading
EOF

cat > queries/set_interval.txt << 'EOF'
METHOD=PUT
RESOURCE=/config/report_interval
PAYLOAD=30
EXPECTED_CODE=2.04
DESCRIPTION=Set reporting interval to 30 seconds
EOF
```

### What Happens

You have created three query definition files. Each describes a CoAP interaction (method, resource path, expected response code) that the experiment will perform against a CoAP-enabled device. Each file becomes one case in the experiment.

## Step 2: Understand CoAP Subtask Coordination

emtorch provides two subtasks for CoAP communication:

| Subtask | Phase | Purpose |
|---------|-------|---------|
| `coap-monitor` | Monitoring (or any phase) | Listens for incoming CoAP messages on a UDP socket. Runs in the background, capturing messages for a specified observation period. |
| `coap-send` | Actions | Sends a CoAP message via an active monitor and waits for a response. Requires a running monitor as its communication channel. |

**How They Work Together:**

1. The `coap-monitor` opens a UDP socket at a specified address (e.g., `0.0.0.0:5683`) and listens for incoming CoAP messages.
2. The `coap-send` subtask references the monitor by name and sends a CoAP message through it.
3. The monitor captures both the outgoing request and incoming response.
4. After the observation timeout expires, the monitor stops and returns the captured messages.

```
┌────────────────────────────────────────────────┐
│  Monitoring Phase                              │
│  ┌──────────────────────────────────────────┐  │
│  │  coap-monitor "sensor_monitor"           │  │
│  │  ┌────────────┐  ┌────────────┐         │  │
│  │  │ UDP Socket │  │ Message    │         │  │
│  │  │ :5683      │  │ Capture    │         │  │
│  │  └────────────┘  └────────────┘         │  │
│  └──────────────────────────────────────────┘  │
│                                               │
│  Actions Phase                                 │
│  ┌──────────────────────────────────────────┐  │
│  │  coap-send "send_query"                 │  │
│  │  • References: "sensor_monitor"          │  │
│  │  • Sends CoAP request                   │  │
│  │  • Waits for response                   │  │
│  └──────────────────────────────────────────┘  │
└────────────────────────────────────────────────┘
```

> **Key Concept:** The `coap-send` subtask does not open its own connection. It uses the UDP socket created by the `coap-monitor` subtask. This means the monitor must be defined in the `monitoring` phase (so it starts before actions) and the `coap-send` must reference it by the monitor's `name`.

## Step 3: Write the CoAP Experiment Configuration

Create the file `coap-experiment.toml`:

```toml
# =============================================================================
# CoAP Device Monitoring Experiment Configuration
# =============================================================================
# This experiment monitors CoAP traffic from an IoT device and sends
# queries to read sensor values and change device configuration.
# =============================================================================

# --- Device Configuration ---
# Replace with your CoAP device address
coap_host = "192.168.1.50"
coap_port = 5683
listen_address = "0.0.0.0:5683"

# --- Timing Configuration ---
[delays]
between_cases = 1.0        # Pause between test cases
before_actions = 1.0       # Wait for monitor to initialize

# =============================================================================
# SETUPS PHASE — Preparation
# =============================================================================

[[setups]]
type = "echo"
name = "announce_case"

[setups.args]
message = "=== CoAP Test Case $EMTORCH_CASE_ID — $EMTORCH_DATA_FILENAME ==="

# Parse the query file and display its contents
[[setups]]
type = "shell"
name = "show_query_details"

[setups.args]
cmd = "echo 'Query definition:' && cat $EMTORCH_DATA_PATH"
timeout = 3

# =============================================================================
# MONITORING PHASE — CoAP message capture
# =============================================================================
# The monitor listens on the specified UDP address for CoAP messages.
# It runs in the background while actions execute.

[[monitoring]]
type = "coap-monitor"
name = "sensor_monitor"

[monitoring.args]
address = "$listen_address"
observation_timeout = 15.0

# =============================================================================
# ACTIONS PHASE — Send CoAP messages
# =============================================================================
# Each action sends a CoAP request through the active monitor.
# The monitor captures the request and any response from the device.

# Parse query parameters from the data file and send via shell utility
[[actions]]
type = "echo"
name = "action_start"

[actions.args]
message = "Sending CoAP query for case $EMTORCH_CASE_ID"

# Send a CoAP request using the coap-send subtask
[[actions]]
type = "coap-send"
name = "send_device_query"

[actions.args]
monitor = "sensor_monitor"
response_timeout = 5.0

# =============================================================================
# CHECKS PHASE — Analyse captured messages
# =============================================================================

[[checks]]
type = "echo"
name = "check_start"

[checks.args]
message = "=== Analysing CoAP responses for case $EMTORCH_CASE_ID ==="

# Display the monitor's captured log to see what CoAP messages were exchanged
[[checks]]
type = "shell"
name = "display_captured_traffic"

[checks.args]
cmd = "echo 'Captured CoAP traffic for case $EMTORCH_CASE_ID (see monitoring result in JSON)'"
timeout = 3

# Verify device is still reachable via ping
[[checks]]
type = "ping-alive"
name = "verify_device_reachable"

[checks.args]
host = "$coap_host"
timeout = 5
interval = 100

[[checks]]
type = "echo"
name = "case_complete"

[checks.args]
message = "=== CoAP test case $EMTORCH_CASE_ID complete ==="
```

### How the CoAP Subtasks Work Together

**The `coap-monitor` subtask (`sensor_monitor`):**

- Runs in the `monitoring` phase, which starts before actions and continues until actions complete.
- Opens a UDP socket on `0.0.0.0:5683` (all interfaces, standard CoAP port).
- Listens for CoAP messages for up to `observation_timeout = 15.0` seconds.
- Captures all incoming and outgoing CoAP messages during this window.
- When actions complete and the monitoring phase ends, the monitor stops and returns the captured data.

**The `coap-send` subtask (`send_device_query`):**

- Runs in the `actions` phase, after the monitor has started.
- References `monitor = "sensor_monitor"` to use the monitor's UDP socket.
- Sends a CoAP message to the device configured in the monitor.
- Waits up to `response_timeout = 5.0` seconds for a response.
- Returns SUCCESS if a CoAP response is received, FAILURE if no response arrives.

> **Note:** In this configuration, `coap-send` sends a CoAP GET request by default. The exact payload and method (GET, POST, PUT) are determined by the monitor's implementation and the data content. Some emtorch builds support additional parameters like `method` and `payload` in `coap-send.args`. Check your version:
> ```bash
> python3 -m emtorch subtask coap-send
> ```

### About the Monitor Address

The `address` parameter in `coap-monitor` specifies the UDP endpoint to listen on:

- `address = "0.0.0.0:5683"` — Listen on all network interfaces on the standard CoAP port. Use this when the CoAP device sends messages to your machine's IP.
- `address = "192.168.1.100:5683"` — Listen on a specific interface IP. Use this for multi-homed machines.
- `address = ":5683"` — Also listens on all interfaces (host part is optional).

The CoAP device must be configured to send messages to the address and port where your monitor is listening. In a typical setup:
- Your experiment machine runs the monitor on `0.0.0.0:5683`.
- The IoT device is configured with your machine's IP address as the CoAP destination.
- When you send a CoAP request via `coap-send`, it goes to the device; the device's response comes back to your monitor.

## Step 4: Run the Experiment

```bash
cd ~/emtorch-coap-tutorial
python3 -m emtorch run queries/get_temperature.txt queries/get_humidity.txt queries/set_interval.txt -c coap-experiment.toml -o coap_results_
```

Or using a glob:

```bash
python3 -m emtorch run queries/*.txt -c coap-experiment.toml -o coap_results_
```

### What Happens

For each query file:

1. **Setups:** The case is announced and the query definition is printed to the log.
2. **Monitoring starts:** The `coap-monitor` opens a UDP socket on `0.0.0.0:5683` and begins listening for CoAP messages. It will listen for up to 15 seconds.
3. **Delay:** The `before_actions` delay (1.0 s) gives the monitor time to initialize.
4. **Actions:** The `coap-send` subtask sends a CoAP message through the monitor. If the device is reachable, it responds with the requested data or an acknowledgement.
5. **Monitoring stops:** After actions complete, the monitor stops listening. All captured CoAP messages are stored in the result.
6. **Checks:** The captured traffic summary is recorded, device connectivity is verified with ping, and completion is logged.

## Step 5: Examine the Results

```bash
cat coap_results_0.json
```

The results contain the monitor's output with captured CoAP messages:

```json
{
  "case_id": "0",
  "data_path": "/home/user/emtorch-coap-tutorial/queries/get_temperature.txt",
  "data_filename": "get_temperature.txt",
  "results": {
    "setups": {
      "announce_case": {
        "status": "SUCCESS",
        "log": "=== CoAP Test Case 0 — get_temperature.txt ===\n"
      },
      "show_query_details": {
        "status": "SUCCESS",
        "log": "Query definition:\nMETHOD=GET\nRESOURCE=/sensors/temperature\nEXPECTED_CODE=2.05\nDESCRIPTION=Query current temperature reading\n"
      }
    },
    "monitoring": {
      "sensor_monitor": {
        "status": "SUCCESS",
        "log": "[CoAP Monitor] Listening on 0.0.0.0:5683\n[CoAP Monitor] Captured request: GET /sensors/temperature\n[CoAP Monitor] Captured response: 2.05 Content (22.5 °C)\n[CoAP Monitor] Observation complete: 1 message(s) captured\n"
      }
    },
    "actions": {
      "action_start": {
        "status": "SUCCESS",
        "log": "Sending CoAP query for case 0\n"
      },
      "send_device_query": {
        "status": "SUCCESS",
        "log": "[CoAP Send] Sent request via sensor_monitor\n[CoAP Send] Response received: 2.05 Content\n"
      }
    },
    "checks": {
      "check_start": {
        "status": "SUCCESS",
        "log": "=== Analysing CoAP responses for case 0 ===\n"
      },
      "display_captured_traffic": {
        "status": "SUCCESS",
        "log": "Captured CoAP traffic for case 0 (see monitoring result in JSON)\n"
      },
      "verify_device_reachable": {
        "status": "SUCCESS",
        "log": ""
      },
      "case_complete": {
        "status": "SUCCESS",
        "log": "=== CoAP test case 0 complete ===\n"
      }
    }
  }
}
```

### What to Look For

In the `monitoring.results.sensor_monitor` section, look for:

- **Captured request/response pairs** — confirms the CoAP exchange happened.
- **Status codes** — `2.05 Content` for successful GET, `2.04 Changed` for successful PUT.
- **Number of captured messages** — indicates whether the device responded.

In the `actions.results.send_device_query` section, check:

- **Status** — `SUCCESS` means a response was received, `FAILURE` means no response.
- **Response details** — the response code and payload.

## Step 6: Advanced CoAP Experiment — Multiple Messages with Response Matching

For more sophisticated testing, you can send multiple CoAP messages within a single case and analyse the responses. Here is an extended configuration that sends both a GET and a POST in sequence:

```toml
# =============================================================================
# Advanced CoAP Experiment — Multiple Messages
# =============================================================================

[delays]
between_cases = 1.0
before_actions = 1.0

[[setups]]
type = "echo"
name = "start_case"
[setups.args]
message = "=== Multi-message CoAP test case $EMTORCH_CASE_ID ==="

# Parse and display the query plan from the data file
[[setups]]
type = "shell"
name = "display_plan"
[setups.args]
cmd = "echo 'Query plan:' && cat $EMTORCH_DATA_PATH"
timeout = 3

# --- Monitoring: Listen for CoAP traffic ---
[[monitoring]]
type = "coap-monitor"
name = "device_monitor"
[monitoring.args]
address = "0.0.0.0:5683"
observation_timeout = 30.0

# --- Actions: Send multiple CoAP messages ---
[[actions]]
type = "echo"
name = "step1"
[actions.args]
message = "Step 1: Reading sensor temperature"

[[actions]]
type = "coap-send"
name = "query_temperature"
[actions.args]
monitor = "device_monitor"
response_timeout = 5.0

[[actions]]
type = "echo"
name = "step2"
[actions.args]
message = "Step 2: Reading sensor humidity"

[[actions]]
type = "coap-send"
name = "query_humidity"
[actions.args]
monitor = "device_monitor"
response_timeout = 5.0

[[actions]]
type = "echo"
name = "step3"
[actions.args]
message = "Step 3: Configuring reporting interval"

[[actions]]
type = "coap-send"
name = "set_interval"
[actions.args]
monitor = "device_monitor"
response_timeout = 5.0

# --- Checks: Verification ---
[[checks]]
type = "ping-alive"
name = "device_alive"
[checks.args]
host = "192.168.1.50"
timeout = 5
interval = 100

[[checks]]
type = "echo"
name = "test_complete"
[checks.args]
message = "=== Multi-message CoAP test case $EMTORCH_CASE_ID complete ==="
```

This configuration:

- Sends three CoAP messages in sequence: two GET requests (temperature, humidity) and one PUT request (set reporting interval).
- Each `coap-send` uses the same `device_monitor`, sharing the same UDP socket.
- The monitor captures all three request/response exchanges.
- The `observation_timeout` is increased to 30 seconds to accommodate the longer action sequence.

### What to Expect

The monitoring result will contain multiple captured exchanges:

```
[CoAP Monitor] Captured request: GET /sensors/temperature
[CoAP Monitor] Captured response: 2.05 Content (22.5 °C)
[CoAP Monitor] Captured request: GET /sensors/humidity
[CoAP Monitor] Captured response: 2.05 Content (60 %)
[CoAP Monitor] Captured request: PUT /config/report_interval
[CoAP Monitor] Captured response: 2.04 Changed
[CoAP Monitor] Observation complete: 3 message(s) captured
```

## Using a CoAP Simulator for Testing

If you do not have a physical CoAP device, you can use a simulator. Here is a simple Python CoAP server for testing:

```python
# coap_test_server.py — Simple CoAP test server
# Requires: pip install aiocoap
import asyncio
import aiocoap.resource as resource
import aiocoap

class TemperatureResource(resource.Resource):
    async def render_get(self, request):
        import random
        temp = 20.0 + random.uniform(-5, 15)
        payload = f"{temp:.1f}".encode()
        return aiocoap.Message(payload=payload, code=aiocoap.CONTENT)

class HumidityResource(resource.Resource):
    async def render_get(self, request):
        import random
        humidity = 40 + random.uniform(-10, 30)
        payload = f"{humidity:.0f}".encode()
        return aiocoap.Message(payload=payload, code=aiocoap.CONTENT)

async def main():
    root = resource.Site()
    root.add_resource(['sensors', 'temperature'], TemperatureResource())
    root.add_resource(['sensors', 'humidity'], HumidityResource())
    await aiocoap.Context.create_server_context(bind=('0.0.0.0', 5683), site=root)
    print("CoAP test server running on 0.0.0.0:5683")
    print("Resources: /sensors/temperature, /sensors/humidity")
    await asyncio.get_running_loop().create_future()

if __name__ == "__main__":
    asyncio.run(main())
```

Run the simulator in a separate terminal:

```bash
pip install aiocoap
python3 coap_test_server.py
```

Then test it manually with `coap-client`:

```bash
# Install coap-client (Ubuntu/Debian)
sudo apt-get install libcoap3

# Test GET request
coap-client -m get coap://127.0.0.1:5683/sensors/temperature
```

With the simulator running locally, update your `coap-experiment.toml` to point to `127.0.0.1`:

```toml
coap_host = "127.0.0.1"
coap_port = 5683
listen_address = "0.0.0.0:5683"
```

Now the experiment can run entirely on your local machine.

> **Note:** When running both the CoAP server and emtorch on the same machine, ensure the port 5683 is not already in use. If the server is on a different machine, use that machine's IP address in `coap_host`.

## Complete Configuration

Here is the complete `coap-experiment.toml` for the basic tutorial scenario:

```toml
[delays]
between_cases = 1.0
before_actions = 1.0

[[setups]]
type = "echo"
name = "announce_case"
[setups.args]
message = "=== CoAP Test Case $EMTORCH_CASE_ID — $EMTORCH_DATA_FILENAME ==="

[[setups]]
type = "shell"
name = "show_query_details"
[setups.args]
cmd = "echo 'Query definition:' && cat $EMTORCH_DATA_PATH"
timeout = 3

[[monitoring]]
type = "coap-monitor"
name = "sensor_monitor"
[monitoring.args]
address = "0.0.0.0:5683"
observation_timeout = 15.0

[[actions]]
type = "echo"
name = "action_start"
[actions.args]
message = "Sending CoAP query for case $EMTORCH_CASE_ID"

[[actions]]
type = "coap-send"
name = "send_device_query"
[actions.args]
monitor = "sensor_monitor"
response_timeout = 5.0

[[checks]]
type = "echo"
name = "check_start"
[checks.args]
message = "=== Analysing CoAP responses for case $EMTORCH_CASE_ID ==="

[[checks]]
type = "shell"
name = "display_captured_traffic"
[checks.args]
cmd = "echo 'Captured CoAP traffic for case $EMTORCH_CASE_ID (see monitoring result in JSON)'"
timeout = 3

[[checks]]
type = "ping-alive"
name = "verify_device_reachable"
[checks.args]
host = "192.168.1.50"
timeout = 5
interval = 100

[[checks]]
type = "echo"
name = "case_complete"
[checks.args]
message = "=== CoAP test case $EMTORCH_CASE_ID complete ==="
```

## Running the Tutorial

```bash
# 1. Create project structure
mkdir -p ~/emtorch-coap-tutorial/queries
cd ~/emtorch-coap-tutorial

# 2. Create query definition files
cat > queries/get_temperature.txt << 'EOF'
METHOD=GET
RESOURCE=/sensors/temperature
EXPECTED_CODE=2.05
DESCRIPTION=Query current temperature reading
EOF

cat > queries/get_humidity.txt << 'EOF'
METHOD=GET
RESOURCE=/sensors/humidity
EXPECTED_CODE=2.05
DESCRIPTION=Query current humidity reading
EOF

cat > queries/set_interval.txt << 'EOF'
METHOD=PUT
RESOURCE=/config/report_interval
PAYLOAD=30
EXPECTED_CODE=2.04
DESCRIPTION=Set reporting interval to 30 seconds
EOF

# 3. Save the configuration as coap-experiment.toml (from Complete Configuration)
#    Update the coap_host and listen_address for your setup

# 4. (Optional) Start a CoAP simulator in another terminal:
#    python3 coap_test_server.py

# 5. Run the experiment
python3 -m emtorch run queries/*.txt -c coap-experiment.toml -o coap_results_

# 6. View results
cat coap_results_0.json
cat coap_results_1.json
cat coap_results_2.json
```

## Expected Output

When a CoAP device is reachable and responds, the console output shows:

```
[INFO] Loaded configuration from coap-experiment.toml
[INFO] Created 3 cases
[INFO] Starting case 0 (get_temperature.txt)
[INFO] Setups phase: SUCCESS
[INFO] Monitoring phase started
[INFO] Actions phase: SUCCESS
[INFO] Monitoring phase stopped
[INFO] Checks phase: SUCCESS
[INFO] Case 0 complete: SUCCESS
[INFO] Starting case 1 (get_humidity.txt)
[INFO] Setups phase: SUCCESS
[INFO] Monitoring phase started
[INFO] Actions phase: SUCCESS
[INFO] Monitoring phase stopped
[INFO] Checks phase: SUCCESS
[INFO] Case 1 complete: SUCCESS
[INFO] Starting case 2 (set_interval.txt)
[INFO] Setups phase: SUCCESS
[INFO] Monitoring phase started
[INFO] Actions phase: SUCCESS
[INFO] Monitoring phase stopped
[INFO] Checks phase: SUCCESS
[INFO] Case 2 complete: SUCCESS
[INFO] All cases complete. 3/3 succeeded.
[INFO] Results written to coap_results_*.json
```

If no CoAP device is reachable, the `coap-send` subtask returns `FAILURE`:

```
[INFO] Case 0 results: actions.send_device_query = FAILURE (no response)
```

The monitoring log will show that no CoAP messages were captured:

```json
"sensor_monitor": {
  "status": "FAILURE",
  "log": "[CoAP Monitor] Listening on 0.0.0.0:5683\n[CoAP Monitor] No messages received within observation timeout\n"
}
```

## Troubleshooting

### "Address already in use"

The CoAP port (5683) is already occupied by another process.

**Solutions:**
- Find and stop the other process: `sudo lsof -i :5683`
- Use a different port: change `address` to `"0.0.0.0:5684"` and configure your device accordingly.
- If running a CoAP server on the same machine, use a different port for the server.

### "No response from device" / coap-send returns FAILURE

**Causes:**
- Device is unreachable on the network.
- Device is not running a CoAP server.
- UDP packets are blocked by a firewall.
- The response timeout is too short.

**Solutions:**
- Verify device reachability: `ping 192.168.1.50`
- Check if the CoAP port is open using `nc -u -z 192.168.1.50 5683`
- Test with a manual CoAP client: `coap-client -m get coap://192.168.1.50:5683/sensors/temperature`
- Increase `response_timeout` in `coap-send.args`.
- Ensure the device is configured to send responses to your machine's IP address.

### Monitor fails to capture messages

**Causes:**
- The monitor's `address` does not match the network interface the device is sending to.
- The `observation_timeout` is too short for the device's response time.
- The device sends responses to a different port than the monitor is listening on.

**Solutions:**
- Use `address = "0.0.0.0:5683"` to listen on all interfaces.
- Increase `observation_timeout`.
- Verify the device's destination IP and port configuration.

### "Permission denied" when binding to port 5683

On Unix systems, binding to ports below 1024 requires root privileges.

**Solutions:**
- Run emtorch with `sudo` (not recommended for production).
- Use a port above 1024 (e.g., `56830`) and configure your device accordingly.
- Grant the `CAP_NET_BIND_SERVICE` capability: `sudo setcap cap_net_bind_service=+ep $(which python3.14)`

### Firewall blocking UDP traffic

Ensure UDP traffic on the CoAP port is allowed through the firewall:

```bash
# Check firewall rules
sudo ufw status

# Allow CoAP port (if using ufw)
sudo ufw allow 5683/udp

# Or with iptables
sudo iptables -A INPUT -p udp --dport 5683 -j ACCEPT
```

### CoAP monitor shows "Observation complete: 0 message(s) captured"

The monitor started and stopped but did not see any CoAP traffic.

**Solutions:**
- Make sure the device is actually sending CoAP messages to your monitor's address and port.
- If the device uses observe (subscription) mode, verify it is configured to send notifications.
- Use a network sniffer (tcpdump, Wireshark) to verify CoAP packets are arriving:

```bash
sudo tcpdump -i any port 5683 -X
```

## Next Steps

Now that you can work with CoAP devices, explore these related topics:

| Topic | Resource |
|-------|----------|
| **CoAP monitor details** | [coap-monitor subtask](../subtasks/coap-monitor.md) |
| **CoAP send details** | [coap-send subtask](../subtasks/coap-send.md) |
| **Remote device testing** | [Remote Testing with SSH](./remote-testing.md) |
| **Data extraction from logs** | [Data Collection with Log Matching](./log-collection.md) |
| **Background monitoring patterns** | [Core Concepts - Monitoring Phase](../core-concepts.md#2-monitoring) |

## Key Takeaways

- **`coap-monitor` listens for CoAP messages** on a UDP socket during the monitoring phase, running in the background while actions execute.
- **`coap-send` sends CoAP messages** through an active monitor and waits for a response. It references the monitor by name.
- **The monitor must start before `coap-send`**, which is why monitors are placed in the `monitoring` phase and `coap-send` in the `actions` phase.
- **CoAP runs over UDP** — messages are best-effort. Set appropriate timeouts and plan for message loss in your experiments.
- **The monitor address should be `0.0.0.0:port`** to listen on all interfaces unless you need to bind to a specific IP.
- **Use the same monitor for multiple `coap-send` calls** to capture a sequence of CoAP exchanges in a single observation window.
- **Test manually first** with `coap-client` before automating with emtorch to isolate device vs. configuration issues.
- **Port 5683 is the standard CoAP port** but you can use any available UDP port.
