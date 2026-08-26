<!--
Copyright (c) 2025-2026 Warsaw University of Technology
This file is licensed under the MIT License.
See the LICENSE.txt file in the root of the repository for full details.
-->

# Subtask: coap-send

## Description
Sends experiment data as a CoAP (Constrained Application Protocol) message to a device and waits for a response. This subtask works in conjunction with a `coap-monitor` subtask, using it as a communication endpoint. It is used to send commands, configuration data, or queries to CoAP-enabled IoT devices and await their replies.

## Use Cases
- Sending configuration commands to IoT devices
- Querying sensor values from CoAP-enabled devices
- Triggering actions on remote constrained devices
- Requesting device status information
- Implementing request-response patterns in IoT experiments

## Configuration Arguments

### Required Arguments
- **monitor** (string): Name of a `coap-monitor` subtask that provides the communication channel for sending the message.
- **response_timeout** (float): Maximum time in seconds to wait for a CoAP response from the device.

### Optional Arguments
None.

## Result
Returns SUCCESS if a CoAP response is received within the timeout period. Returns FAILURE if no response is received or the communication fails.

## Example Configuration

```toml
[[monitoring]]
type = "coap-monitor"
name = "sensor_monitor"

[monitoring.args]
address = "0.0.0.0:5683"
observation_timeout = 60.0

[[actions]]
type = "coap-send"
name = "query_sensor"

[actions.args]
monitor = "sensor_monitor"
response_timeout = 5.0
```

```toml
[[monitoring]]
type = "coap-monitor"
name = "device_listener"

[monitoring.args]
address = "192.168.1.100:5683"
observation_timeout = 30.0

[[actions]]
type = "coap-send"
name = "send_command"

[actions.args]
monitor = "device_listener"
response_timeout = 10.0
```

## Notes
- This subtask requires a running `coap-monitor` instance to handle the communication channel.
- The monitor subtask must be defined in the same experiment configuration and typically runs in a `monitoring` phase.
- The response timeout should be set appropriately based on expected device response times and network latency.
- CoAP is an UDP-based protocol; message delivery is best-effort and may require retransmission at the application level.
- For monitoring unsolicited CoAP messages (notifications, observations), use `coap-monitor` alone.

## See Also
- [coap-monitor](./coap-monitor.md) — Monitor incoming CoAP messages
