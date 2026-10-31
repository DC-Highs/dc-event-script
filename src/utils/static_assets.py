import asyncio
import logging
import string
from typing import Any, Dict, Optional

import httpx
from dc_assets import AssetDownloader, AssetsError, DragonThumbnailDownloader
from dc_core import DragonPhase, StaticFileUrlPlatformPrefix

logger = logging.getLogger(__name__)

ASSET_TIMEOUT_SECONDS: float = 30.0
SPINE_FORMAT: str = 'spine'
BASIC_PREFIX: str = 'basic_'


class VersionedChestSpriteDownloader(AssetDownloader):
    """Chest sprite whose file name already carries its prefix and version suffix."""

    def __init__(
        self,
        file_name: str,
        platform_prefix: StaticFileUrlPlatformPrefix = StaticFileUrlPlatformPrefix.ANDROID
    ) -> None:
        self.file_name = file_name
        self.platform_prefix = str(platform_prefix)

    @property
    def url(self) -> str:
        return (
            f"https://{self.platform_prefix}-static-s1.socialpointgames.com"
            f"/static/dragoncity/mobile/ui/chests/ui_{self.file_name}.png"
        )


def chest_file_name(chest_name: str, version_info: Optional[Dict[str, Any]]) -> str:
    """Applies the `asset_versioning` rules: `basic_` for spine chests and `_b`, `_c`... for versions above 1."""
    if not version_info:
        return chest_name

    prefix: str = BASIC_PREFIX if version_info['Format'] == SPINE_FORMAT else ""
    suffix: str = "" if version_info['Version'] == 1 else "_" + string.ascii_lowercase[version_info['Version']]
    return f"{prefix}{chest_name}{suffix}"


def chest_sprite_downloader(chest_name: str, version_info: Optional[Dict[str, Any]]) -> VersionedChestSpriteDownloader:
    return VersionedChestSpriteDownloader(chest_file_name(chest_name, version_info))


def dragon_thumbnail_downloader(image_name: str) -> DragonThumbnailDownloader:
    return DragonThumbnailDownloader(
        image_name,
        DragonPhase.ADULT,
        platform_prefix=StaticFileUrlPlatformPrefix.ANDROID
    )


async def _fetch(downloader: AssetDownloader) -> bytes:
    async with httpx.AsyncClient(timeout=ASSET_TIMEOUT_SECONDS, follow_redirects=True) as client:
        return await downloader.fetch(client)


def fetch_asset(downloader: AssetDownloader) -> Optional[bytes]:
    """Downloads a static file into memory; returns None (and logs) when it cannot be downloaded."""
    try:
        return asyncio.run(_fetch(downloader))
    except AssetsError as error:
        logger.error(f"Failed to download {downloader.url}: {error}")
        return None
