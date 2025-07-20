"""Test helper functions for creating valid test files."""

from pathlib import Path


def create_test_pdf(path: Path, content: str = "dummy content") -> Path:
    """Create a valid PDF file for testing."""
    from PIL import Image, ImageDraw, ImageFont
    
    # Create an image with text
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a default font, fall back to PIL default if not available
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 20)
    except (OSError, IOError):
        font = ImageFont.load_default()
    
    # Draw the text content on the image
    draw.text((50, 50), content, fill='black', font=font)
    
    # Save as PDF
    img.save(str(path), 'PDF', resolution=100.0)
    
    return path


def create_test_png(path: Path) -> Path:
    """Create a valid PNG file for testing."""
    png_header = b"\x89PNG\r\n\x1a\n"
    png_content = png_header + b"dummy image data"
    path.write_bytes(png_content)
    return path


def create_test_jpg(path: Path) -> Path:
    """Create a valid JPEG file for testing."""
    jpg_header = b"\xff\xd8\xff\xe0"
    jpg_content = jpg_header + b"dummy jpeg data"
    path.write_bytes(jpg_content)
    return path