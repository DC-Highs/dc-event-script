import logging

import numpy as np
import pytest
from PIL import Image, ImageDraw, ImageFont

from conftest import png_bytes, rgba_array
from src.utils.image_processing import (
    apply_transparency_mask,
    draw_text_with_offset,
    load_image_as_array,
    load_image_from_bytes,
    resize_icon,
)
from src.utils.network import ensure_directory


def test_ensure_directory(tmp_path):
    target = tmp_path / "a" / "b"

    ensure_directory(str(target))
    ensure_directory(str(target))

    assert target.is_dir()


def test_load_image_as_array(tmp_path, caplog):
    path = tmp_path / "image.png"
    Image.new("RGB", (3, 2), (1, 2, 3)).save(path)

    assert load_image_as_array(str(path)).shape == (2, 3, 3)

    with caplog.at_level(logging.ERROR):
        assert load_image_as_array(str(tmp_path / "missing.png")) is None

    assert "Error loading image" in caplog.text


def test_load_image_from_bytes(caplog):
    assert load_image_from_bytes(png_bytes("RGB", (3, 2), (1, 2, 3))).shape == (2, 3, 3)

    with caplog.at_level(logging.ERROR):
        assert load_image_from_bytes(b"not an image") is None

    assert "Error decoding image data" in caplog.text


def test_apply_transparency_mask():
    gray = np.zeros((2, 2), dtype=np.uint8)
    rgb = np.zeros((2, 2, 3), dtype=np.uint8)
    assert apply_transparency_mask(gray) is gray
    assert apply_transparency_mask(rgb) is rgb

    rgba = rgba_array(2, 1)
    rgba[0, 0, 3] = 0
    masked = apply_transparency_mask(rgba)

    assert masked[0, 0].tolist() == [255, 255, 255, 255]
    assert masked[0, 1].tolist() == [100, 100, 100, 255]
    assert rgba[0, 0].tolist() == [100, 100, 100, 0]


def test_resize_icon():
    assert resize_icon(rgba_array(10, 10)).size == (60, 60)
    assert resize_icon(np.zeros((10, 10, 3), dtype=np.uint8), size=(20, 30)).size == (20, 30)
    assert resize_icon(np.zeros((10, 10), dtype=np.uint8), size=(5, 5)).size == (5, 5)


def test_draw_text_with_offset():
    canvas = Image.new("L", (60, 60), 0)
    draw = ImageDraw.Draw(canvas)

    draw_text_with_offset(draw, (2, 2), "Hi", ImageFont.load_default_imagefont(), 255, y_offset=20)

    assert np.array(canvas)[:20].max() == 0
    assert np.array(canvas)[20:].max() == 255
    draw_text_with_offset(draw, (2, 2), "Hi", ImageFont.load_default_imagefont(), 255)
