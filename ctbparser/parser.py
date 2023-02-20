# -*- coding: utf-8 -*-

from __future__ import annotations

import io
import logging
from collections.abc import Iterable
from itertools import tee
from pprint import pformat, pprint
from typing import Any

import pyparsing
from pyparsing import (
    Combine,
    Dict,
    Forward,
    Group,
    LineEnd,
    Literal,
    Opt,
    StringEnd,
    Suppress,
    Word,
    ZeroOrMore,
    alphas,
    alphanums,
    common,
    delimited_list,
    nums,
    rest_of_line,
)

log = logging.getLogger(__name__)

pyparsing.enable_all_warnings()

LiteralEquals = Suppress(Literal("="))
LiteralTrue = Literal("TRUE")
LiteralFalse = Literal("FALSE")
LiteralBlockStart = Suppress(Literal("{"))
LiteralBlockEnd = Suppress(Literal("}"))
LiteralParenOpen = Suppress(Literal("("))
LiteralParenClose = Suppress(Literal(")"))
LiteralQuote = Suppress(Literal('"'))
LiteralNUL = Literal("\x00")
LiteralEOL = Suppress(LineEnd())
String = LiteralQuote + rest_of_line
Integer = common.signed_integer
Float = common.real + Opt(Suppress(rest_of_line)("trailer"))
Number = Float ^ Integer
ItemKey = Word(alphanums + "_")
ItemValue = LiteralTrue | LiteralFalse | Number | String
Item = Group(ItemKey + LiteralEquals + ItemValue + LiteralEOL)
NestedBlock = Forward()
Block = Group(
    ItemKey
    + LiteralBlockStart
    + LiteralEOL
    + (Group(Dict(ZeroOrMore(Item))) ^ Group(Dict(ZeroOrMore(NestedBlock))))
    + LiteralBlockEnd
    + LiteralEOL
)
NestedBlock <<= Block
CtbStructure = (Item | Block)[...] | StringEnd()


@LiteralTrue.set_parse_action
def resolve_true(results: pyparsing.ParseResults):
    return True


@LiteralFalse.set_parse_action
def resolve_false(results: pyparsing.ParseResults):
    return False


CtbStructure.validate()


def parse(indata: bytes) -> ...:
    indata = indata.decode("utf-8")
    if indata.endswith("\x00"):
        indata = indata[:-1]

    result = CtbStructure.parse_string(indata, parse_all=True).as_list()
    log.debug(f"parsed data: {pformat(result)}")
    return to_dict(result)


def _is_list_pair(item: Any) -> bool:
    if isinstance(item, (list, tuple)) and len(item) == 2:
        return True

    return False


def _is_list_of_list_pairs(item: Any) -> bool:
    if isinstance(item, (list, tuple)):
        if all([_is_list_pair(subitem) for subitem in item]):
            return True

    return False


def pairwise(iterable):
    # pairwise('ABCDEFG') --> AB BC CD DE EF FG
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def to_dict(obj: Any) -> dict:
    out = {}
    if isinstance(
        obj,
        (
            str,
            bytes,
            int,
            float,
            bool,
        ),
    ):
        return obj

    if _is_list_pair(obj):
        log.debug(f"converting obj pairwise: {obj}")
        obj = pairwise(obj)

    for item in obj:
        if _is_list_of_list_pairs(item):
            log.debug(f"item converts directly to dict: {item}")
            return dict(item)
        elif _is_list_pair(item):
            key, value = item
            if _is_list_of_list_pairs(value) or _is_list_pair(value):
                log.debug(f"recursively converting: {item}")
                out[key] = to_dict(value)
            else:
                log.debug(f"passing through {key} => {value}")
                out[key] = value
        elif isinstance(item, (list, tuple)):
            log.debug(f"recursively converting sequence: {item}")
            out[key] = to_dict(item)
        else:
            raise ValueError(f"Unhandled value {item}")

    return out
