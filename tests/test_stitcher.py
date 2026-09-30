from PIL import Image
from app.stitcher import stitch

def test_vertical_preserves_native_pixels(tmp_path):
    a = tmp_path / "1.png"
    b = tmp_path / "2.png"
    Image.new("RGB", (4000, 3000), "white").save(a)
    Image.new("RGB", (4000, 2000), "black").save(b)
    out = stitch([a, b], "vertical", gap=10)
    assert out.size == (4000, 5010)

def test_horizontal_preserves_native_pixels(tmp_path):
    a = tmp_path / "1.png"
    b = tmp_path / "2.png"
    Image.new("RGB", (4000, 3000), "white").save(a)
    Image.new("RGB", (2000, 3000), "black").save(b)
    out = stitch([a, b], "horizontal", gap=10)
    assert out.size == (6010, 3000)
