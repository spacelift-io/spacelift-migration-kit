#!/usr/bin/env bash
set -euo pipefail

# Configuration
SVG_SOURCE="src/smk/core/desktop/assets/logo.svg"
OUTPUT_DIR="src/smk/core/desktop/assets"
TEMP_DIR=$(mktemp -d)

# Generate PNG at specific size with proper aspect ratio handling
# Uses rsvg-convert for proper gradient rendering, then ImageMagick for padding
generate_png() {
    local size=$1
    local output=$2
    local temp_svg_render="$TEMP_DIR/temp_$size.png"

    # First: render SVG to PNG at target size with rsvg-convert (handles gradients properly)
    rsvg-convert \
        --width "$size" \
        --height "$size" \
        --keep-aspect-ratio \
        --background-color transparent \
        "$SVG_SOURCE" \
        -o "$temp_svg_render"

    # Second: ensure it's centered in a square canvas and properly formatted
    magick "$temp_svg_render" \
        -background transparent \
        -gravity center \
        -extent "${size}x${size}" \
        -strip \
        -depth 8 \
        "$output"

    rm "$temp_svg_render"
}

# Generate all iconset PNGs
mkdir -p "$TEMP_DIR/icon.iconset"
generate_png 16 "$TEMP_DIR/icon.iconset/icon_16x16.png"
generate_png 32 "$TEMP_DIR/icon.iconset/icon_16x16@2x.png"
generate_png 32 "$TEMP_DIR/icon.iconset/icon_32x32.png"
generate_png 64 "$TEMP_DIR/icon.iconset/icon_32x32@2x.png"
generate_png 128 "$TEMP_DIR/icon.iconset/icon_128x128.png"
generate_png 256 "$TEMP_DIR/icon.iconset/icon_128x128@2x.png"
generate_png 256 "$TEMP_DIR/icon.iconset/icon_256x256.png"
generate_png 512 "$TEMP_DIR/icon.iconset/icon_256x256@2x.png"
generate_png 512 "$TEMP_DIR/icon.iconset/icon_512x512.png"
generate_png 1024 "$TEMP_DIR/icon.iconset/icon_512x512@2x.png"

# Create ICNS from iconset
iconutil -c icns "$TEMP_DIR/icon.iconset" -o "$OUTPUT_DIR/icon.icns"

# Create ICO with multiple resolutions
generate_png 16 "$TEMP_DIR/ico_16.png"
generate_png 32 "$TEMP_DIR/ico_32.png"
generate_png 48 "$TEMP_DIR/ico_48.png"
generate_png 256 "$TEMP_DIR/ico_256.png"

magick "$TEMP_DIR/ico_16.png" "$TEMP_DIR/ico_32.png" \
       "$TEMP_DIR/ico_48.png" "$TEMP_DIR/ico_256.png" \
       "$OUTPUT_DIR/icon.ico"

# Create Linux PNG
generate_png 512 "$OUTPUT_DIR/icon.png"

# Cleanup
rm -rf "$TEMP_DIR"

echo "✓ Icons generated successfully"
