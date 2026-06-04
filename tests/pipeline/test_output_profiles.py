from __future__ import annotations

import pytest

from src.pipeline.output_profiles import (
    OUTPUT_PROFILES,
    OutputFormat,
    OutputProfile,
    detect_format,
    get_profile,
)


class TestDetectFormat:
    def test_dissertation_keywords_return_dissertation(self) -> None:
        result = detect_format("dissertation thesis paradigm shift hypothesis")
        assert result == OutputFormat.DISSERTATION

    def test_blueprint_keywords_return_blueprint(self) -> None:
        result = detect_format("write a blueprint specification for the api")
        assert result == OutputFormat.BLUEPRINT

    def test_code_keywords_return_code(self) -> None:
        result = detect_format("implement a function to sort the algorithm with code")
        assert result == OutputFormat.CODE

    def test_no_keywords_defaults_to_article_in_solve_mode(self) -> None:
        result = detect_format("xyzzy")
        assert result == OutputFormat.ARTICLE

    def test_turbo_mode_boosts_dissertation_on_no_keywords(self) -> None:
        result = detect_format("xyzzy", mode="turbo")
        assert result == OutputFormat.DISSERTATION

    def test_turbo_mode_boosts_dissertation_with_weak_signal(self) -> None:
        result = detect_format("shift", mode="turbo")
        assert result == OutputFormat.DISSERTATION


class TestOutputProfile:
    def test_profile_construction_defaults(self) -> None:
        profile = OutputProfile(format=OutputFormat.DISSERTATION, label="Test", description="Desc")
        assert profile.format == OutputFormat.DISSERTATION
        assert profile.label == "Test"
        assert profile.require_abstract is True
        assert profile.require_epistemic_notice is True
        assert profile.file_extension == ".md"

    def test_profile_custom_export_formats(self) -> None:
        profile = OutputProfile(
            format=OutputFormat.DISSERTATION,
            label="Test",
            description="Desc",
            export_formats=["markdown", "json", "bibtex", "latex"],
        )
        assert "bibtex" in profile.export_formats
        assert "latex" in profile.export_formats


class TestOutputProfilesRegistry:
    def test_all_formats_have_profile(self) -> None:
        for fmt in OutputFormat:
            assert fmt in OUTPUT_PROFILES, f"Missing profile for {fmt}"

    def test_dissertation_profile_has_verification_backends(self) -> None:
        profile = OUTPUT_PROFILES[OutputFormat.DISSERTATION]
        assert len(profile.verification_backends) > 0
        assert "lean4" in profile.verification_backends
        assert profile.require_formal_proof is True

    def test_article_profile_requires_empirical_validation(self) -> None:
        profile = OUTPUT_PROFILES[OutputFormat.ARTICLE]
        assert profile.require_empirical_validation is True
        assert profile.require_formal_proof is False

    def test_code_profile_disables_sections_and_references(self) -> None:
        profile = OUTPUT_PROFILES[OutputFormat.CODE]
        assert profile.require_abstract is False
        assert profile.require_sections is False
        assert profile.require_references is False
        assert profile.require_epistemic_notice is False


class TestGetProfile:
    def test_get_profile_returns_dissertation(self) -> None:
        profile = get_profile(OutputFormat.DISSERTATION)
        assert profile.label == "Academic Dissertation"

    def test_get_profile_unknown_falls_back_to_dissertation(self) -> None:
        profile = get_profile("nonexistent")  # type: ignore[arg-type]
        assert profile.format == OutputFormat.DISSERTATION
