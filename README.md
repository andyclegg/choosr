## Installation

**Prerequisites:**
- Poetry must be installed
- Run `poetry install` to set up dependencies

**Install choosr as a system application:**
```bash
./install.sh
```

This will:
- Create a proper launcher script
- Install the desktop file with correct paths
- Set up the application icon
- Initialize the choosr configuration

**Uninstall:**
```bash
./uninstall.sh
```

## Setting choosr as Default Browser

After installing the desktop file, you can set choosr as your default browser:

**Using the command line:**
```bash
xdg-settings set default-web-browser choosr.desktop
```

**Using GNOME Settings:**
1. Open Settings → Default Applications
2. Select "choosr" as your Web Browser

**Using KDE Settings:**  
1. Open System Settings → Applications → Default Applications
2. Set Web Browser to "choosr"

**Verify the change:**
```bash
xdg-settings get default-web-browser
```

This should return `choosr.desktop` if set correctly.
