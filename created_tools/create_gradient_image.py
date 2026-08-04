# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont
import numpy as np


# example tool (created by the agent during testing)
def create_gradient_image():
    """
    Creates an 800x600 image with a blue-to-red gradient, draws the text "Omni_core"
    in white at the center, and saves it as "gradient.png".
    """
    width = 800
    height = 600

    # 1. Create the image canvas
    img = Image.new('RGB', (width, height))
    pixels = np.zeros((height, width, 3), dtype=np.uint8)

    # 2. Generate the gradient (Blue to Red)
    # Blue at x=0, Red at x=width-1
    for y in range(height):
        for x in range(width):
            # Calculate interpolation factor based on x position
            ratio = x / width

            # Interpolate from Blue (0, 0, 255) to Red (255, 0, 0)
            # R component: increases from 0 to 255
            r = int(255 * ratio)
            # G component: stays at 0
            g = 0
            # B component: decreases from 255 to 0
            b = int(255 * (1 - ratio))

            pixels[y, x] = [r, g, b]

    img = Image.fromarray(pixels)

    # 3. Draw the text "Omni_core" in white at the center
    text = "Omni_core"
    font_size = 80
    try:
        # Attempt to use a common system font or default PIL font
        font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        print("Arial font not found, using default PIL font.")
        font = ImageFont.load_default()

    # Calculate text size and position for centering
    # Note: getbbox is preferred in newer Pillow versions
    try:
        bbox = ImageDraw.Draw(img).textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    except AttributeError:
        # Fallback for older PIL versions
        text_width, text_height = img.getsize()  # Placeholder size calculation if bounding box fails

    x_center = (width - text_width) / 2
    y_center = (height - text_height) / 2

    draw = ImageDraw.Draw(img)
    # Draw white text
    draw.text((x_center, y_center), text, fill=(255, 255, 255), font=font)

    # 4. Save the image
    output_filename = "gradient.png"
    img.save(output_filename)
    print(f"Successfully created and saved the gradient image to {output_filename}")


if __name__ == "__main__":
    create_gradient_image()