#!/bin/bash
# Setup script for GitHub Actions secrets
# This script helps encode certificates for GitHub Actions

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "=========================================="
echo "GitHub Actions Secrets Setup"
echo "=========================================="
echo ""

# Function to encode file to base64
encode_file() {
    local file="$1"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        base64 -i "$file" -o "${file}.base64"
    else
        # Linux
        base64 -w 0 "$file" > "${file}.base64"
    fi
    echo "Encoded to: ${file}.base64"
    echo "Content:"
    cat "${file}.base64"
    echo ""
}

# Menu
echo "Select secret to generate:"
echo "1) macOS Certificate (.p12)"
echo "2) Windows Certificate (.pfx)"
echo "3) Show all required secrets"
echo "4) Exit"
echo ""
read -p "Choice: " choice

case $choice in
    1)
        echo ""
        echo "macOS Certificate Setup"
        echo "----------------------"
        read -p "Path to .p12 certificate: " cert_path
        
        if [ ! -f "$cert_path" ]; then
            echo "Error: File not found: $cert_path"
            exit 1
        fi
        
        echo ""
        echo "Encoding certificate..."
        encode_file "$cert_path"
        
        echo ""
        echo "Add these secrets to GitHub:"
        echo "1. MACOS_CERTIFICATE - Copy contents of ${cert_path}.base64"
        read -s -p "2. MACOS_CERTIFICATE_PWD: " cert_pwd
        echo ""
        echo "3. MACOS_CERTIFICATE_NAME - Usually 'Developer ID Application: Your Name (TEAM_ID)'"
        read -p "4. MACOS_NOTARIZATION_APPLE_ID: " apple_id
        read -p "5. MACOS_NOTARIZATION_TEAM_ID: " team_id
        read -s -p "6. MACOS_NOTARIZATION_PWD (app-specific password): " notary_pwd
        echo ""
        echo ""
        echo "Summary of secrets to add:"
        echo "--------------------------"
        echo "MACOS_CERTIFICATE: [See ${cert_path}.base64]"
        echo "MACOS_CERTIFICATE_PWD: [hidden]"
        echo "MACOS_CERTIFICATE_NAME: Developer ID Application: [Your Name] ($team_id)"
        echo "MACOS_NOTARIZATION_APPLE_ID: $apple_id"
        echo "MACOS_NOTARIZATION_TEAM_ID: $team_id"
        echo "MACOS_NOTARIZATION_PWD: [hidden]"
        ;;
        
    2)
        echo ""
        echo "Windows Certificate Setup"
        echo "------------------------"
        read -p "Path to .pfx certificate: " cert_path
        
        if [ ! -f "$cert_path" ]; then
            echo "Error: File not found: $cert_path"
            exit 1
        fi
        
        echo ""
        echo "Encoding certificate..."
        encode_file "$cert_path"
        
        echo ""
        echo "Add these secrets to GitHub:"
        echo "1. WINDOWS_CERTIFICATE - Copy contents of ${cert_path}.base64"
        read -s -p "2. WINDOWS_CERTIFICATE_PASSWORD: " cert_pwd
        echo ""
        echo ""
        echo "Summary of secrets to add:"
        echo "--------------------------"
        echo "WINDOWS_CERTIFICATE: [See ${cert_path}.base64]"
        echo "WINDOWS_CERTIFICATE_PASSWORD: [hidden]"
        ;;
        
    3)
        echo ""
        echo "Required GitHub Secrets"
        echo "======================="
        echo ""
        echo "macOS Signing (Optional but recommended)"
        echo "----------------------------------------"
        echo "MACOS_CERTIFICATE           - Base64-encoded Developer ID Application certificate (.p12)"
        echo "MACOS_CERTIFICATE_PWD       - Certificate password"
        echo "MACOS_CERTIFICATE_NAME      - Certificate name (e.g., 'Developer ID Application: Name (ID)')"
        echo "MACOS_NOTARIZATION_APPLE_ID - Apple ID email"
        echo "MACOS_NOTARIZATION_TEAM_ID  - Apple Developer Team ID"
        echo "MACOS_NOTARIZATION_PWD      - App-specific password for notarization"
        echo ""
        echo "Windows Signing (Optional but recommended)"
        echo "------------------------------------------"
        echo "WINDOWS_CERTIFICATE         - Base64-encoded code signing certificate (.pfx)"
        echo "WINDOWS_CERTIFICATE_PASSWORD - Certificate password"
        echo ""
        echo "Auto-generated (No action needed)"
        echo "---------------------------------"
        echo "GITHUB_TOKEN                - Automatically provided by GitHub Actions"
        ;;
        
    4)
        echo "Exiting..."
        exit 0
        ;;
        
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "Next steps:"
echo "1. Go to https://github.com/gzp/anime1-desktop/settings/secrets/actions"
echo "2. Click 'New repository secret'"
echo "3. Add each secret with the values shown above"
echo "4. Done! Next tag push will trigger signed builds"
