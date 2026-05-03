from __future__ import annotations

import math
from typing import Any, Literal

from shared.constants import FUZZY_MATCH_TOLERANCE
from shared.schemas import MatchVerdict

ExpectedOutputType = Literal["exact", "numeric", "contains"]


def _is_number(value: Any) -> bool:
	return isinstance(value, (int, float)) and not isinstance(value, bool)


def _contains_check(actual: Any, expected: Any) -> bool:
	if isinstance(actual, str) and isinstance(expected, str):
		return expected.lower() in actual.lower()
	if isinstance(actual, list):
		return expected in actual
	if isinstance(actual, dict) and isinstance(expected, str):
		return expected in actual
	return False


def judge_output(
	actual_output: Any,
	expected_output: Any,
	expected_output_type: ExpectedOutputType,
	tolerance: float = FUZZY_MATCH_TOLERANCE,
) -> MatchVerdict:
	"""Compare model output with expected output and return a structured verdict."""
	if expected_output_type == "exact":
		ok = actual_output == expected_output
		if not ok and isinstance(actual_output, (str, int, float, bool)) and isinstance(expected_output, (str, int, float, bool)):
			ok = str(actual_output) == str(expected_output)
		return MatchVerdict(matched=ok, reason="exact_match" if ok else "exact_mismatch")

	if expected_output_type == "numeric":
		if not (_is_number(actual_output) and _is_number(expected_output)):
			return MatchVerdict(matched=False, reason="numeric_type_mismatch")
		ok = math.isclose(float(actual_output), float(expected_output), rel_tol=0.0, abs_tol=tolerance)
		return MatchVerdict(matched=ok, reason="numeric_within_tolerance" if ok else "numeric_out_of_tolerance")

	if expected_output_type == "contains":
		ok = _contains_check(actual_output, expected_output)
		return MatchVerdict(matched=ok, reason="contains_match" if ok else "contains_mismatch")

	return MatchVerdict(matched=False, reason=f"unsupported_expected_output_type:{expected_output_type}")
