"""Test clean-workspace."""

import clean_workspace


def test_import() -> None:
    """Test that the  can be imported."""
    assert isinstance(clean_workspace.__name__, str)


def test_version() -> None:
    """Test that the version is available."""
    assert isinstance(clean_workspace.__version__, str)
