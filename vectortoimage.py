import sys
from pathlib import Path
import xml.etree.ElementTree as ET
import cairosvg
from PIL import Image

ANDROID_NS = "{http://schemas.android.com/apk/res/android}"

def android_vector_to_svg(xml_path, svg_path):
    """Convert Android VectorDrawable XML to SVG."""
    tree = ET.parse(xml_path)
    root = tree.getroot()

    if root.tag != "vector":
        raise ValueError("Not an Android VectorDrawable XML")

    # Extract dimensions
    width = root.attrib.get(ANDROID_NS + "width", "24dp").replace("dp", "")
    height = root.attrib.get(ANDROID_NS + "height", "24dp").replace("dp", "")
    viewportWidth = root.attrib.get(ANDROID_NS + "viewportWidth", width)
    viewportHeight = root.attrib.get(ANDROID_NS + "viewportHeight", height)

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" '
           f'width="{width}" height="{height}" viewBox="0 0 {viewportWidth} {viewportHeight}">']

    # Convert <path> elements
    for path in root.findall("path"):
        path_data = path.attrib.get(ANDROID_NS + "pathData")
        fill_color = path.attrib.get(ANDROID_NS + "fillColor", "#000000")
        if path_data:
            svg.append(f'<path d="{path_data}" fill="{fill_color}"/>')

    svg.append("</svg>")

    svg_str = "\n".join(svg)
    svg_path.write_text(svg_str)
    return svg_path

def convert_vector(input_path, output_path=None, output_format="png"):
    output_format = output_format.lower()
    if output_format not in ("png", "webp"):
        raise ValueError("Output format must be 'png' or 'webp'")

    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if output_path is None:
        output_path = input_path.with_suffix(f".{output_format}")
    else:
        output_path = Path(output_path)

    temp_svg = input_path.with_suffix(".temp.svg")
    temp_png = input_path.with_suffix(".temp.png")

    # Detect Android VectorDrawable
    tree = ET.parse(input_path)
    root = tree.getroot()
    if root.tag == "vector":
        print("🧩 Detected Android VectorDrawable — converting to SVG...")
        android_vector_to_svg(input_path, temp_svg)
        svg_source = temp_svg
    else:
        svg_source = input_path

    # Convert SVG → PNG
    try:
        cairosvg.svg2png(url=str(svg_source), write_to=str(temp_png))
    except Exception as e:
        print("⚠️ CairoSVG failed:", e)
        print("Using default 1024x1024 fallback...")
        cairosvg.svg2png(url=str(svg_source), write_to=str(temp_png),
                         output_width=1024, output_height=1024)

    # PNG → final output
    if output_format == "png":
        temp_png.rename(output_path)
    else:
        with Image.open(temp_png) as img:
            img.save(output_path, "WEBP")
        temp_png.unlink(missing_ok=True)

    temp_svg.unlink(missing_ok=True)
    print(f"✅ Converted: {input_path.name} → {output_path.name}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python vectortoimage.py <input.xml/svg> [png|webp]")
        sys.exit(1)

    input_file = sys.argv[1]
    fmt = sys.argv[2] if len(sys.argv) > 2 else "png"
    convert_vector(input_file, output_format=fmt)
