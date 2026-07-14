from __future__ import annotations

import math

from src.utils.math_utils import extract_doi, normal_cdf


class TestNormalCDF:
    def test_zero_returns_half(self):
        assert math.isclose(normal_cdf(0.0), 0.5, rel_tol=1e-6)

    def test_positive_1_96(self):
        assert math.isclose(normal_cdf(1.96), 0.975, rel_tol=1e-3)

    def test_negative_1_96(self):
        assert math.isclose(normal_cdf(-1.96), 0.025, rel_tol=1e-3)

    def test_large_negative_clamps_to_zero(self):
        assert normal_cdf(-10.0) == 0.0
        assert normal_cdf(-100.0) == 0.0

    def test_large_positive_clamps_to_one(self):
        assert normal_cdf(10.0) == 1.0
        assert normal_cdf(100.0) == 1.0

    def test_boundary_negative_8(self):
        assert normal_cdf(-8.5) == 0.0
        assert math.isclose(normal_cdf(-8.0), 0.0, abs_tol=1e-14)

    def test_boundary_positive_8(self):
        assert normal_cdf(8.5) == 1.0
        assert math.isclose(normal_cdf(8.0), 1.0, abs_tol=1e-14)

    def test_symmetry(self):
        for z in [0.5, 1.0, 1.5, 2.0]:
            left = normal_cdf(-z)
            right = normal_cdf(z)
            assert math.isclose(left + right, 1.0, rel_tol=1e-6)

    def test_monotonic(self):
        vals = [normal_cdf(z / 10.0) for z in range(-30, 31)]
        for i in range(len(vals) - 1):
            assert vals[i] <= vals[i + 1]


class TestExtractDOI:
    def test_basic_doi(self):
        result = extract_doi("Check out this paper 10.1234/abc.123 for details")
        assert result == "10.1234/abc.123"

    def test_no_doi(self):
        assert extract_doi("no doi here") is None
        assert extract_doi("") is None
        assert extract_doi("just some random text 123") is None

    def test_doi_with_punctuation_trailing(self):
        result = extract_doi("See 10.1234/abc.123. and more")
        assert result == "10.1234/abc.123"

    def test_multiple_dois_returns_first(self):
        result = extract_doi("First 10.1111/first.001 and then 10.2222/second.002")
        assert result == "10.1111/first.001"

    def test_complex_doi(self):
        result = extract_doi("doi: 10.1007/s00425-019-03169-2")
        assert result == "10.1007/s00425-019-03169-2"

    def test_doi_in_brackets(self):
        result = extract_doi("[10.1234/abc.123]")
        assert result == "10.1234/abc.123]"

    def test_doi_with_query_params(self):
        result = extract_doi("10.1234/abc.123?download=true")
        assert result == "10.1234/abc.123?download=true"
