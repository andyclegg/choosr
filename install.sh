#!/bin/bash
# Installation script for Choosr browser selector
# This script properly installs choosr as a system application with
# correct desktop integration and default browser capability.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
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

# Check if we're in the right directory
check_directory() {
    if [[ ! -f "choosr.py" ]]; then
        print_error "Must run from the choosr project directory"
        exit 1
    fi
}

# Check if Poetry is available
check_poetry() {
    if ! command -v poetry &> /dev/null; then
        print_error "Poetry not found. Please install Poetry first."
        exit 1
    fi
    
    if ! poetry check &> /dev/null; then
        print_error "Poetry project not properly configured. Run 'poetry install' first."
        exit 1
    fi
}

# Get Poetry virtual environment path
get_venv_path() {
    poetry env info --path
}

# Create installation directory
create_install_dir() {
    local install_dir="$HOME/.local/share/choosr"
    mkdir -p "$install_dir"
    echo "$install_dir"
}

# Create launcher script
create_launcher() {
    local venv_path="$1"
    local install_dir="$2"
    local launcher_path="$install_dir/choosr-launcher"
    local project_dir="$(pwd)"
    
    cat > "$launcher_path" << EOF
#!/bin/bash
# Choosr launcher script
# This script launches choosr from its virtual environment

# Export environment
export PATH="$venv_path/bin:\$PATH"

# Change to the choosr directory
cd "$project_dir"

# Execute choosr with all arguments
exec "$venv_path/bin/python" -m choosr "\$@"
EOF

    chmod +x "$launcher_path"
    echo "$launcher_path"
}

# Create application icon
create_icon() {
    local install_dir="$1"
    local icon_path="$install_dir/choosr-icon.svg"
    
    cat > "$icon_path" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<svg width="64" height="64" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
  <!-- Background -->
  <rect width="64" height="64" rx="8" fill="#1976D2"/>
  
  <!-- Central globe -->
  <circle cx="32" cy="32" r="16" fill="#4CAF50"/>
  <circle cx="32" cy="32" r="16" fill="none" stroke="#2E7D32" stroke-width="1.5"/>
  
  <!-- Globe grid lines -->
  <ellipse cx="32" cy="32" rx="16" ry="8" fill="none" stroke="#2E7D32" stroke-width="1"/>
  <ellipse cx="32" cy="32" rx="16" ry="4" fill="none" stroke="#2E7D32" stroke-width="0.8"/>
  <line x1="16" y1="32" x2="48" y2="32" stroke="#2E7D32" stroke-width="1"/>
  <line x1="32" y1="16" x2="32" y2="48" stroke="#2E7D32" stroke-width="1"/>
  
  <!-- Continents (simple shapes) -->
  <ellipse cx="28" cy="26" rx="3" ry="2" fill="#2E7D32"/>
  <ellipse cx="36" cy="30" rx="2" ry="3" fill="#2E7D32"/>
  <ellipse cx="30" cy="38" rx="4" ry="2" fill="#2E7D32"/>
  
  <!-- Outgoing arrows representing browser choices -->
  <!-- Top-right arrow -->
  <g stroke="#FF9800" stroke-width="2" fill="none">
    <path d="M44 20 L54 10" />
    <path d="M50 10 L54 10 L54 14" />
  </g>
  
  <!-- Right arrow -->
  <g stroke="#FF9800" stroke-width="2" fill="none">
    <path d="M48 32 L58 32" />
    <path d="M54 28 L58 32 L54 36" />
  </g>
  
  <!-- Bottom-right arrow -->
  <g stroke="#FF9800" stroke-width="2" fill="none">
    <path d="M44 44 L54 54" />
    <path d="M50 54 L54 54 L54 50" />
  </g>
  
  <!-- Bottom-left arrow -->
  <g stroke="#FF9800" stroke-width="2" fill="none">
    <path d="M20 44 L10 54" />
    <path d="M14 54 L10 54 L10 50" />
  </g>
  
  <!-- Left arrow -->
  <g stroke="#FF9800" stroke-width="2" fill="none">
    <path d="M16 32 L6 32" />
    <path d="M10 28 L6 32 L10 36" />
  </g>
  
  <!-- Top-left arrow -->
  <g stroke="#FF9800" stroke-width="2" fill="none">
    <path d="M20 20 L10 10" />
    <path d="M14 10 L10 10 L10 14" />
  </g>
  
  <!-- Small browser icons at arrow endpoints -->
  <circle cx="54" cy="10" r="3" fill="#4285F4"/>
  <circle cx="58" cy="32" r="3" fill="#FF5722"/>
  <circle cx="54" cy="54" r="3" fill="#9C27B0"/>
  <circle cx="10" cy="54" r="3" fill="#FF9800"/>
  <circle cx="6" cy="32" r="3" fill="#E91E63"/>
  <circle cx="10" cy="10" r="3" fill="#00BCD4"/>
</svg>
EOF

    # Try to convert to PNG if ImageMagick is available
    local png_path="$install_dir/choosr-icon.png"
    if command -v convert &> /dev/null; then
        if convert "$icon_path" "$png_path" 2>/dev/null; then
            echo "$png_path"
        else
            echo "$icon_path"
        fi
    else
        echo "$icon_path"
    fi
}

