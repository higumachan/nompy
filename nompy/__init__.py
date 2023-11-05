from dataclasses import dataclass
from typing import Iterable, TypeVar, Callable, Tuple, Any, overload, TypeVarTuple


@dataclass
class ParserResult[T, V, E]:
    return_value: V | None
    error: E | None
    remain: Iterable[T]

@dataclass
class StrParserResult[V, E]:
    return_value: V | None
    error: E | None
    remain: str


@dataclass
class TagParserError:
    tag: str

@dataclass
class TupleParserError:
    pass

type StrParser[V, E] = Callable[[str], StrParserResult[V, E]]

def tag(literal: str) -> StrParser[str, TagParserError]:
    def parser(s: str) -> StrParserResult[str, TagParserError]:
        if s.startswith(literal):
            return StrParserResult(literal, None, s[len(literal):])
        else:
            return StrParserResult(None, TagParserError(literal), s)
    return parser


# @overload
# def sequence[T1, E1](parsers: Tuple[StrParser[T1, E1]]) -> StrParser[Tuple[T1], TupleParserError]:
#     ...
#
#
# @overload
# def sequence[T1, E1, T2, E2](parsers: Tuple[StrParser[T1, E1], StrParser[T2, E2]]) -> StrParser[Tuple[T1, T2], TupleParserError]:
#     ...


Ts = TypeVarTuple("Ts")
Es = TypeVarTuple("Es")

def sequence(parsers: Tuple[*StrParser[Ts, Es]]) -> StrParser[Tuple[*Ts], TupleParserError]:
    def parser(s: str) -> StrParserResult[Tuple[*Ts], TupleParserError]:
        result = []
        for p in parsers:
            r = p(s)
            if r.return_value is None:
                return StrParserResult(None, TupleParserError(), s)
            else:
                result.append(r.return_value)
                s = r.remain
        return StrParserResult(tuple[*Ts](result), None, s)
    return parser

def sequence2[T1, E1, T2, E2](parsers: Tuple[StrParser[T1, E1], StrParser[T2, E2]]) -> StrParser[Tuple[T1, T2], TupleParserError]:
    def parser(s: str) -> StrParserResult[Tuple[T1, T2], TupleParserError]:
        r1 = parsers[0](s)
        if r1.return_value is None:
            return StrParserResult(None, TupleParserError(), s)
        else:
            r2 = parsers[1](r1.remain)
            if r2.return_value is None:
                return StrParserResult(None, TupleParserError(), s)
            else:
                return StrParserResult((r1.return_value, r2.return_value), None, r2.remain)
    return parser

def sequence3[T1, E1, T2, E2, T3, E3](parsers: Tuple[StrParser[T1, E1], StrParser[T2, E2], StrParser[T3, E3]]) -> StrParser[Tuple[T1, T2, T3], TupleParserError]:
    def parser(s: str) -> StrParserResult[Tuple[T1, T2, T3], TupleParserError]:
        r1 = parsers[0](s)
        if r1.return_value is None:
            return StrParserResult(None, TupleParserError(), s)
        else:
            r2 = parsers[1](r1.remain)
            if r2.return_value is None:
                return StrParserResult(None, TupleParserError(), s)
            else:
                r3 = parsers[2](r2.remain)
                if r3.return_value is None:
                    return StrParserResult(None, TupleParserError(), s)
                else:
                    return StrParserResult((r1.return_value, r2.return_value, r3.return_value), None, r3.remain)
    return parser

@dataclass
class AltParserError:
    child_errors: list[Any]


def alt[T1, E1](parsers: Tuple[StrParser[T1, E1]]) -> StrParser[T1, E1]:
    def parser(s: str) -> StrParserResult[T1, E1]:
        errs = []
        for p in parsers:
            ret = p(s)
            if ret.return_value is not None:
                return ret
            errs.append(ret.error)
        return StrParserResult(None, AltParserError(errs), s)
    return parser


@dataclass
class ManyError:
    pass


def many0[T, E](parser: StrParser[T, E]) -> StrParser[list[T], E]:
    def new_parser(s: str) -> StrParserResult[list[T], E]:
        result = []
        while True:
            r = parser(s)
            if r.return_value is None:
                return StrParserResult(result, None, s)
            else:
                result.append(r.return_value)
                s = r.remain
    return new_parser


def many1[T, E](parser: StrParser[T, E]) -> StrParser[list[T], E]:
    def new_parser(s: str) -> StrParserResult[list[T], E]:
        start_s = s
        result = []
        while True:
            r = parser(s)
            if r.return_value is None:
                if len(result) == 1:
                    return StrParserResult(result, None, s)
                else:
                    return StrParserResult(None, ManyError(), start_s)
            else:
                result.append(r.return_value)
                s = r.remain
    return new_parser


@dataclass
class TakeWhileError:
    pass


def take_while[T, E](cond: Callable[[str], bool]) -> StrParser[str, TakeWhileError]:
    def parser(s: str) -> StrParserResult[str, TakeWhileError]:
        l = s
        result = ""
        for i in range(len(s)):
            if cond(s[i]):
                result += s[i]
            else:
                break
        return StrParserResult(result, None, s[len(result):])
    return parser

def take_while_m_n[T, E](m: int, n: int, cond: Callable[[str], bool]) -> StrParser[str, TakeWhileError]:
    def parser(s: str) -> StrParserResult[str, TakeWhileError]:
        l = s
        result = ""
        for i in range(n):
            if len(s) == 0:
                break
            elif cond(s[0]):
                result += s[0]
                s = s[1:]
            else:
                break
        if len(result) < m:
            return StrParserResult(None, TakeWhileError(), l)
        else:
            return StrParserResult(result, None, s)
    return parser


def parser_map[T1, E, T2](parser: StrParser[T1, E], f: Callable[[T1], T2]) -> StrParser[T2, E]:
    def new_parser(s: str) -> StrParserResult[T2, E]:
        r = parser(s)
        if r.return_value is None:
            return StrParserResult(None, r.error, r.remain)
        else:
            return StrParserResult(f(r.return_value), None, r.remain)
    return new_parser


@dataclass
class MapExceptionError:
    exception: Exception

def parser_map_exception[T1, E1, T2](parser: StrParser[T1, E1], f: Callable[[T1], T2]) -> StrParser[T2, MapExceptionError | E1]:
    def new_parser(s: str) -> StrParserResult[T2, MapExceptionError | E1]:
        r = parser(s)
        if r.return_value is None:
            return StrParserResult(None, r.error, r.remain)
        else:
            try:
                ret_val = f(r.return_value)
            except Exception as e:
                return StrParserResult(None, MapExceptionError(e), r.remain)
            return StrParserResult(ret_val, None, r.remain)
    return new_parser
