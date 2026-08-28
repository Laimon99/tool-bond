"""Create the deterministic 1280x640 GitHub social preview for BondFX."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "docs" / "images"
LOGO_PATH = REPO_ROOT / "apps" / "web" / "public" / "images" / "bondfx-logo.png"
SCREENSHOT_PATH = OUTPUT_DIR / "demo.png"
REGULAR_FONT = Path("C:/Windows/Fonts/segoeui.ttf")
BOLD_FONT = Path("C:/Windows/Fonts/segoeuib.ttf")


def font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size=size)


def transparent_logo(path: Path, size: int) -> Image.Image:
    logo = Image.open(path).convert("RGBA")
    red, green, blue, _ = logo.split()
    alpha = Image.new("L", logo.size)
    alpha.putdata(
        [
            255 - min(r, g, b)
            for r, g, b in zip(
                red.get_flattened_data(),
                green.get_flattened_data(),
                blue.get_flattened_data(),
            )
        ]
    )
    logo.putalpha(alpha)
    bbox = logo.getbbox()
    if bbox:
        logo = logo.crop(bbox)
    logo.thumbnail((size, size), Image.Resampling.LANCZOS)
    return logo


def rounded_image(image: Image.Image, size: tuple[int, int], radius: int) -> Image.Image:
    fitted = ImageOps.fit(image.convert("RGB"), size, method=Image.Resampling.LANCZOS)
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=255)
    fitted.putalpha(mask)
    return fitted


def build(background_path: Path) -> tuple[Path, Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    background = ImageOps.fit(
        Image.open(background_path).convert("RGB"),
        (1280, 640),
        method=Image.Resampling.LANCZOS,
    )
    background_out = OUTPUT_DIR / "social-preview-background.jpg"
    background.save(background_out, quality=84, optimize=True, progressive=True)

    canvas = background.convert("RGBA")
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rounded_rectangle((48, 42, 635, 598), radius=28, fill=(250, 247, 238, 238))
    canvas = Image.alpha_composite(canvas, overlay)

    logo = transparent_logo(LOGO_PATH, 86)
    canvas.alpha_composite(logo, (78, 72))

    draw = ImageDraw.Draw(canvas)
    forest = "#11291f"
    green = "#096648"
    teal = "#08a6ae"
    muted = "#4e625a"
    draw.text((184, 86), "OPEN-SOURCE FINANCE ENGINEERING", font=font(BOLD_FONT, 17), fill=green)
    draw.text((78, 196), "Bond", font=font(BOLD_FONT, 76), fill=forest)
    bond_width = draw.textlength("Bond", font=font(BOLD_FONT, 76))
    draw.text((78 + bond_width, 196), "FX", font=font(BOLD_FONT, 76), fill=teal)
    draw.multiline_text(
        (78, 304),
        "Explainable TRY bond\nvaluation in USD.",
        font=font(BOLD_FONT, 37),
        fill=forest,
        spacing=5,
    )
    draw.text((78, 429), "Normalize  •  Value  •  Explain", font=font(REGULAR_FONT, 23), fill=green)
    draw.rounded_rectangle((78, 493, 510, 539), radius=23, fill=(17, 41, 31, 245))
    draw.text((101, 503), "FASTAPI   NEXT.JS   PYTHON", font=font(BOLD_FONT, 17), fill="#f9f6ec")
    draw.text((78, 557), "Educational proof of concept", font=font(REGULAR_FONT, 16), fill=muted)

    screenshot = rounded_image(Image.open(SCREENSHOT_PATH), (548, 343), 18)
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle((673, 151, 1245, 518), radius=24, fill=(0, 0, 0, 115))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    canvas = Image.alpha_composite(canvas, shadow)
    border = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(border).rounded_rectangle(
        (660, 138, 1232, 505),
        radius=24,
        fill=(17, 41, 31, 245),
    )
    canvas = Image.alpha_composite(canvas, border)
    canvas.alpha_composite(screenshot, (672, 150))

    output_path = OUTPUT_DIR / "social-preview.png"
    canvas.convert("RGB").save(output_path, optimize=True, compress_level=9)
    return background_out, output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--background", type=Path, required=True)
    args = parser.parse_args()
    background_output, preview_output = build(args.background)
    print(f"Saved background: {background_output}")
    print(f"Saved social preview: {preview_output}")
