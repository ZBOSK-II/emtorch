# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module generating JSON Schema of the experiment configuration,
usable by editors (e.g. Taplo, Tombi) for TOML completion and validation.
"""

import inspect
import logging
from typing import Any, Iterator

from pydantic import TypeAdapter
from pydantic.json_schema import GenerateJsonSchema, JsonSchemaMode, JsonSchemaValue
from pydantic_core import core_schema

from ..case import Case
from ..subtasks import SubTask, SubTaskInstance, SubTasksLibrary

logger = logging.getLogger(__name__)

# Draft 7 is the most widely supported one among TOML editor plugins
DIALECT = "http://json-schema.org/draft-07/schema#"
REF_TEMPLATE = "#/definitions/{model}"

_MODE: JsonSchemaMode = "validation"
# keys of generated schemas - internal ones never collide with sub-task names
_CASE = ("internal", "case")
_INSTANCE = ("internal", "instance")


class _TomlJsonSchema(GenerateJsonSchema):
    def nullable_schema(self, schema: core_schema.NullableSchema) -> JsonSchemaValue:
        return self.generate_inner(schema["schema"])

    def default_schema(self, schema: core_schema.WithDefaultSchema) -> JsonSchemaValue:
        if schema.get("default", ...) is None:
            return self.generate_inner(schema["schema"])
        return super().default_schema(schema)

    def field_title_should_be_set(self, schema: Any) -> bool:
        return False

    def dataclass_schema(self, schema: core_schema.DataclassSchema) -> JsonSchemaValue:
        return self._forbid_extra(super().dataclass_schema(schema))

    def typed_dict_schema(self, schema: core_schema.TypedDictSchema) -> JsonSchemaValue:
        return self._forbid_extra(super().typed_dict_schema(schema))

    def model_schema(self, schema: core_schema.ModelSchema) -> JsonSchemaValue:
        return self._forbid_extra(super().model_schema(schema))

    @staticmethod
    def _forbid_extra(schema: JsonSchemaValue) -> JsonSchemaValue:
        schema.setdefault("additionalProperties", False)
        return schema


def _draft7_refs(node: Any) -> Any:
    if isinstance(node, list):
        return [_draft7_refs(n) for n in node]
    if not isinstance(node, dict):
        return node
    result = {k: _draft7_refs(v) for k, v in node.items()}
    if "$ref" in result and len(result) > 1:
        ref = result.pop("$ref")
        result["allOf"] = [{"$ref": ref}]
    return result


def _iter_refs(node: Any) -> Iterator[str]:
    if isinstance(node, list):
        for n in node:
            yield from _iter_refs(n)
    elif isinstance(node, dict):
        if "$ref" in node:
            yield _definition_name(node)
        for n in node.values():
            yield from _iter_refs(n)


def _used_definitions(
    root: dict[str, Any], definitions: dict[str, Any]
) -> dict[str, Any]:
    used: set[str] = set()
    pending = list(_iter_refs(root))
    while pending:
        name = pending.pop()
        if name not in used:
            used.add(name)
            pending += _iter_refs(definitions[name])
    return {name: d for name, d in definitions.items() if name in used}


def _subtask_key(name: str) -> tuple[str, str]:
    return ("subtask", name)


def _subtask_configs(
    library: SubTasksLibrary,
) -> dict[str, tuple[type[SubTask], TypeAdapter[Any]]]:
    # pylint: disable=broad-exception-caught
    result = {}
    for name in sorted(library.names()):
        try:
            subtask, config = library.get(name)
            adapter = TypeAdapter(config)
            # probe - a sub-task failing here must not break the joint generation
            adapter.json_schema(schema_generator=_TomlJsonSchema)
        except Exception as ex:
            logger.warning(f"Sub-task '{name}' arguments left unchecked: {ex}")
            continue
        result[name] = (subtask, adapter)
    return result


def _definition_name(ref: JsonSchemaValue) -> str:
    return str(ref["$ref"]).removeprefix(REF_TEMPLATE.format(model=""))


def _subtask_branch(subtask: type[SubTask], config: JsonSchemaValue) -> dict[str, Any]:
    # a copy - the definition may be referenced elsewhere, without reserved keys
    then = dict(config)
    if "properties" in then:
        reserved = {key: True for key in sorted(SubTaskInstance.RESERVED_KEYS)}
        then["properties"] = then["properties"] | reserved
    if doc := inspect.getdoc(subtask):
        then["description"] = doc
    return then


def build_schema(library: SubTasksLibrary) -> dict[str, Any]:
    configs = _subtask_configs(library)
    inputs: list[tuple[tuple[str, str], JsonSchemaMode, TypeAdapter[Any]]] = [
        (_CASE, _MODE, TypeAdapter[Any](Case.Config)),
        (_INSTANCE, _MODE, TypeAdapter[Any](SubTaskInstance.Config)),
    ] + [(_subtask_key(name), _MODE, adapter) for name, (_, adapter) in configs.items()]
    refs, schemas = TypeAdapter.json_schemas(
        inputs, ref_template=REF_TEMPLATE, schema_generator=_TomlJsonSchema
    )
    definitions: dict[str, Any] = schemas["$defs"]
    for definition in definitions.values():
        definition.pop("title", None)

    def resolve(key: tuple[str, str]) -> JsonSchemaValue:
        schema = refs[(key, _MODE)]
        return definitions[_definition_name(schema)] if "$ref" in schema else schema

    instance = resolve(_INSTANCE)
    del instance["additionalProperties"]
    # every installed type is accepted, also the ones without described arguments
    instance["properties"]["type"]["enum"] = sorted(library.names())
    instance["allOf"] = [
        {
            "if": {"properties": {"type": {"const": name}}, "required": ["type"]},
            "then": _subtask_branch(subtask, resolve(_subtask_key(name))),
        }
        for name, (subtask, _) in configs.items()
    ]

    root = {"$schema": DIALECT, "title": "emtorch experiment configuration"}
    root |= resolve(_CASE)
    return dict(
        _draft7_refs(root | {"definitions": _used_definitions(root, definitions)})
    )
