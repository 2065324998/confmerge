"""Tests for type coercion of string configuration values."""

from confmerge.coerce import coerce_value


class TestCoerceValue:
    def test_coerce_true_variants(self):
        for val in ("true", "True", "TRUE", "yes", "Yes", "on", "ON", "1"):
            assert coerce_value(val) is True, f"Expected True for '{val}'"

    def test_coerce_false_variants(self):
        for val in ("false", "False", "FALSE", "no", "No", "off", "OFF", "0"):
            assert coerce_value(val) is False, f"Expected False for '{val}'"

    def test_coerce_integer(self):
        assert coerce_value("42") == 42
        assert isinstance(coerce_value("42"), int)

    def test_coerce_negative_integer(self):
        assert coerce_value("-7") == -7
        assert isinstance(coerce_value("-7"), int)

    def test_coerce_float(self):
        assert coerce_value("3.14") == 3.14
        assert isinstance(coerce_value("3.14"), float)

    def test_coerce_string_unchanged(self):
        assert coerce_value("hello") == "hello"
        assert coerce_value("/path/to/file") == "/path/to/file"
        assert coerce_value("localhost") == "localhost"

    def test_coerce_null_string_stays_string(self):
        """'null' and 'none' are intentionally kept as strings."""
        assert coerce_value("null") == "null"
        assert coerce_value("none") == "none"
        assert coerce_value("None") == "None"

    def test_coerce_empty_string(self):
        assert coerce_value("") == ""
        assert coerce_value("   ") == "   "

    def test_coerce_whitespace_handling(self):
        assert coerce_value("  true  ") is True
        assert coerce_value("  42  ") == 42
        assert coerce_value("  3.14  ") == 3.14

    def test_coerce_non_string_passthrough(self):
        assert coerce_value(42) == 42
        assert coerce_value(3.14) == 3.14
        assert coerce_value(True) is True
        assert coerce_value(False) is False
        assert coerce_value(None) is None
        assert coerce_value([1, 2]) == [1, 2]
