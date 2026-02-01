import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import Qt5Compat.GraphicalEffects

Rectangle {
    id: window
    width: 900
    height: Math.min(850, screenHeight * 0.95)  // Taller default, but respect screen limits
    focus: true  // Enable focus to receive key events
    
    // Global keyboard event handling
    Keys.onPressed: function(event) {
        // Check for Ctrl modifier in any key press
        if (event.modifiers & Qt.ControlModifier) {
            window.ctrlKeyPressed = true
        }
        
        // Handle Escape
        if (event.key === Qt.Key_Escape) {
            window.cancelled()
            event.accepted = true
            return
        }
        
        // Handle Enter
        if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
            if (window.selectedProfile !== "" && window.domainPattern.trim() !== "") {
                // Setup timer to delay window closing and trigger animation globally
                selectionDelayTimer.pendingProfileName = window.selectedProfile
                selectionDelayTimer.pendingDomainPattern = window.domainPattern.trim()
                selectionDelayTimer.pendingRememberPattern = window.rememberPattern
                window.animateSelectedProfile = true  // Signal to animate
                selectionDelayTimer.start()
            }
            event.accepted = true
            return
        }
        
        // Handle Arrow Keys for navigation
        if (event.key === Qt.Key_Up) {
            navigateProfile("up")
            event.accepted = true
            return
        }
        
        if (event.key === Qt.Key_Down) {
            navigateProfile("down")
            event.accepted = true
            return
        }
        
        if (event.key === Qt.Key_Left) {
            navigateProfile("left")
            event.accepted = true
            return
        }
        
        if (event.key === Qt.Key_Right) {
            navigateProfile("right")
            event.accepted = true
            return
        }
        
        // Handle Ctrl+0-9 shortcuts
        if (event.modifiers & Qt.ControlModifier) {
            var keyIndex = -1
            if (event.key >= Qt.Key_0 && event.key <= Qt.Key_9) {
                keyIndex = event.key - Qt.Key_0
                launchProfileByIndex(keyIndex)
                event.accepted = true
            }
        }
    }
    
    Keys.onReleased: function(event) {
        // Reset Ctrl state when no modifiers are present
        if (!(event.modifiers & Qt.ControlModifier)) {
            window.ctrlKeyPressed = false
        }
    }
    
    property string currentUrl: ""
    property string currentDomain: ""
    property var profileData: []
    property string selectedProfile: ""
    property int selectedProfileIndex: 0  // Index for keyboard navigation
    property string domainPattern: ""
    property bool warningVisible: false
    property bool rememberPattern: true
    property bool ctrlKeyPressed: false
    property var profileShortcuts: []  // Array to store first 10 profiles for shortcuts
    property string systemTheme: "light"
    property bool animateSelectedProfile: false  // Signal to trigger animation on selected profile
    
    // Screen dimension properties (set by Qt controller)
    property int screenHeight: 1280
    
    // Timer for delaying window close after animation
    Timer {
        id: selectionDelayTimer
        interval: 320  // Match total animation duration (80 + 80 + 80 + 80)
        property string pendingProfileName: ""
        property string pendingDomainPattern: ""
        property bool pendingRememberPattern: false

        onTriggered: {
            var configKey = findProfileConfigKey(pendingProfileName)
            window.profileSelected(configKey, pendingDomainPattern, pendingRememberPattern)
        }
    }
    
    // Watch for profileData changes and rebuild shortcuts
    onProfileDataChanged: {
        buildProfileShortcuts()
    }
    
    signal profileSelected(string profileName, string domainPattern, bool saveChoice)
    signal cancelled()
    
    // Dynamic color scheme based on system theme
    readonly property bool isDarkTheme: systemTheme === "dark"
    
    // Light theme colors
    readonly property color lightBackgroundColor: "#FAFAFA"
    readonly property color lightCardColor: "#FFFFFF"
    readonly property color lightTextPrimaryColor: "#212121"
    readonly property color lightTextSecondaryColor: "#757575"
    readonly property color lightDividerColor: "#E0E0E0"
    readonly property color lightShadowColor: "#00000020"
    readonly property color lightHoverColor: "#F0F0F0"
    readonly property color lightInputBackgroundColor: "#F5F5F5"
    
    // Dark theme colors
    readonly property color darkBackgroundColor: "#121212"
    readonly property color darkCardColor: "#1E1E1E"
    readonly property color darkTextPrimaryColor: "#FFFFFF"
    readonly property color darkTextSecondaryColor: "#AAAAAA"
    readonly property color darkDividerColor: "#333333"
    readonly property color darkShadowColor: "#00000040"
    readonly property color darkHoverColor: "#2A2A2A"
    readonly property color darkInputBackgroundColor: "#2A2A2A"
    
    // Common colors (same for both themes)
    readonly property color primaryColor: "#1976D2"
    readonly property color primaryDarkColor: "#1565C0"
    readonly property color accentColor: "#03DAC6"
    readonly property color errorColor: "#F44336"
    readonly property color warningColor: "#FF9800"
    
    // Active color scheme
    readonly property color backgroundColor: isDarkTheme ? darkBackgroundColor : lightBackgroundColor
    readonly property color cardColor: isDarkTheme ? darkCardColor : lightCardColor
    readonly property color textPrimaryColor: isDarkTheme ? darkTextPrimaryColor : lightTextPrimaryColor
    readonly property color textSecondaryColor: isDarkTheme ? darkTextSecondaryColor : lightTextSecondaryColor
    readonly property color dividerColor: isDarkTheme ? darkDividerColor : lightDividerColor
    readonly property color shadowColor: isDarkTheme ? darkShadowColor : lightShadowColor
    readonly property color hoverColor: isDarkTheme ? darkHoverColor : lightHoverColor
    readonly property color inputBackgroundColor: isDarkTheme ? darkInputBackgroundColor : lightInputBackgroundColor
    
    color: backgroundColor
    
    // Header section
    Rectangle {
        id: headerSection
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: 60
        color: cardColor
        
        // Drop shadow
        layer.enabled: true
        layer.effect: DropShadow {
            verticalOffset: 2
            radius: 4
            samples: 9
            color: shadowColor
        }
        
        RowLayout {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 10
            
            Text {
                text: "Choose a profile for:"
                font.pixelSize: 16
                font.weight: Font.Medium
                color: textPrimaryColor
            }
            
            Text {
                text: window.currentUrl
                font.pixelSize: 16
                font.weight: Font.Bold
                color: primaryColor
                elide: Text.ElideMiddle
                Layout.fillWidth: true
            }
        }
    }
    
    // Domain pattern editing section
    Rectangle {
        id: domainSection
        anchors.top: headerSection.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        height: 110
        color: cardColor
        
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 8
            
            Text {
                text: "URL pattern to remember:"
                font.pixelSize: 14
                font.weight: Font.Medium
                color: window.rememberPattern ? textPrimaryColor : textSecondaryColor
                opacity: window.rememberPattern ? 1.0 : 0.6
                
                Behavior on opacity {
                    NumberAnimation { duration: 150 }
                }
            }
            
            RowLayout {
                Layout.fillWidth: true
                spacing: 12
                
                Rectangle {
                    Layout.fillWidth: true
                    height: 40
                    color: window.rememberPattern ? inputBackgroundColor : dividerColor
                    border.color: window.rememberPattern && domainInput.activeFocus ? primaryColor : dividerColor
                    border.width: window.rememberPattern && domainInput.activeFocus ? 2 : 1
                    radius: 8
                    opacity: window.rememberPattern ? 1.0 : 0.5
                    
                    Behavior on opacity {
                        NumberAnimation { duration: 150 }
                    }
                    
                    Behavior on color {
                        ColorAnimation { duration: 150 }
                    }
                    
                    TextInput {
                        id: domainInput
                        anchors.fill: parent
                        anchors.margins: 12
                        text: window.domainPattern
                        font.pixelSize: 14
                        color: window.rememberPattern ? textPrimaryColor : textSecondaryColor
                        selectByMouse: window.rememberPattern
                        enabled: window.rememberPattern
                        focus: false  // Don't steal focus from global handler
                        
                        onTextChanged: {
                            if (window.rememberPattern) {
                                window.domainPattern = text
                                // Check if pattern matches current domain
                                if (text.trim() !== "" && !matchesPattern(window.currentDomain, text.trim())) {
                                    window.warningVisible = true
                                } else {
                                    window.warningVisible = false
                                }
                            }
                        }
                    }
                }
                
                RowLayout {
                    spacing: 6
                    
                    CheckBox {
                        id: rememberCheckbox
                        checked: window.rememberPattern
                        onCheckedChanged: window.rememberPattern = checked
                        
                        indicator: Rectangle {
                            implicitWidth: 16
                            implicitHeight: 16
                            x: rememberCheckbox.leftPadding
                            y: parent.height / 2 - height / 2
                            radius: 2
                            border.color: rememberCheckbox.checked ? primaryColor : dividerColor
                            border.width: 2
                            color: rememberCheckbox.checked ? primaryColor : "transparent"
                            
                            Behavior on border.color {
                                ColorAnimation { duration: 150 }
                            }
                            
                            Behavior on color {
                                ColorAnimation { duration: 150 }
                            }
                            
                            Text {
                                text: "✓"
                                font.pixelSize: 10
                                color: "white"
                                anchors.centerIn: parent
                                opacity: rememberCheckbox.checked ? 1.0 : 0.0
                                
                                Behavior on opacity {
                                    NumberAnimation { duration: 150 }
                                }
                            }
                        }
                    }
                    
                    Text {
                        text: "Remember"
                        font.pixelSize: 12
                        color: textPrimaryColor
                    }
                }
            }
            
            // Warning message
            Text {
                text: "⚠️ Pattern doesn't match the current URL"
                font.pixelSize: 12
                color: errorColor
                visible: window.warningVisible && window.rememberPattern
                Layout.fillWidth: true
            }
        }
    }
    
    // Profile list section  
    Rectangle {
        id: profileSection
        anchors.top: domainSection.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: 20
        color: cardColor
        radius: 12
        
        // Drop shadow
        layer.enabled: true
        layer.effect: DropShadow {
            verticalOffset: 1
            radius: 3
            samples: 7
            color: shadowColor
        }
        
        ColumnLayout {
            id: profileColumnLayout
            anchors.fill: parent
            anchors.margins: 20
            spacing: 15
            
            Text {
                text: "Select Profile:"
                font.pixelSize: 16
                font.weight: Font.Medium
                color: textPrimaryColor
            }
            
            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 20
                
                // Create columns for each browser
                Repeater {
                    model: window.profileData
                    
                    // Browser column
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.minimumWidth: 350
                        color: "transparent"
                        
                        ColumnLayout {
                            id: browserColumnLayout
                            anchors.fill: parent
                            spacing: 10
                            
                            // Browser header
                            Text {
                                text: modelData.browserName
                                font.pixelSize: 16
                                font.weight: Font.Bold
                                color: textPrimaryColor
                                Layout.fillWidth: true
                                horizontalAlignment: Text.AlignHCenter
                            }
                            
                            // Divider
                            Rectangle {
                                Layout.fillWidth: true
                                height: 1
                                color: dividerColor
                            }
                            
                            // Profile list for this browser
                            ScrollView {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                clip: true
                                
                                Column {
                                    width: parent.width
                                    spacing: 8
                                
                                Repeater {
                                    model: modelData.profiles
                                    
                                    Rectangle {
                                        id: profileRect
                                        width: parent.width
                                        height: 70
                                        radius: 8
                                        border.color: window.selectedProfile === modelData.name ? primaryColor : "transparent"
                                        border.width: 2
                                        
                                        // Animation properties
                                        property bool isAnimating: false
                                        property color animationColor: "transparent"
                                        
                                        // Final color combines hover, animation, and base states
                                        color: isAnimating ? animationColor : (profileMouseArea.containsMouse ? hoverColor : "transparent")
                                        
                                        SequentialAnimation {
                                                id: selectionAnimation
                                                
                                                onStarted: profileRect.isAnimating = true
                                                onFinished: profileRect.isAnimating = false
                                                
                                                // First flash
                                                ColorAnimation {
                                                    target: profileRect
                                                    property: "animationColor"
                                                    to: primaryColor
                                                    duration: 80
                                                    easing.type: Easing.OutCubic
                                                }
                                                
                                                ColorAnimation {
                                                    target: profileRect
                                                    property: "animationColor"
                                                    to: "transparent"
                                                    duration: 80
                                                    easing.type: Easing.InCubic
                                                }
                                                
                                                // Second flash
                                                ColorAnimation {
                                                    target: profileRect
                                                    property: "animationColor"
                                                    to: primaryColor
                                                    duration: 80
                                                    easing.type: Easing.OutCubic
                                                }
                                                
                                                ColorAnimation {
                                                    target: profileRect
                                                    property: "animationColor"
                                                    to: "transparent"
                                                    duration: 80
                                                    easing.type: Easing.InCubic
                                                }
                                            }
                                            
                                            // Watch for global animation trigger
                                            Connections {
                                                target: window
                                                function onAnimateSelectedProfileChanged() {
                                                    if (window.animateSelectedProfile && window.selectedProfile === modelData.name) {
                                                        selectionAnimation.start()
                                                        window.animateSelectedProfile = false  // Reset flag
                                                    }
                                                }
                                            }
                                            
                                            RowLayout {
                                                anchors.fill: parent
                                                anchors.margins: 12
                                                spacing: 15
                                                
                                                // Profile icon
                                                Rectangle {
                                                    width: 40
                                                    height: 40
                                                    radius: 20
                                                    color: modelData.backgroundColor || "#4285F4"
                                                    
                                                    // Profile picture (highest priority)
                                                    Image {
                                                        id: profilePicture
                                                        anchors.centerIn: parent
                                                        width: 36
                                                        height: 36
                                                        source: modelData.iconFilePath ? "file://" + modelData.iconFilePath : ""
                                                        visible: source != "" && status === Image.Ready
                                                        fillMode: Image.PreserveAspectCrop
                                                        smooth: true
                                                        layer.enabled: true
                                                        layer.effect: OpacityMask {
                                                            maskSource: Rectangle {
                                                                width: profilePicture.width
                                                                height: profilePicture.height
                                                                radius: width / 2
                                                            }
                                                        }
                                                    }
                                                    
                                                    // Browser icon fallback
                                                    Image {
                                                        id: browserIcon
                                                        anchors.centerIn: parent
                                                        width: 20
                                                        height: 20
                                                        source: modelData.browserIcon || ""
                                                        visible: !profilePicture.visible && source != ""
                                                        fillMode: Image.PreserveAspectFit
                                                    }
                                                    
                                                    // Text avatar fallback
                                                    Text {
                                                        anchors.centerIn: parent
                                                        text: modelData.name ? modelData.name.charAt(0).toUpperCase() : "?"
                                                        font.pixelSize: 18
                                                        font.weight: Font.Bold
                                                        color: modelData.textColor || "#FFFFFF"
                                                        visible: !profilePicture.visible && !browserIcon.visible
                                                    }
                                                }
                                                
                                                // Profile info
                                                ColumnLayout {
                                                    Layout.fillWidth: true
                                                    spacing: 2
                                                    
                                                    Text {
                                                        text: modelData.name || ""
                                                        font.pixelSize: 14
                                                        font.weight: Font.Medium
                                                        color: modelData.isPrivate ? errorColor : textPrimaryColor
                                                        Layout.fillWidth: true
                                                        elide: Text.ElideRight
                                                    }
                                                    
                                                    // Private mode indicator (text instead of dot)
                                                    Text {
                                                        text: modelData.isPrivate ? "Private Mode" : ""
                                                        font.pixelSize: 11
                                                        color: errorColor
                                                        visible: modelData.isPrivate || false
                                                        Layout.fillWidth: true
                                                    }
                                                }
                                                
                                                
                                                // Keyboard shortcut number (shown when Ctrl is pressed)
                                                Text {
                                                    text: getProfileShortcutIndex(modelData.name) >= 0 ? "[" + getProfileShortcutNumber(modelData.name) + "]" : ""
                                                    font.pixelSize: 14
                                                    font.weight: Font.Bold
                                                    color: primaryColor
                                                    visible: getProfileShortcutIndex(modelData.name) >= 0
                                                    opacity: window.ctrlKeyPressed ? 1.0 : 0.0
                                                    
                                                    Behavior on opacity {
                                                        NumberAnimation {
                                                            duration: 200
                                                            easing.type: Easing.OutCubic
                                                        }
                                                    }
                                                }
                                            }
                                            
                                            MouseArea {
                                                id: profileMouseArea
                                                anchors.fill: parent
                                                hoverEnabled: true
                                                onClicked: {
                                                    window.selectedProfile = modelData.name
                                                    window.selectedProfileIndex = findProfileIndex(modelData.name)
                                                }
                                                onDoubleClicked: {
                                                    window.selectedProfile = modelData.name
                                                    window.selectedProfileIndex = findProfileIndex(modelData.name)
                                                    if (window.domainPattern.trim() !== "") {
                                                        selectionAnimation.start()
                                                        // Setup timer to delay window closing
                                                        selectionDelayTimer.pendingProfileName = modelData.name
                                                        selectionDelayTimer.pendingDomainPattern = window.domainPattern.trim()
                                                        selectionDelayTimer.pendingRememberPattern = window.rememberPattern
                                                        selectionDelayTimer.start()
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            
            // Instructions
            Text {
                text: "↑↓←→ to navigate • Enter/Double-click to launch • Hold Ctrl to show shortcuts (Ctrl+0-9) • Escape to cancel"
                font.pixelSize: 11
                color: textSecondaryColor
                horizontalAlignment: Text.AlignHCenter
                Layout.fillWidth: true
                Layout.topMargin: 10
                wrapMode: Text.WordWrap
            }
        }
    }
    
    
    // Helper function for pattern matching (simplified)
    function matchesPattern(domain, pattern) {
        if (!domain || !pattern) return false
        
        // Simple glob matching - convert * to regex
        var regexPattern = pattern.replace(/\*/g, '.*')
        var regex = new RegExp('^' + regexPattern + '$')
        return regex.test(domain)
    }
    
    // Get profile shortcut index (0-9, -1 if not in first 10)
    function getProfileShortcutIndex(profileName) {
        for (var i = 0; i < Math.min(window.profileShortcuts.length, 10); i++) {
            if (window.profileShortcuts[i] === profileName) {
                return i
            }
        }
        return -1
    }
    
    // Get profile shortcut number display (0-9)
    function getProfileShortcutNumber(profileName) {
        var index = getProfileShortcutIndex(profileName)
        return index >= 0 ? index.toString() : ""
    }
    
    // Launch profile by shortcut index
    function launchProfileByIndex(index) {
        if (index >= 0 && index < window.profileShortcuts.length && window.domainPattern.trim() !== "") {
            var profileName = window.profileShortcuts[index]
            window.selectedProfile = profileName
            window.selectedProfileIndex = index
            
            // Setup timer to delay window closing and trigger animation
            selectionDelayTimer.pendingProfileName = profileName
            selectionDelayTimer.pendingDomainPattern = window.domainPattern.trim()
            selectionDelayTimer.pendingRememberPattern = window.rememberPattern
            window.animateSelectedProfile = true  // Signal to animate
            selectionDelayTimer.start()
        }
    }
    
    // Navigate through profiles with arrow keys (2D grid navigation)
    function navigateProfile(direction) {
        if (window.profileShortcuts.length === 0) return
        
        var newIndex = window.selectedProfileIndex
        
        if (direction === "up" || direction === "down") {
            // Vertical navigation - simple linear navigation
            newIndex = window.selectedProfileIndex + (direction === "down" ? 1 : -1)
            
            // Wrap around
            if (newIndex < 0) {
                newIndex = window.profileShortcuts.length - 1
            } else if (newIndex >= window.profileShortcuts.length) {
                newIndex = 0
            }
        } else if (direction === "left" || direction === "right") {
            // Horizontal navigation - move between browsers/columns
            var currentProfile = window.profileShortcuts[window.selectedProfileIndex]
            var currentBrowserIndex = -1
            var currentProfileInBrowser = -1
            var newBrowserIndex = -1
            
            // Find which browser and position the current profile is in
            var profileIndex = 0
            for (var b = 0; b < profileData.length; b++) {
                var browserData = profileData[b]
                if (browserData && browserData.profiles && browserData.profiles.length > 0) {
                    for (var p = 0; p < browserData.profiles.length && profileIndex < window.profileShortcuts.length; p++) {
                        if (window.profileShortcuts[profileIndex] === currentProfile) {
                            currentBrowserIndex = b
                            currentProfileInBrowser = p
                            break
                        }
                        profileIndex++
                    }
                    if (currentBrowserIndex >= 0) break
                }
            }
            
            if (currentBrowserIndex >= 0) {
                // Move to next/previous browser
                newBrowserIndex = currentBrowserIndex + (direction === "right" ? 1 : -1)
                
                // Wrap around browsers
                if (newBrowserIndex < 0) {
                    newBrowserIndex = profileData.length - 1
                } else if (newBrowserIndex >= profileData.length) {
                    newBrowserIndex = 0
                }
                
                // Find corresponding profile in new browser
                var targetBrowserData = profileData[newBrowserIndex]
                if (targetBrowserData && targetBrowserData.profiles && targetBrowserData.profiles.length > 0) {
                    // Try to stay at same position, or go to last profile if new browser has fewer profiles
                    var targetProfileInBrowser = Math.min(currentProfileInBrowser, targetBrowserData.profiles.length - 1)
                    
                    // Calculate the absolute index
                    newIndex = 0
                    for (var i = 0; i < newBrowserIndex; i++) {
                        var browserProfiles = profileData[i]
                        if (browserProfiles && browserProfiles.profiles) {
                            newIndex += Math.min(browserProfiles.profiles.length, 10 - newIndex) // Max 10 profiles
                        }
                    }
                    newIndex += targetProfileInBrowser
                    
                    // Ensure we don't exceed the shortcuts array
                    if (newIndex >= window.profileShortcuts.length) {
                        newIndex = window.profileShortcuts.length - 1
                    }
                }
            }
        }
        
        window.selectedProfileIndex = Math.max(0, Math.min(newIndex, window.profileShortcuts.length - 1))
        window.selectedProfile = window.profileShortcuts[window.selectedProfileIndex]
    }
    
    // Find index of profile by name
    function findProfileIndex(profileName) {
        for (var i = 0; i < window.profileShortcuts.length; i++) {
            if (window.profileShortcuts[i] === profileName) {
                return i
            }
        }
        return 0
    }

    // Find configKey for a profile by display name
    function findProfileConfigKey(profileName) {
        for (var b = 0; b < profileData.length; b++) {
            var browserData = profileData[b]
            if (browserData && browserData.profiles) {
                for (var i = 0; i < browserData.profiles.length; i++) {
                    var profile = browserData.profiles[i]
                    if (profile.name === profileName) {
                        return profile.configKey
                    }
                }
            }
        }
        return profileName  // Fallback to name if not found
    }
    
    // Build profile shortcuts array
    function buildProfileShortcuts() {
        var shortcuts = []
        var selectedFound = false
        var firstNonPrivateIndex = -1
        
        for (var b = 0; b < profileData.length && shortcuts.length < 10; b++) {
            var browserData = profileData[b]
            if (browserData && browserData.profiles && browserData.profiles.length > 0) {
                for (var i = 0; i < browserData.profiles.length && shortcuts.length < 10; i++) {
                    var profile = browserData.profiles[i]
                    shortcuts.push(profile.name)
                    
                    // Find first non-private profile index
                    if (firstNonPrivateIndex === -1 && !profile.isPrivate) {
                        firstNonPrivateIndex = shortcuts.length - 1
                    }
                    
                    // Select first non-private profile as default (only if none selected yet)
                    if (!selectedFound && !profile.isPrivate && selectedProfile === "") {
                        selectedProfile = profile.name
                        selectedProfileIndex = shortcuts.length - 1
                        selectedFound = true
                    }
                }
            }
        }
        
        window.profileShortcuts = shortcuts
        
        // If no non-private profile found and no profile selected, select first profile
        if (!selectedFound && shortcuts.length > 0 && selectedProfile === "") {
            selectedProfile = shortcuts[0]
            selectedProfileIndex = 0
        }
        
        // If we have a non-private profile, prefer it
        if (firstNonPrivateIndex >= 0 && !selectedFound) {
            selectedProfile = shortcuts[firstNonPrivateIndex]
            selectedProfileIndex = firstNonPrivateIndex
        }
    }
    
    // Find profile rectangle by name (for animation)
    function findProfileRectangle(profileName) {
        // This is a simplified approach - in QML it's complex to find dynamic components
        // The animation will be handled by the MouseArea that triggered the selection
        return null
    }
    
    
    // Initialize when component is completed
    Component.onCompleted: {
        buildProfileShortcuts()
    }
}
