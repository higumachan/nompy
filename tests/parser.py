from dataclasses import dataclass

from nompy import tag, StrParserResult, TagParserError, sequence, sequence2, take_while_m_n, TakeWhileError, sequence3, \
    parser_map_exception


def test_tag():
    assert tag("hello")("hello world") == StrParserResult("hello", None, " world")
    assert tag("hello")("world") == StrParserResult(None, TagParserError("hello"), "world")

def test_tuple():
    parser = sequence2((tag("hello"), tag("world")))
    assert parser("helloworld") == StrParserResult(("hello", "world"), None, "")


def test_take_while():
    parser = take_while_m_n(2, 2, lambda c: c in "0123456789")
    assert parser("1234") == StrParserResult("12", None, "34")

    parser = take_while_m_n(2, 3, lambda c: c in "0123456789")
    assert parser("1234") == StrParserResult("123", None, "4")

    parser = take_while_m_n(2, 3, lambda c: c in "0123456789")
    assert parser("1a234") == StrParserResult(None, TakeWhileError(), "1a234")

def test_hex_color_parser():
    @dataclass
    class Color:
        r: int
        g: int
        b: int

    hex_2digit = parser_map_exception(take_while_m_n(2, 2, lambda c: c in "0123456789abcdefABCDEF"), lambda x: int(x, 16))
    parser = parser_map_exception(sequence2((tag("#"), sequence3(
        (hex_2digit,
        hex_2digit,
        hex_2digit)
    ))), lambda x: Color(r=x[1][0], g=x[1][1], b=x[1][2]))
    assert parser("#2F14DF") == StrParserResult(Color(r=47, g=20, b=223), None, "")
