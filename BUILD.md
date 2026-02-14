# Build and Release Guide

This document describes how to build and release Anime1 Desktop.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Local Build](#local-build)
- [CI/CD Setup](#cicd-setup)
- [Code Signing](#code-signing)
- [Release Process](#release-process)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- Node.js 22+
- npm or yarn
- Git

For platform-specific builds:
- **macOS**: Xcode Command Line Tools (for signing/notarization)
- **Windows**: Windows SDK (for signing)
- **Linux**: build-essential, fakeroot, dpkg, rpm

## Local Build

### Install Dependencies

```bash
npm install
```

### Development Mode

```bash
npm start
```

### Build for Current Platform

```bash
# Package without distribution
npm run package

# Create distributables
npm run make
```

### Build for Specific Platform

```bash
# macOS
npm run make -- --platform=darwin

# Windows
npm run make -- --platform=win32

# Linux
npm run make -- --platform=linux
```

### Running Tests

```bash
# Unit tests
npm test

# E2E tests
npm run test:e2e

# All tests
npm test && npm run test:e2e
```

## CI/CD Setup

The project uses GitHub Actions for automated builds and releases.

### Workflow Overview

1. **Test**: Runs on every push/PR
   - Unit tests with Vitest
   - E2E tests with Playwright

2. **Build**: Runs after tests pass
   - Builds on macOS, Ubuntu, and Windows
   - Creates platform-specific installers
   - Signs binaries (if certificates configured)

3. **Release**: Runs only on tags
   - Publishes to GitHub Releases
   - Generates release notes
   - Creates auto-updater feed

### Workflow File

The workflow is defined in `.github/workflows/build.yml`.

### Required Secrets

For code signing, add these secrets to your GitHub repository:

#### macOS Signing (Apple Developer ID)

| Secret | Description |
|--------|-------------|
| `MACOS_CERTIFICATE` | Base64-encoded Developer ID Application certificate (.p12) |
| `MACOS_CERTIFICATE_PWD` | Certificate password |
| `MACOS_CERTIFICATE_NAME` | Certificate name in Keychain |
| `MACOS_NOTARIZATION_APPLE_ID` | Apple ID for notarization |
| `MACOS_NOTARIZATION_TEAM_ID` | Apple Developer Team ID |
| `MACOS_NOTARIZATION_PWD` | App-specific password for notarization |

#### Windows Signing

| Secret | Description |
|--------|-------------|
| `WINDOWS_CERTIFICATE` | Base64-encoded code signing certificate (.pfx) |
| `WINDOWS_CERTIFICATE_PASSWORD` | Certificate password |

### Setting Up Secrets

1. Go to Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add each secret with its value

## Code Signing

### macOS

1. **Join Apple Developer Program** ($99/year)
2. **Create Developer ID Certificate**:
   - Xcode → Preferences → Accounts → Manage Certificates
   - Add "Developer ID Application"
   - Export certificate as .p12 file

3. **Enable Notarization**:
   - Generate app-specific password at appleid.apple.com
   - Get Team ID from developer.apple.com

4. **Encode Certificate**:
   ```bash
   base64 -i certificate.p12 -o certificate.base64
   ```

5. **Add to GitHub Secrets**:
   - Copy contents of `certificate.base64` to `MACOS_CERTIFICATE`
   - Add password to `MACOS_CERTIFICATE_PWD`
   - Add other required secrets

### Windows

1. **Obtain Code Signing Certificate**:
   - Purchase from a trusted CA (DigiCert, Sectigo, etc.)
   - Or use Azure Code Signing

2. **Export Certificate**:
   - Export as .pfx file with private key

3. **Encode Certificate**:
   ```powershell
   [Convert]::ToBase64String([IO.File]::ReadAllBytes("certificate.pfx")) | Set-Clipboard
   ```

4. **Add to GitHub Secrets**:
   - Paste base64 to `WINDOWS_CERTIFICATE`
   - Add password to `WINDOWS_CERTIFICATE_PASSWORD`

### Testing Signing Locally

#### macOS

```bash
# Set environment variables
export APPLE_ID="your-apple-id@example.com"
export APPLE_ID_PASSWORD="your-app-specific-password"
export APPLE_TEAM_ID="YOURTEAMID"
export MACOS_CERTIFICATE_NAME="Developer ID Application: Your Name (YOURTEAMID)"

# Build
npm run make
```

#### Windows

```powershell
# Set environment variables
$env:WINDOWS_PFX_FILE = "C:\path\to\certificate.pfx"
$env:WINDOWS_PFX_PASSWORD = "certificate-password"

# Build
npm run make
```

## Release Process

### Automatic Release (Recommended)

1. **Update Version**:
   ```bash
   npm version patch  # or minor, major
   ```

2. **Push Tag**:
   ```bash
   git push origin main --tags
   ```

3. **GitHub Actions Will**:
   - Run tests
   - Build for all platforms
   - Sign binaries (if secrets configured)
   - Create GitHub Release
   - Upload artifacts
   - Generate release notes

### Manual Release

1. Go to GitHub → Releases → Draft a new release
2. Create and push a new tag
3. GitHub Actions will handle the rest

### Pre-releases

For beta/alpha releases, include in the tag:
- `v1.0.0-alpha.1`
- `v1.0.0-beta.1`
- `v1.0.0-rc.1`

These will be marked as pre-releases on GitHub.

## Auto-Updater

The app uses `electron-updater` to check for updates from GitHub Releases.

### How It Works

1. App checks GitHub Releases for new versions
2. If update available, downloads in background
3. User notified and can install on next launch
4. Silent updates on Windows (Squirrel)

### Update Configuration

See `src/services/updater.js` for update settings:
- Check interval: 1 hour
- Auto-download: enabled
- Allow pre-releases: disabled (can be enabled in settings)

### Testing Updates

1. Build current version: `npm run make`
2. Create a test release with higher version
3. Install old version and check for updates

## Troubleshooting

### Build Failures

#### Out of Memory

```bash
export NODE_OPTIONS="--max-old-space-size=4096"
npm run make
```

#### Native Module Issues

```bash
npm run rebuild
# or
npx electron-rebuild
```

### Signing Issues

#### macOS: "Unable to build chain to self-signed root"

- Ensure Apple WWDR certificates are installed
- Download from: https://www.apple.com/certificateauthority/

#### macOS: Notarization Failed

Check notarization logs:
```bash
xcrun notarytool log <submission-id> --apple-id <apple-id> --team-id <team-id>
```

#### Windows: "SignTool Error"

- Verify certificate is valid and not expired
- Check certificate password is correct
- Ensure Windows SDK is installed

### CI/CD Issues

#### "Resource not accessible by integration"

- Check `GITHUB_TOKEN` permissions
- Ensure workflow has `contents: write` permission

#### Artifacts Not Uploaded

- Check artifact path in workflow
- Verify build actually created files

## Platform-Specific Notes

### macOS

- Minimum version: macOS 10.13 (High Sierra)
- Architecture: x64 and arm64 (Universal Binary)
- Gatekeeper requires signed and notarized apps

### Windows

- Minimum version: Windows 10
- Architecture: x64 and ia32
- SmartScreen may warn about unsigned apps

### Linux

- DEB: Debian, Ubuntu, Linux Mint
- RPM: Fedora, CentOS, RHEL, openSUSE
- Architecture: x64, arm64

## Support

For build issues:
1. Check GitHub Actions logs
2. Review Electron Forge documentation: https://www.electronforge.io/
3. Open an issue on GitHub
