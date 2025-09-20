#!/usr/bin/env python3
"""
RemBraille Icon Generation Script

Generates icons in multiple formats from the main SVG source file.
Produces system tray icons, Windows .ico files, high-resolution PNGs,
and standard PNGs for Qt applications.

Requirements:
    pip install Pillow cairosvg

Usage:
    python scripts/generate_icons.py [--clean] [--verbose] [--format FORMAT]

Copyright (C) 2025 Stefan Lohmaier
Licensed under GNU GPL v2.0 or later
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Tuple, Optional

try:
    import cairosvg
    from PIL import Image, ImageOps
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    MISSING_DEPENDENCY = str(e)

# Configuration
SVG_SOURCE = "resources/icons/rembraille_icon.svg"
OUTPUT_BASE = "resources/icons/generated"

# Icon size configurations
ICON_CONFIGS = {
    "systray": [16, 24, 32],
    "standard": [48, 64, 128, 256],
    "highres": [512, 1024],
    "windows_ico": [16, 24, 32, 48, 64, 128, 256]
}

def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )

def check_dependencies():
    """Check if required dependencies are available"""
    if not DEPENDENCIES_AVAILABLE:
        logging.error(f"Missing required dependencies: {MISSING_DEPENDENCY}")
        logging.error("Please install required packages:")
        logging.error("  pip install Pillow cairosvg")
        return False
    return True

def ensure_directory(path: Path):
    """Ensure directory exists"""
    path.mkdir(parents=True, exist_ok=True)
    logging.debug(f"Ensured directory exists: {path}")

def svg_to_png(svg_path: Path, output_path: Path, size: int) -> bool:
    """Convert SVG to PNG at specified size"""
    try:
        # Convert SVG to PNG using cairosvg
        png_data = cairosvg.svg2png(
            url=str(svg_path),
            output_width=size,
            output_height=size
        )

        # Save to file
        with open(output_path, 'wb') as f:
            f.write(png_data)

        logging.debug(f"Generated {size}x{size} PNG: {output_path}")
        return True

    except Exception as e:
        logging.error(f"Failed to generate {size}x{size} PNG: {e}")
        return False

def create_ico_file(png_files: List[Path], ico_path: Path) -> bool:
    """Create Windows .ico file from multiple PNG files"""
    try:
        # Load all PNG images
        images = []
        for png_file in png_files:
            if png_file.exists():
                img = Image.open(png_file)
                images.append(img)
            else:
                logging.warning(f"PNG file not found for ICO generation: {png_file}")

        if not images:
            logging.error("No PNG files available for ICO generation")
            return False

        # Save as ICO file with multiple resolutions
        images[0].save(
            ico_path,
            format='ICO',
            sizes=[(img.width, img.height) for img in images]
        )

        logging.info(f"Generated Windows ICO file: {ico_path}")
        return True

    except Exception as e:
        logging.error(f"Failed to generate ICO file: {e}")
        return False

def generate_icon_set(svg_path: Path, output_base: Path, formats: Optional[List[str]] = None) -> bool:
    """Generate complete icon set from SVG source"""
    if not svg_path.exists():
        logging.error(f"SVG source file not found: {svg_path}")
        return False

    logging.info(f"Generating icons from: {svg_path}")

    # Determine which formats to generate
    if formats is None:
        formats = list(ICON_CONFIGS.keys())

    success = True
    generated_files = {}

    # Generate PNG files for each category
    for format_name in formats:
        if format_name == "windows_ico":
            continue  # Handle ICO separately

        if format_name not in ICON_CONFIGS:
            logging.warning(f"Unknown format: {format_name}")
            continue

        sizes = ICON_CONFIGS[format_name]
        format_dir = output_base / format_name
        ensure_directory(format_dir)

        generated_files[format_name] = []

        for size in sizes:
            output_file = format_dir / f"{size}x{size}.png"
            if svg_to_png(svg_path, output_file, size):
                generated_files[format_name].append(output_file)
            else:
                success = False

    # Generate Windows ICO file if requested
    if "windows_ico" in formats:
        ico_dir = output_base / "windows"
        ensure_directory(ico_dir)
        ico_path = ico_dir / "rembraille.ico"

        # Collect PNG files for ICO
        ico_pngs = []
        for size in ICON_CONFIGS["windows_ico"]:
            # Look for the PNG in any generated format
            for format_files in generated_files.values():
                for png_file in format_files:
                    if f"{size}x{size}.png" in str(png_file):
                        ico_pngs.append(png_file)
                        break

        if ico_pngs:
            if not create_ico_file(ico_pngs, ico_path):
                success = False
        else:
            logging.error("No PNG files found for ICO generation")
            success = False

    return success

def clean_generated_files(output_base: Path):
    """Remove all generated files"""
    if output_base.exists():
        import shutil
        shutil.rmtree(output_base)
        logging.info(f"Cleaned generated files from: {output_base}")
    else:
        logging.info("No generated files to clean")

def print_usage_examples():
    """Print usage examples for the generated icons"""
    print("\n" + "="*60)
    print("ICON USAGE EXAMPLES")
    print("="*60)

    print("\n📱 System Tray Icons:")
    print("  Windows: resources/icons/generated/systray/16x16.png")
    print("  macOS:   resources/icons/generated/systray/24x24.png")
    print("  Linux:   resources/icons/generated/systray/32x32.png")

    print("\n🖥️  Windows ICO:")
    print("  resources/icons/generated/windows/rembraille.ico")

    print("\n🎨 Qt/GUI Applications:")
    print("  Small:  resources/icons/generated/standard/48x48.png")
    print("  Medium: resources/icons/generated/standard/128x128.png")
    print("  Large:  resources/icons/generated/standard/256x256.png")

    print("\n📄 Documentation/Marketing:")
    print("  Logo:   resources/icons/generated/highres/512x512.png")
    print("  Banner: resources/icons/generated/highres/1024x1024.png")

    print("\n💻 Python Example (System Tray):")
    print("  import tkinter as tk")
    print("  root = tk.Tk()")
    print("  icon = tk.PhotoImage(file='resources/icons/generated/systray/32x32.png')")
    print("  root.iconphoto(True, icon)")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Generate RemBraille icons in multiple formats",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/generate_icons.py                    # Generate all formats
  python scripts/generate_icons.py --format systray   # Generate only system tray icons
  python scripts/generate_icons.py --clean            # Clean generated files
  python scripts/generate_icons.py --verbose          # Verbose output
        """
    )

    parser.add_argument(
        '--clean',
        action='store_true',
        help='Remove all generated files'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )

    parser.add_argument(
        '--format',
        choices=['systray', 'standard', 'highres', 'windows_ico'],
        help='Generate only specific format (default: all)'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

    # Get script directory and project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # Paths
    svg_path = project_root / SVG_SOURCE
    output_base = project_root / OUTPUT_BASE

    # Clean if requested
    if args.clean:
        clean_generated_files(output_base)
        return 0

    # Check dependencies
    if not check_dependencies():
        return 1

    # Determine formats to generate
    formats = [args.format] if args.format else None

    # Generate icons
    logging.info("🎨 Starting RemBraille icon generation...")

    if generate_icon_set(svg_path, output_base, formats):
        logging.info("✅ Icon generation completed successfully!")

        # Print usage examples
        if not args.format:  # Only show examples when generating all formats
            print_usage_examples()

        return 0
    else:
        logging.error("❌ Icon generation failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())