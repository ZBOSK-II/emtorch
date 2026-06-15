<!--
Copyright (c) 2025-2026 Warsaw University of Technology
This file is licensed under the MIT License.
See the LICENSE.txt file in the root of the repository for full details.
-->

# Developer Guide

Learn how to extend emtorch by creating custom subtasks and contributing to the project.

## Overview

emtorch is designed to be extensible. You can:

- **Create custom subtasks** for operations not covered by built-in subtasks
- **Register subtasks** as Python entry points so they work like built-in subtasks
- **Contribute** your subtasks back to the project

This guide walks through creating a custom subtask from scratch.

## Architecture Overview

### Package Structure

```
emtorch/
├── __init__.py          # Main execute() and run() functions
├── __main__.py          # CLI entry point
├── arguments.py         # Argument dataclass
├── cli/                 # CLI command implementations
├── case/                # Case execution logic
├── config/              # Configuration handling
├── context/             # Runtime context
├── results/             # Result classes
└── subtasks/            # Subtask implementations
    ├── __init__.py      # Base classes (SubTask, BasicSubTask, etc.)
    ├── echo.py
    ├── subprocess.py    # Shell, Exec
    ├── ping.py          # PingIsAlive, PingIsStable
    └── ...
```

### Subtask Plugin System

Subtasks are registered as Python entry points in `pyproject.toml`:

```toml
[project.entry-points."emtorch.subtasks"]
my-subtask = "mypackage.subtasks:MySubTask"
```

This allows emtorch to discover and load subtasks dynamically without modifying core code.

## Creating a Custom Subtask

### Step 1: Understand the Base Classes

All subtasks inherit from `SubTask` or one of its subclasses.

#### BasicSubTask (Most Common)

For operations that return SUCCESS/FAILURE/ERROR/TIMEOUT:

```python
from emtorch.subtasks import BasicSubTask, SubTaskContext
from emtorch.results.basic import BasicResult

class MySubTask(BasicSubTask):
    """Description of what your subtask does."""
    
    async def execute(self, context: SubTaskContext) -> BasicResult:
        # Your implementation here
        return self.Result.SUCCESS
```

#### TypedSubTask (Advanced)

For operations that return custom result types:

```python
from enum import StrEnum
from emtorch.subtasks import TypedSubTask, SubTaskContext

class MyResult(StrEnum):
    SUCCESS = "success"
    SPECIAL_FAILURE = "special_failure"

class MySubTask(TypedSubTask[MyResult]):
    @property
    def result_type(self) -> type[MyResult]:
        return MyResult
    
    async def execute(self, context: SubTaskContext) -> MyResult:
        # Your implementation
        return MyResult.SUCCESS
```

### Step 2: Define Configuration

Use the `@configclass` decorator to define configuration parameters:

```python
from typing import Annotated
from emtorch.config import configclass, Doc
from emtorch.context.template import Template

@configclass
class Config:
    message: Annotated[Template, Doc("message to display")]
    timeout: Annotated[float, Doc("timeout in seconds")] = 5.0
    count: Annotated[int, Doc("number of times")] = 1
```

**Key points:**
- Use `Annotated` for type hints with documentation
- Use `Doc()` to provide parameter descriptions
- Use `Template` for values that should support $-variables
- Provide sensible defaults for optional parameters

### Step 3: Implement the Execute Method

The `execute()` method is where your subtask logic runs:

```python
async def execute(self, context: SubTaskContext) -> BasicResult:
    # Access configuration
    message = self._config.message.evaluate(context.parent)
    
    # Log information
    context.logger.info(f"Processing: {message}")
    
    # Do work (can be async)
    result = await do_something()
    
    # Return result
    if result:
        return self.Result.SUCCESS
    else:
        return self.Result.FAILURE
```

**Available in `SubTaskContext`:**
- `logger` — LoggerAdapter for logging output
- `parent` — CaseContext with case information
  - Access `parent.data_registry` for case ID, file path, etc.

### Step 4: Complete Example Subtask

Here's a complete example of a simple custom subtask:

