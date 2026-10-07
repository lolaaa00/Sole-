"""Repository-wide Direct Mode configuration."""

import pytest


DIRECT_SDK_VERSION = "v0.2.16"


@pytest.fixture(autouse=True)
def pin_stable_studionet_sdk(monkeypatch):
    """Prevent CI from drifting to an incompatible latest prerelease bundle."""
    import gltest.direct.sdk_loader as sdk_loader

    original = sdk_loader.setup_sdk_paths

    def pinned(contract_path=None, sdk_version=None):
        return original(contract_path, sdk_version or DIRECT_SDK_VERSION)

    monkeypatch.setattr(sdk_loader, "setup_sdk_paths", pinned)
