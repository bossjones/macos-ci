from macos_ci._gui_core import (
    VncTarget,
    next_screenshot_sequence,
    parse_vnc_url,
    screenshot_filename,
)


def test_parse_vnc_url():
    line = "Opening vnc://:enhance-chase-volume-push@127.0.0.1:59415..."
    assert parse_vnc_url(line) == VncTarget(
        host="127.0.0.1", port=59415, password="enhance-chase-volume-push"
    )


def test_screenshot_filename_matches_spec_12_naming():
    # spec 12 §"gui": "artifacts/<run-id>/screenshots/NN-<label>.png"
    assert screenshot_filename(1, "starship-prompt") == "01-starship-prompt.png"


def test_screenshot_filename_slugifies_spaces_and_punctuation():
    assert screenshot_filename(2, "Nerd Font Glyphs!") == "02-nerd-font-glyphs.png"


def test_screenshot_filename_rejects_a_label_with_no_content():
    import pytest

    with pytest.raises(ValueError, match="empty"):
        screenshot_filename(1, "!!!")


def test_next_screenshot_sequence_starts_at_one():
    assert next_screenshot_sequence([]) == 1


def test_next_screenshot_sequence_continues_from_the_highest_existing():
    assert next_screenshot_sequence(["01-a.png", "02-b.png"]) == 3


def test_next_screenshot_sequence_ignores_unrelated_files():
    assert next_screenshot_sequence(["readme.txt", "01-a.png"]) == 2
