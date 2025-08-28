#!/usr/bin/env python3
"""
Generate sample profile images for test fixtures.

Creates 256x256 JPEG images with different colors and simple patterns
to simulate realistic profile images that might come from Google Takeout.
"""

import base64
import io
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

def create_solid_color_image(color, size=(256, 256)):
    """Create a solid color image."""
    return Image.new('RGB', size, color)

def create_gradient_image(color1, color2, size=(256, 256)):
    """Create a gradient image between two colors."""
    img = Image.new('RGB', size, color1)
    draw = ImageDraw.Draw(img)
    
    for i in range(size[1]):
        # Calculate gradient factor
        factor = i / size[1]
        r = int(color1[0] * (1 - factor) + color2[0] * factor)
        g = int(color1[1] * (1 - factor) + color2[1] * factor)
        b = int(color1[2] * (1 - factor) + color2[2] * factor)
        draw.line([(0, i), (size[0], i)], fill=(r, g, b))
    
    return img

def create_geometric_image(bg_color, shape_color, size=(256, 256)):
    """Create an image with geometric shapes."""
    img = Image.new('RGB', size, bg_color)
    draw = ImageDraw.Draw(img)
    
    # Draw a circle in the center
    center = (size[0] // 2, size[1] // 2)
    radius = min(size) // 3
    draw.ellipse([
        center[0] - radius, center[1] - radius,
        center[0] + radius, center[1] + radius
    ], fill=shape_color)
    
    return img

def create_initials_image(initials, bg_color, text_color, size=(256, 256)):
    """Create an image with initials (like typical profile avatars)."""
    img = Image.new('RGB', size, bg_color)
    draw = ImageDraw.Draw(img)
    
    # Try to use a default font, fall back to default if not available
    try:
        font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()
    
    # Get text size and center it
    bbox = draw.textbbox((0, 0), initials, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (size[0] - text_width) // 2
    y = (size[1] - text_height) // 2
    
    draw.text((x, y), initials, fill=text_color, font=font)
    
    return img

def image_to_base64_jpeg(image, quality=85):
    """Convert PIL image to base64-encoded JPEG bytes."""
    buffer = io.BytesIO()
    image.save(buffer, format='JPEG', quality=quality)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

def image_to_jpeg_bytes(image, quality=85):
    """Convert PIL image to JPEG bytes."""
    buffer = io.BytesIO()
    image.save(buffer, format='JPEG', quality=quality)
    return buffer.getvalue()

def generate_profile_images():
    """Generate a set of realistic profile images for test fixtures."""
    
    profiles = {}
    
    # 1. John Doe - Professional blue gradient
    john_img = create_gradient_image((70, 130, 180), (30, 60, 100))  # Steel blue gradient
    profiles["john_doe.jpg"] = {
        "data": image_to_base64_jpeg(john_img),
        "bytes": image_to_jpeg_bytes(john_img),
        "mime_type": "image/jpeg",
        "filename": "john_doe.jpg"
    }
    
    # 2. Jane Smith - Warm initials style
    jane_img = create_initials_image("JS", (220, 20, 60), (255, 255, 255))  # Crimson with white text
    profiles["jane_smith.jpg"] = {
        "data": image_to_base64_jpeg(jane_img),
        "bytes": image_to_jpeg_bytes(jane_img),
        "mime_type": "image/jpeg", 
        "filename": "jane_smith.jpg"
    }
    
    # 3. Bob Wilson - Geometric pattern
    bob_img = create_geometric_image((34, 139, 34), (255, 215, 0))  # Forest green with gold circle
    profiles["bob_wilson.jpg"] = {
        "data": image_to_base64_jpeg(bob_img),
        "bytes": image_to_jpeg_bytes(bob_img),
        "mime_type": "image/jpeg",
        "filename": "bob_wilson.jpg"
    }
    
    # 4. Alice Johnson - Purple gradient
    alice_img = create_gradient_image((138, 43, 226), (75, 0, 130))  # Blue violet to indigo
    profiles["alice_johnson.jpg"] = {
        "data": image_to_base64_jpeg(alice_img),
        "bytes": image_to_jpeg_bytes(alice_img),
        "mime_type": "image/jpeg",
        "filename": "alice_johnson.jpg"
    }
    
    # 5. Charlie Brown - Initials with orange background
    charlie_img = create_initials_image("CB", (255, 140, 0), (255, 255, 255))  # Dark orange with white text
    profiles["charlie_brown.jpg"] = {
        "data": image_to_base64_jpeg(charlie_img),
        "bytes": image_to_jpeg_bytes(charlie_img),
        "mime_type": "image/jpeg",
        "filename": "charlie_brown.jpg"
    }
    
    # 6. Diana Prince - Elegant teal gradient
    diana_img = create_gradient_image((0, 128, 128), (72, 209, 204))  # Teal to medium turquoise
    profiles["diana_prince.jpg"] = {
        "data": image_to_base64_jpeg(diana_img),
        "bytes": image_to_jpeg_bytes(diana_img),
        "mime_type": "image/jpeg",
        "filename": "diana_prince.jpg"
    }
    
    return profiles

def save_images_to_disk(profiles, output_dir="profile_images"):
    """Save generated images to disk for inspection."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    for filename, profile in profiles.items():
        file_path = output_path / filename
        with open(file_path, 'wb') as f:
            f.write(profile["bytes"])
        print(f"Saved: {file_path}")

if __name__ == "__main__":
    print("Generating profile images...")
    profiles = generate_profile_images()
    
    print(f"Generated {len(profiles)} profile images:")
    for filename, profile in profiles.items():
        data_size = len(profile["data"])
        bytes_size = len(profile["bytes"])
        print(f"  {filename}: {bytes_size} bytes ({data_size} base64 chars)")
    
    # Save to disk for inspection
    save_images_to_disk(profiles)
    print("\nImages saved to 'profile_images/' directory for inspection.")
