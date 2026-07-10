import pytest

from macos_ci._config_core import ConfigError, load


def test_load_valid_config():
    raw = {
        "default": "sequoia",
        "image": {
            "sequoia": {
                "source": "oci",
                "ref": "ghcr.io/cirruslabs/macos-sequoia-vanilla:latest",
            },
            "sequoia-15.6.1": {
                "source": "ipsw",
                "url": "https://updates.cdn-apple.com/.../UniversalMac_15.6.1_Restore.ipsw",
                "sha256": "a" * 64,
            },
        },
    }

    config = load(raw)

    assert config.default == "sequoia"
    assert config.images["sequoia"].source == "oci"
    assert config.images["sequoia"].ref == "ghcr.io/cirruslabs/macos-sequoia-vanilla:latest"
    assert config.images["sequoia-15.6.1"].source == "ipsw"
    assert config.images["sequoia-15.6.1"].sha256 == "a" * 64


def test_load_rejects_unknown_source():
    raw = {
        "default": "sequoia",
        "image": {
            "sequoia": {"source": "usb-stick", "ref": "whatever"},
        },
    }

    with pytest.raises(ConfigError, match="unknown source"):
        load(raw)


def test_load_rejects_ipsw_missing_sha256():
    raw = {
        "default": "sequoia-15.6.1",
        "image": {
            "sequoia-15.6.1": {
                "source": "ipsw",
                "url": "https://updates.cdn-apple.com/.../UniversalMac_15.6.1_Restore.ipsw",
            },
        },
    }

    with pytest.raises(ConfigError, match="sha256"):
        load(raw)


def test_load_rejects_default_naming_nonexistent_image():
    raw = {
        "default": "tahoe",
        "image": {
            "sequoia": {
                "source": "oci",
                "ref": "ghcr.io/cirruslabs/macos-sequoia-vanilla:latest",
            },
        },
    }

    with pytest.raises(ConfigError, match="default"):
        load(raw)