# Create desktop file
create_desktop_file() {
    local launcher_path="$1"
    local icon_path="$2"
    local install_dir="$3"
    local desktop_path="$install_dir/choosr.desktop"
    
    cat > "$desktop_path" << EOF
[Desktop Entry]
Name=Choosr
GenericName=Browser Chooser
Comment=Choose which browser profile to use for links
Exec=$launcher_path url %u
Icon=$icon_path
Type=Application
Categories=Network;WebBrowser;
MimeType=x-scheme-handler/http;x-scheme-handler/https;x-scheme-handler/ftp;text/html;application/xhtml+xml;
StartupNotify=true
Terminal=false
NoDisplay=false
EOF

    echo "$desktop_path"
}

# Install desktop file to system
install_desktop_file() {
    local desktop_file="$1"
    local apps_dir="$HOME/.local/share/applications"
    local dest_path="$apps_dir/choosr.desktop"
    
    mkdir -p "$apps_dir"
    cp "$desktop_file" "$dest_path"
    chmod +x "$dest_path"
    
    # Validate desktop file if validator is available
    if command -v desktop-file-validate &> /dev/null; then
        if desktop-file-validate "$dest_path" 2>/dev/null; then
            print_success "Desktop file installed and validated: $dest_path"
        else
            print_warning "Desktop file installed but validation failed: $dest_path"
        fi
    else
        print_success "Desktop file installed: $dest_path"
        print_info "(desktop-file-validate not available for validation)"
    fi
    
    # Update desktop database if available
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database "$apps_dir" 2>/dev/null || true
    fi
    
    echo "$dest_path"
}

# Initialize choosr configuration
init_config() {
    local launcher_path="$1"
    
    if "$launcher_path" init 2>/dev/null; then
        print_success "Initialized choosr configuration"
    else
        print_warning "Failed to initialize config - you may need to run 'choosr init' manually"
    fi
}

# Main installation function
main() {
    echo "Installing Choosr Browser Selector..."
    echo "======================================"
    
    # Pre-flight checks
    check_directory
    check_poetry
    
    # Get environment info
    local venv_path
    venv_path=$(get_venv_path)
    print_info "Using virtual environment: $venv_path"
    
    # Create installation directory
    local install_dir
    install_dir=$(create_install_dir)
    print_info "Installing to: $install_dir"
    
    # Create components
    local launcher_path
    launcher_path=$(create_launcher "$venv_path" "$install_dir")
    print_success "Created launcher: $launcher_path"
    
    local icon_path
    icon_path=$(create_icon "$install_dir")
    print_success "Created icon: $icon_path"
    
    local desktop_file
    desktop_file=$(create_desktop_file "$launcher_path" "$icon_path" "$install_dir")
    print_success "Created desktop file: $desktop_file"
    
    # Install to system
    local installed_desktop
    installed_desktop=$(install_desktop_file "$desktop_file")
    
    # Initialize configuration
    init_config "$launcher_path"
    
    # Success message
    echo
    echo "=================================================="
    echo -e "${GREEN}Installation completed successfully!${NC}"
    echo "=================================================="
    echo
    echo "To set Choosr as your default browser:"
    echo
    echo "1. Using command line:"
    echo "   xdg-settings set default-web-browser choosr.desktop"
    echo
    echo "2. Using GNOME Settings:"
    echo "   Settings → Default Applications → Web Browser → Choosr"
    echo
    echo "3. Using KDE Settings:"
    echo "   System Settings → Applications → Default Applications → Web Browser → Choosr"
    echo
    echo "4. Verify the setting:"
    echo "   xdg-settings get default-web-browser"
    echo
    echo "You can test choosr by running:"
    echo "   $launcher_path url https://example.com"
    echo
    echo "Or simply click on any web link!"
}

# Run main function
main "$@"