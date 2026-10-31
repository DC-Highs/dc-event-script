import httpx
import pytest

from conftest import png_bytes
from src.utils.static_assets import (
    VersionedChestSpriteDownloader,
    chest_file_name,
    chest_sprite_downloader,
    dragon_thumbnail_downloader,
    fetch_asset,
)

UI = "https://dca-static-s1.socialpointgames.com/static/dragoncity/mobile/ui"


@pytest.mark.parametrize(
    "version_info, expected",
    [
        (None, "wood_chest"),
        ({}, "wood_chest"),
        ({"Format": "png", "Version": 1}, "wood_chest"),
        ({"Format": "spine", "Version": 1}, "basic_wood_chest"),
        ({"Format": "png", "Version": 2}, "wood_chest_c"),
        ({"Format": "spine", "Version": 3}, "basic_wood_chest_d"),
    ],
)
def test_chest_file_name(version_info, expected):
    assert chest_file_name("wood_chest", version_info) == expected


def test_downloader_urls():
    assert VersionedChestSpriteDownloader("abc").url == f"{UI}/chests/ui_abc.png"
    assert VersionedChestSpriteDownloader("abc", "dci").url.startswith("https://dci-static-s1.")
    assert chest_sprite_downloader("wood", {"Format": "spine", "Version": 2}).url == f"{UI}/chests/ui_basic_wood_c.png"
    assert dragon_thumbnail_downloader("1000_dragon_nature").url == f"{UI}/dragons/HD/thumb_1000_dragon_nature_3.png"


def test_fetch_asset_returns_the_file_content(mock_http):
    requested = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested.append(str(request.url))
        return httpx.Response(200, content=png_bytes())

    mock_http(handler)

    assert fetch_asset(dragon_thumbnail_downloader("nature")) == png_bytes()
    assert requested == [f"{UI}/dragons/HD/thumb_nature_3.png"]


def test_fetch_asset_returns_none_when_the_download_fails(mock_http, caplog):
    mock_http(lambda request: httpx.Response(404))

    assert fetch_asset(chest_sprite_downloader("missing", None)) is None
    assert "Failed to download" in caplog.text and "ui_missing.png" in caplog.text
