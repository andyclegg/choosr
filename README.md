# Choosr

A browser profile selector that lets you choose which browser profile to use when opening URLs. Acts as a default browser handler with a modern Qt/QML interface.

## Installation

```bash
# Install dependencies
uv sync

# Install system-wide
./install.sh

# Set as default browser
xdg-settings set default-web-browser choosr.desktop
```

## Usage

```bash
# Open URL with profile selector
choosr https://example.com

# Rescan browser profiles
choosr --rescan-browsers

# Enable debug logging
choosr --debug https://example.com

# Or use environment variable
CHOOSR_DEBUG=1 choosr https://example.com
```

## Configuration

Choosr stores configuration in `~/.choosr.yaml`. On first run, it auto-discovers browser profiles and creates a default config.

### Config Structure

```yaml
browser_profiles:
  chrome-work:
    browser: chrome
    profile_id: Profile 1
    name: Work
    email: work@company.com
  firefox-personal:
    browser: firefox
    profile_id: default
    name: Personal

urls:
  - match: "*.company.com"
    profile: chrome-work
  - match: "*.github.com"
    profile: chrome-work
  - match: "facebook.com"
    profile: firefox-personal
```

### Pattern Syntax

URL patterns use fnmatch glob syntax:

| Pattern | Matches |
|---------|---------|
| `*.example.com` | `foo.example.com`, `bar.example.com` |
| `example.com` | Only `example.com` exactly |
| `*google*` | Any domain containing "google" |
| `????.com` | Four-letter .com domains |

## Troubleshooting

### Debug Mode

Enable debug logging to see detailed information:

```bash
choosr --debug https://example.com
# or
CHOOSR_DEBUG=1 choosr https://example.com
```

### Profile Not Found

If a profile is missing, rescan browsers:

```bash
choosr --rescan-browsers
```

### Browser Won't Launch

1. Check debug output for error messages
2. Verify the browser is installed: `which google-chrome` or `which firefox`
3. Check profile exists in browser's profile manager

### GUI Doesn't Appear

1. Ensure Qt/PySide6 is installed: `uv sync`
2. Check for errors: `choosr --debug https://example.com`
3. Verify display: `echo $DISPLAY`

## Environment Variables

| Variable | Description |
|----------|-------------|
| `CHOOSR_DEBUG` | Set to `1` to enable debug logging |
| `CHOOSR_TIMEOUT` | GUI timeout in milliseconds (default: 300000 = 5 min) |

## Uninstallation

```bash
./uninstall.sh
```

Note: Configuration file `~/.choosr.yaml` is preserved. Delete manually if desired.
