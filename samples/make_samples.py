"""Create simple sample product photos for demo mode. Replace with real phone photos for live testing."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).parent


def mug() -> Image.Image:
    img = Image.new("RGB", (1200, 900), (196, 170, 140))  # wooden table tone
    d = ImageDraw.Draw(img)
    d.rectangle([0, 620, 1200, 900], fill=(150, 120, 90))
    d.ellipse([430, 640, 790, 700], fill=(110, 85, 60))                       # shadow
    d.rounded_rectangle([450, 300, 750, 670], radius=40, fill=(232, 26, 59))  # body
    d.ellipse([450, 270, 750, 330], fill=(152, 0, 46))                        # rim
    d.ellipse([720, 380, 880, 560], outline=(232, 26, 59), width=34)          # handle
    return img.filter(ImageFilter.GaussianBlur(1))


def bottle() -> Image.Image:
    img = Image.new("RGB", (900, 1200), (231, 231, 231))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([340, 330, 560, 1050], radius=60, fill=(0, 143, 210))
    d.rectangle([390, 220, 510, 340], fill=(91, 110, 127))
    d.rounded_rectangle([375, 170, 525, 240], radius=18, fill=(51, 51, 51))
    d.rectangle([340, 600, 560, 700], fill=(255, 255, 255))
    return img


if __name__ == "__main__":
    mug().save(HERE / "sample_mug.jpg", quality=92)
    bottle().save(HERE / "sample_bottle.png")
    print("Created sample_mug.jpg and sample_bottle.png")
