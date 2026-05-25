#!/usr/bin/env python3
# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module containing utilities for generating configuration documentation.
"""

import string
from dataclasses import dataclass
from typing import (
    Annotated,
    Any,
    Iterator,
    Union,
    cast,
    get_args,
    get_origin,
    get_type_hints,
)

import fieldz

from . import Doc
from .net import NetworkAddress
from .signal import Signal
from .ssh import ConnectionConfig


def __iter_fields(cls: Any) -> Iterator[tuple[fieldz.Field[Any], Any]]:
    hints = get_type_hints(cls, include_extras=True)

    for f in fieldz.fields(cls):
        annotation = hints.get(f.name, f.type)
        yield f, annotation


@dataclass(frozen=True, kw_only=True)
class FieldDescription:
    name: str
    typename: str
    description: str
    defaultvalue: str | None


def __extract_annotated_description(annotation: Any) -> str | None:
    _, *meta = get_args(annotation)
    for m in meta:
        if isinstance(m, Doc):
            return m.text
    return None


def __extract_native_description(native_field: Any) -> str | None:
    if hasattr(native_field, "description"):
        if native_field.description:
            return cast(str, native_field.description)
    return None


def __extract_description(field: fieldz.Field[Any], annotation: Any) -> str:
    if get_origin(annotation) is Annotated:
        if description := __extract_annotated_description(annotation):
            return description
    if description := __extract_native_description(field.native_field):
        return description

    return ""


def __extract_default(field: fieldz.Field[Any]) -> str | None:
    if field.default != fieldz.Field.MISSING:
        return str(field.default)
    return None


# pylint: disable=too-many-return-statements,too-many-branches
def __name_of_type(t: type[Any] | str | Any) -> str:
    origin = get_origin(t)
    args = get_args(t)

    if origin is list:
        if args:
            return f"list of {__name_of_type(args[0])}"
        return "list"

    if origin is Union:
        if args and args[0] is Signal:
            return "string"

    match t:
        case str():
            return t  # already string literal

        case _ if t is int:
            return "int"

        case _ if t is float:
            return "float"

        case _ if t is bool:
            return "boolean"

        case _ if t is str:
            return "string"

        case _ if t is list:
            return "list"

        case _ if isinstance(t, type) and issubclass(t, string.Template):
            return "$-string"

        case _ if t is NetworkAddress:
            return "host: string, port: int"

        case _ if t is ConnectionConfig:
            return "host: string, port: int (22), username: string, password: string"

        case _:
            pass

    return getattr(t, "__name__", str(t))


def __extract_type(field: fieldz.Field[Any]) -> str:
    return __name_of_type(field.type)


def fields_descriptions(clazz: Any) -> Iterator[FieldDescription]:
    for field, annotation in __iter_fields(clazz):
        yield FieldDescription(
            name=field.name,
            typename=__extract_type(field),
            description=__extract_description(field, annotation),
            defaultvalue=__extract_default(field),
        )
