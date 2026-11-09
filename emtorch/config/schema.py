# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module generating JSON Schema of the experiment configuration,
usable by editors (e.g. Taplo, Tombi) for TOML completion and validation.
"""

import inspect
import logging
from typing import Any, cast

from pydantic import TypeAdapter

from ..case import Case
from ..subtasks import SubTaskInstance, SubTasksLibrary

logger = logging.getLogger(__name__)

# Draft 7 is the most widely supported one among TOML editor plugins
DIALECT = "http://json-schema.org/draft-07/schema#"

SUBTASK_REF = "#/definitions/subtask"

# keywords holding values, not schemas - left untouched
_VALUE_KEYWORDS = frozenset({"const", "default", "enum", "examples"})
# keywords holding mappings of names to schemas
_NAMED_SCHEMAS_KEYWORDS = frozenset({"properties", "patternProperties", "$defs"})


def _inline_refs(schema: dict[str, Any]) -> dict[str, Any]:
    defs = schema.pop("$defs", {})

    def resolve(node: Any, visited: frozenset[str]) -> Any:
        if isinstance(node, list):
            return [resolve(n, visited) for n in node]
        if not isinstance(node, dict):
            return node
        if "$ref" not in node:
            return {k: resolve(v, visited) for k, v in node.items()}
        name = node["$ref"].removeprefix("#/$defs/")
        if name in visited:
            raise ValueError(f"Recursive configuration type '{name}'")
        rest = {k: v for k, v in node.items() if k != "$ref"}
        return resolve(defs[name], visited | {name}) | resolve(rest, visited)

    return cast(dict[str, Any], resolve(schema, frozenset()))


_NULL = {"type": "null"}


def _without_null(node: dict[str, Any]) -> dict[str, Any]:
    if node.get("default", ...) is None:
        node = {k: v for k, v in node.items() if k != "default"}
    alternatives = node.get("anyOf")
    if not alternatives or _NULL not in alternatives:
        return node
    alternatives = [a for a in alternatives if a != _NULL]
    rest = {k: v for k, v in node.items() if k != "anyOf"}
    if len(alternatives) == 1:
        return cast(dict[str, Any], alternatives[0]) | rest
    return rest | {"anyOf": alternatives}


def _clean(node: Any) -> Any:
    if isinstance(node, list):
        return [_clean(n) for n in node]
    if not isinstance(node, dict):
        return node

    result: dict[str, Any] = {}
    for key, value in _without_null(node).items():
        if key == "title":
            continue
        if key in _VALUE_KEYWORDS:
            result[key] = value
        elif key in _NAMED_SCHEMAS_KEYWORDS:
            result[key] = {name: _clean(s) for name, s in value.items()}
        else:
            result[key] = _clean(value)
    if "properties" in result:
        result.setdefault("additionalProperties", False)
    return result


def _type_schema(config_type: Any) -> dict[str, Any]:
    return dict(_clean(_inline_refs(TypeAdapter(config_type).json_schema())))


def _subtask_branch(library: SubTasksLibrary, name: str) -> dict[str, Any]:
    # pylint: disable=broad-exception-caught
    try:
        subtask, config = library.get(name)
        then = _type_schema(config)
    except Exception as ex:
        logger.warning(f"Sub-task '{name}' arguments left unchecked: {ex}")
        return {}

    if "properties" in then:
        # keys handled by the sub-task instance are described in the base schema
        reserved = {key: True for key in sorted(SubTaskInstance.RESERVED_KEYS)}
        then["properties"] = then["properties"] | reserved
    if doc := inspect.getdoc(subtask):
        then["description"] = doc

    return {
        "if": {"properties": {"type": {"const": name}}, "required": ["type"]},
        "then": then,
    }


def _subtask_schema(library: SubTasksLibrary) -> dict[str, Any]:
    names = sorted(library.names())
    schema = _type_schema(SubTaskInstance.Config)
    # sub-task arguments are allowed, as defined by the 'type' specific branch
    del schema["additionalProperties"]
    schema["properties"]["type"]["enum"] = names
    schema["allOf"] = [
        branch for name in names if (branch := _subtask_branch(library, name))
    ]
    return schema


def build_schema(library: SubTasksLibrary) -> dict[str, Any]:
    schema = _type_schema(Case.Config)
    name_pattern = f"^{SubTaskInstance.NAME_PATTERN.pattern}$"
    for key in Case.Config.subtasks_keys():
        schema["properties"][key] = schema["properties"][key] | {
            "type": "object",
            "propertyNames": {"pattern": name_pattern},
            "additionalProperties": {"$ref": SUBTASK_REF},
        }

    return (
        {
            "$schema": DIALECT,
            "title": "emtorch experiment configuration",
        }
        | schema
        | {"definitions": {"subtask": _subtask_schema(library)}}
    )
