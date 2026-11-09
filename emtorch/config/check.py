# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module validating experiment configuration without executing it.
"""

from typing import Any

from pydantic import ValidationError

from ..case import Case
from ..subtasks import SubTaskFactoryCache, SubTaskInstance, SubTaskNameError
from .loader import ConfigLoader


def _format_validation_error(prefix: str | None, error: ValidationError) -> list[str]:
    result = []
    for e in error.errors():
        parts = e["loc"] if prefix is None else (prefix, *e["loc"])
        location = ".".join(str(part) if part != "" else '""' for part in parts)
        result.append(f"{location}: {e['msg']}")
    return result


def _format_exception(location: str, error: Exception) -> str:
    message = str(error) or "unexpected error"
    return f"{location}: {message} [{type(error).__name__}]"


class _SubTaskValidator:
    def __init__(
        self,
        loader: ConfigLoader,
        factories: SubTaskFactoryCache,
        subtasks_key: str,
        name: str,
    ):
        self._loader = loader
        self._factories = factories
        self._subtasks_key = subtasks_key
        self._name = name
        self._errors: list[str] = []
        self._fullname = ""

    def validate(self, table: dict[str, Any]) -> list[str]:
        self._fullname = self._check_name()
        instance, args = SubTaskInstance.separate_args(table)
        type_name = self._check_instance_config(instance)
        if type_name is not None:
            factory = self._find_factory(type_name)
            if factory is not None:
                self._check_construction(factory, args)
        return self._errors

    def _check_name(self) -> str:
        try:
            return SubTaskInstance.check_name(self._subtasks_key, self._name)
        except SubTaskNameError as ex:
            self._errors.append(f"{ex.location}: invalid sub-task name, {ex.reason}")
            return ex.location

    def _check_instance_config(self, instance: dict[str, Any]) -> str | None:
        try:
            return self._loader.from_dict(SubTaskInstance.Config, instance).type
        except ValidationError as ex:
            self._errors += _format_validation_error(self._fullname, ex)
        type_name = instance.get("type")
        return type_name if isinstance(type_name, str) else None

    def _find_factory(self, type_name: str) -> SubTaskFactoryCache.Factory | None:
        # pylint: disable=broad-exception-caught
        try:
            return self._factories.get(type_name)
        except KeyError as ex:
            # unknown sub-task type
            reason = ex.args[0] if ex.args else ex
            self._errors.append(f"{self._fullname}.type: {reason}")
        except Exception as ex:
            self._errors.append(_format_exception(f"{self._fullname}.type", ex))
        return None

    def _check_construction(
        self, factory: SubTaskFactoryCache.Factory, args: dict[str, Any]
    ) -> None:
        # pylint: disable=broad-exception-caught
        try:
            factory(args)
        except ValidationError as ex:
            self._errors += _format_validation_error(self._fullname, ex)
        except Exception as ex:
            self._errors.append(_format_exception(self._fullname, ex))


def validate_config(raw: dict[str, Any], loader: ConfigLoader) -> list[str]:
    errors: list[str] = []
    try:
        loader.from_dict(Case.Config, raw)
    except ValidationError as ex:
        errors += _format_validation_error(None, ex)

    factories = SubTaskFactoryCache(loader)
    for subtasks_key in Case.Config.subtasks_keys():
        subtasks = raw.get(subtasks_key, {})
        if not isinstance(subtasks, dict):
            continue
        for name, table in subtasks.items():
            if isinstance(table, dict):
                validator = _SubTaskValidator(loader, factories, subtasks_key, name)
                errors += validator.validate(table)
    return errors