```python
# Copyright (c) 2025-2026 Your Organization
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module containing custom counter subtask.
"""

from typing import Annotated

from emtorch.config import Doc, configclass
from emtorch.context.template import Template
from emtorch.subtasks import BasicSubTask, SubTaskContext


class Counter(BasicSubTask):
    """
    Counts from 1 to N and logs each number.
    
    Useful for testing iteration and logging.
    """

    @configclass
    class Config:
        count: Annotated[int, Doc("number of items to count")]
        prefix: Annotated[Template, Doc("prefix for each message")] = Template("Item")

    def __init__(self, config: Config):
        self._config = config

    async def execute(self, context: SubTaskContext) -> BasicSubTask.Result:
        prefix = self._config.prefix.evaluate(context.parent)
        
        try:
            for i in range(1, self._config.count + 1):
                context.logger.info(f"{prefix} {i}")
            return self.Result.SUCCESS
        except Exception as e:
            context.logger.error(f"Error during counting: {e}")
            return self.Result.ERROR
```

### Step 5: Register Your Subtask

Register your subtask as an entry point in `pyproject.toml`:

```toml
[project.entry-points."emtorch.subtasks"]
counter = "mypackage.subtasks:Counter"
```

Then reinstall the package:

```bash
pip install -e .
# or
poetry install
```

### Step 6: Use Your Subtask

After registration, use it in configurations:

```toml
[[actions]]
type = "counter"
name = "count_items"

[actions.args]
count = 5
prefix = "Processing case $EMTORCH_CASE_ID - Item"
```

## Handling Async Operations

emtorch uses asyncio for concurrent execution. Your subtask's `execute()` method can be async:

```python
async def execute(self, context: SubTaskContext) -> BasicResult:
    # Async operations work directly
    result = await some_async_function()
    
    # You can also use asyncio.sleep
    await asyncio.sleep(1)
    
    return self.Result.SUCCESS
```

## Error Handling

Return appropriate result types based on error conditions:

```python
async def execute(self, context: SubTaskContext) -> BasicResult:
    try:
        result = do_something()
        if result:
            return self.Result.SUCCESS
        else:
            return self.Result.FAILURE  # Operation failed normally
    except TimeoutError:
        return self.Result.TIMEOUT      # Timeout occurred
    except Exception as e:
        context.logger.error(f"Unexpected error: {e}")
        return self.Result.ERROR        # Unexpected error
```

## Working with Templates

Template variables (`$EMTORCH_CASE_ID`, etc.) are handled via `Template` class:

```python
from emtorch.context.template import Template

# In config
cmd: Annotated[Template, Doc("command to execute")]

# In execute()
evaluated_cmd = self._config.cmd.evaluate(context.parent)
```

The `evaluate()` method replaces:
- `$EMTORCH_CASE_ID` — Case number
- `$EMTORCH_DATA_PATH` — Full data file path
- `$EMTORCH_DATA_FILENAME` — Data filename only

## Code Style and Standards

### Code Formatting

emtorch uses strict code standards:

**Black** (code formatting, line length 100):
```bash
black --line-length 100 myfile.py
```

**isort** (import sorting, profile=black):
```bash
isort --profile black myfile.py
```

**flake8** (linting):
```bash
flake8 myfile.py
```

**mypy** (type checking, strict mode):
```bash
mypy --strict myfile.py
```

**pylint** (additional linting):
```bash
pylint myfile.py
```

### All Subtasks Include

```python
# Copyright header
# Copyright (c) 2025-2026 Your Organization
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

# Module docstring
"""
Module containing description of functionality.
"""

# Class docstring
class MySubTask(BasicSubTask):
    """
    One-line summary.
    
    More detailed description if needed.
    """
```

## Testing Your Subtask

### Unit Testing

Create tests in a `tests/` directory:

```python
import pytest
from emtorch.subtasks import SubTaskContext
from mypackage.subtasks import Counter

@pytest.mark.asyncio
async def test_counter_success():
    config = Counter.Config(count=3, prefix="Item")
    subtask = Counter(config)
    
    # Create mock context
    context = SubTaskContext(...)  # Mock appropriately
    
    result = await subtask.execute(context)
    assert result == BasicResult.SUCCESS
```

