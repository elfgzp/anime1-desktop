# Assets Directory

This directory contains application assets used for building and packaging.

## Required Files

### Icon Files

For proper app packaging, add the following icon files:

| File | Format | Size | Description |
|------|--------|------|-------------|
| `icon.ico` | Windows ICO | 256x256 (multi-size) | Windows app icon |
| `icon.icns` | macOS ICNS | 1024x1024 (multi-size) | macOS app icon |
| `icon.png` | PNG | 1024x1024 | Linux app icon, fallback |

### Optional Files

| File | Format | Description |
|------|--------|-------------|
| `installer.gif` | GIF | Windows installer animation |
| `dmg-background.png` | PNG | macOS DMG background |

## Creating Icons

### From PNG to ICO (Windows)

Using ImageMagick:
```bash
convert icon.png -define icon:auto-resize=256,128,64,48,32,16 icon.ico
```

Using an online converter:
- https://convertio.co/png-ico/
- https://icoconvert.com/

### From PNG to ICNS (macOS)

Using iconutil:
```bash
# Create iconset directory
mkdir icon.iconset

# Generate different sizes
sips -z 16 16 icon.png --out icon.iconset/icon_16x16.png
sips -z 32 32 icon.png --out icon.iconset/icon_16x16@2x.png
sips -z 32 32 icon.png --out icon.iconset/icon_32x32.png
sips -z 64 64 icon.png --out icon.iconset/icon_32x32@2x.png
sips -z 128 128 icon.png --out icon.iconset/icon_128x128.png
sips -z 256 256 icon.png --out icon.iconset/icon_128x128@2x.png
sips -z 256 256 icon.png --out icon.iconset/icon_256x256.png
sips -z 512 512 icon.png --out icon.iconset/icon_256x256@2x.png
sips -z 512 512 icon.png --out icon.iconset/icon_512x512.png
sips -z 1024 1024 icon.png --out icon.iconset/icon_512x512@2x.png

# Compile iconset to icns
iconutil -c icns icon.iconset

# Cleanup
rm -rf icon.iconset
```

### Recommended Icon Design

1. **Simple and recognizable** at small sizes (16x16)
2. **High contrast** for visibility
3. **Follow platform guidelines**:
   - macOS: https://developer.apple.com/design/human-interface-guidelines/app-icons
   - Windows: https://docs.microsoft.com/en-us/windows/apps/design/style/iconography/app-icon-design
   - Linux: Follow GNOME/KDE guidelines

4. **Use transparency** where appropriate
5. **Test on different backgrounds**

## Placeholder Icon

If you don't have custom icons yet, you can temporarily use a placeholder.
The build will work without icons, but the app will use default Electron icons.

## License

Ensure you have rights to use any icons placed in this directory.
