#!/bin/bash
# Uninstallation script for Choosr browser selector

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Remove choosr installation
main() {
    echo "Uninstalling Choosr Browser Selector..."
    echo "======================================="
    
    # Remove desktop file
    local desktop_file="$HOME/.local/share/applications/choosr.desktop"
    if [[ -f "$desktop_file" ]]; then
        rm "$desktop_file"
        print_success "Removed desktop file: $desktop_file"
    else
        print_info "Desktop file not found: $desktop_file"
    fi
    
    # Remove installation directory
    local install_dir="$HOME/.local/share/choosr"
    if [[ -d "$install_dir" ]]; then
        rm -rf "$install_dir"
        print_success "Removed installation directory: $install_dir"
    else
        print_info "Installation directory not found: $install_dir"
    fi
    
    # Update desktop database
    local apps_dir="$HOME/.local/share/applications"
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database "$apps_dir" 2>/dev/null || true
        print_success "Updated desktop database"
    fi
    
    # Check if choosr was the default browser
    if command -v xdg-settings &> /dev/null; then
        local current_browser
        current_browser=$(xdg-settings get default-web-browser 2>/dev/null || echo "")
        if [[ "$current_browser" == "choosr.desktop" ]]; then
            print_warning "Choosr was set as default browser. You may want to set a new default:"
            echo "   xdg-settings set default-web-browser firefox.desktop"
            echo "   xdg-settings set default-web-browser google-chrome.desktop"
        fi
    fi
    
    echo
    echo "================================================"
    echo -e "${GREEN}Uninstallation completed successfully!${NC}"
    echo "================================================"
    echo
    echo "Note: The choosr configuration file ~/.choosr.yaml was kept."
    echo "Remove it manually if you don't plan to reinstall choosr."
}

main "$@"