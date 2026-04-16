"""Test clean-workspace."""

import clean_workspace


def test_import() -> None:
    """Test that the  can be imported."""
    assert isinstance(clean_workspace.__name__, str)
