#!/bin/bash
# Uninstallation script for Choosr browser selector

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info()    { echo -e "${BLUE}ℹ${NC} $1"; }
print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1"; }

main() {
    echo "Uninstalling Choosr Browser Selector..."
    echo "======================================="

    # Uninstall the uv tool
    if uv tool list 2>/dev/null | grep -q "^choosr"; then
        uv tool uninstall choosr
        print_success "Removed choosr tool"
    else
        print_info "choosr tool not installed via uv"
    fi

    # Remove desktop file
    local desktop_file="$HOME/.local/share/applications/choosr.desktop"
    if [[ -f "$desktop_file" ]]; then
        rm "$desktop_file"
        print_success "Removed desktop file"
    fi

    # Remove icon
    local icon_file="$HOME/.local/share/icons/hicolor/scalable/apps/choosr.svg"
    if [[ -f "$icon_file" ]]; then
        rm "$icon_file"
        print_success "Removed icon"
    fi

    # Update desktop database
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
    fi

    # Warn if choosr was default browser
    if command -v xdg-settings &> /dev/null; then
        local current_browser
        current_browser=$(xdg-settings get default-web-browser 2>/dev/null || echo "")
        if [[ "$current_browser" == "choosr.desktop" ]]; then
            print_warning "Choosr was the default browser. Set a new one:"
            echo "   xdg-settings set default-web-browser firefox.desktop"
            echo "   xdg-settings set default-web-browser google-chrome.desktop"
        fi
    fi

    echo
    echo "================================================"
    echo -e "${GREEN}Uninstallation completed successfully!${NC}"
    echo "================================================"
    echo
    echo "Note: ~/.choosr.yaml was kept. Remove it manually if no longer needed."
}

main "$@"