### Integration Testing

Test in a real emtorch configuration:

```toml
[[actions]]
type = "counter"
name = "test_counter"

[actions.args]
count = 3
prefix = "Test"
```

```bash
python3 -m emtorch run test_data.bin -c test_config.toml -o test_
cat test_0.json
```

## Contributing Your Subtask

To contribute a subtask back to emtorch:

1. **Fork the repository** on GitHub
2. **Create a feature branch** with your subtask
3. **Ensure code quality**:
   - Run `black`, `isort`, `flake8`, `mypy`, `pylint`
   - Add unit tests
   - Document with docstrings and configuration descriptions
4. **Update `pyproject.toml`** with your entry point
5. **Create a Pull Request** with a clear description

## Advanced Topics

### Custom Result Types

For subtasks that need special result types:

```python
from enum import StrEnum
from emtorch.subtasks import TypedSubTask

class AnalysisResult(StrEnum):
    SUCCESS = "success"
    ANOMALY_DETECTED = "anomaly_detected"
    INCONCLUSIVE = "inconclusive"

class AnalysisSubTask(TypedSubTask[AnalysisResult]):
    @property
    def result_type(self) -> type[AnalysisResult]:
        return AnalysisResult
    
    async def execute(self, context: SubTaskContext) -> AnalysisResult:
        # Your logic
        pass
```

### Collecting Values

Subtasks can collect values during execution (e.g., metrics):

```python
# In SubTaskResults, values are stored as:
# {"metric_name": value}

# Access in logger matchers:
[[checks]]
type = "logger-float-matcher"
name = "extract_metric"

[checks.args]
subtask = "your_subtask"
pattern = "Metric: (?P<value>\\d+\\.\\d+)"
value = "metric_name"
```

## Debugging

### Enable Verbose Logging

```bash
python3 -m emtorch run data.bin -c config.toml --log-level DEBUG
```

### Inspect Context

In your `execute()` method:

```python
context.logger.debug(f"Case ID: {context.parent.case_id}")
context.logger.debug(f"Data path: {context.parent.data_path}")
context.logger.debug(f"Config: {self._config}")
```

### Test Execution

```python
# Run subtask directly for testing
import asyncio
from mypackage.subtasks import MySubTask

async def test():
    config = MySubTask.Config(...)
    subtask = MySubTask(config)
    # Create mock context or use real execution
    result = await subtask.execute(context)
    print(f"Result: {result}")

asyncio.run(test())
```

## Common Patterns

### Wrapping External Tools

```python
import subprocess

async def execute(self, context: SubTaskContext) -> BasicResult:
    try:
        result = subprocess.run(
            ["external_tool", "--option", "value"],
            capture_output=True,
            timeout=self._config.timeout,
            text=True
        )
        if result.returncode == 0:
            context.logger.info(result.stdout)
            return self.Result.SUCCESS
        else:
            context.logger.error(result.stderr)
            return self.Result.FAILURE
    except subprocess.TimeoutExpired:
        return self.Result.TIMEOUT
    except Exception as e:
        context.logger.error(f"Error: {e}")
        return self.Result.ERROR
```

### Communicating with Remote Devices

```python
import asyncssh

async def execute(self, context: SubTaskContext) -> BasicResult:
    try:
        async with asyncssh.connect(
            self._config.host,
            username=self._config.username,
            password=self._config.password,
            timeout=self._config.timeout
        ) as conn:
            result = await conn.run(self._config.cmd)
            context.logger.info(result.stdout)
            return self.Result.SUCCESS if result.exit_status == 0 else self.Result.FAILURE
    except asyncssh.Error as e:
        context.logger.error(f"SSH Error: {e}")
        return self.Result.ERROR
```

---

## Useful References

- **[Subtasks Reference](./subtasks/index.md)** — Built-in subtask documentation
- **[Configuration Guide](./configuration-guide.md)** — Configuration syntax
- **emtorch source code** — Study existing subtasks for patterns
- **Python asyncio docs** — For async/await patterns

---

Ready to create your first subtask? Start with a simple one like the `Counter` example, test it locally, and gradually add complexity!
