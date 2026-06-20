#!/bin/bash
# Installation script for Choosr browser selector

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info()    { echo -e "${BLUE}ℹ${NC} $1" >&2; }
print_success() { echo -e "${GREEN}✓${NC} $1" >&2; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1" >&2; }
print_error()   { echo -e "${RED}✗${NC} $1" >&2; }

main() {
    echo "Installing Choosr Browser Selector..."
    echo "======================================"

    if ! command -v uv &> /dev/null; then
        print_error "uv not found. Install it first: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi

    # Install the tool via uv
    print_info "Installing choosr with uv tool install..."
    uv tool install . --reinstall
    print_success "choosr installed to ~/.local/bin/choosr"

    # Install icon
    local icon_src="$(dirname "$0")/src/choosr/choosr-icon.svg"
    local icon_dir="$HOME/.local/share/icons/hicolor/scalable/apps"
    mkdir -p "$icon_dir"
    cp "$icon_src" "$icon_dir/choosr.svg"
    print_success "Icon installed: $icon_dir/choosr.svg"

    # Install desktop file
    local apps_dir="$HOME/.local/share/applications"
    mkdir -p "$apps_dir"
    local choosr_bin="$HOME/.local/bin/choosr"
    cat > "$apps_dir/choosr.desktop" << EOF
[Desktop Entry]
Name=Choosr
GenericName=Browser Chooser
Comment=Choose which browser profile to use for links
Exec=$choosr_bin %u
Icon=choosr
Type=Application
Categories=Network;WebBrowser;
MimeType=x-scheme-handler/http;x-scheme-handler/https;x-scheme-handler/ftp;text/html;application/xhtml+xml;
StartupNotify=true
Terminal=false
NoDisplay=false
EOF
    chmod +x "$apps_dir/choosr.desktop"
    print_success "Desktop file installed: $apps_dir/choosr.desktop"

    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database "$apps_dir" 2>/dev/null || true
    fi

    # Set as default browser
    print_info "Setting choosr as default browser..."
    if xdg-settings set default-web-browser choosr.desktop; then
        print_success "Choosr is now the default browser"
    else
        print_warning "Could not set default browser automatically"
        print_info "Set it manually: xdg-settings set default-web-browser choosr.desktop"
    fi

    echo
    echo "=================================================="
    echo -e "${GREEN}Installation completed successfully!${NC}"
    echo "=================================================="
    echo
    echo "Verify: xdg-settings get default-web-browser"
    echo "Test:   choosr https://example.com"
}

main "$@"
