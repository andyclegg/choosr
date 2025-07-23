import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import Qt5Compat.GraphicalEffects

Rectangle {
    id: window
    width: 800
    height: 650
    
    property string currentUrl: ""
    property string currentDomain: ""
    property var profileData: []
    property string selectedProfile: ""
    property string domainPattern: ""
    property bool warningVisible: false
    property string systemTheme: "light"
    
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
        id: header
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: 80
        color: cardColor
        
        // Drop shadow
        layer.enabled: true
        layer.effect: DropShadow {
            verticalOffset: 2
            radius: 4
            samples: 9
            color: shadowColor
        }
        
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 5
            
            Text {
                text: "Choose a profile for:"
                font.pixelSize: 16
                font.weight: Font.Medium
                color: textPrimaryColor
                Layout.fillWidth: true
            }
            
            Text {
                text: window.currentUrl
                font.pixelSize: 14
                color: primaryColor
                elide: Text.ElideMiddle
                Layout.fillWidth: true
            }
        }
    }
    
    // Domain pattern editing section
    Rectangle {
        id: domainSection
        anchors.top: header.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        height: 120
        color: cardColor
        
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 8
            
            Text {
                text: "Pattern to save:"
                font.pixelSize: 14
                font.weight: Font.Medium
                color: textPrimaryColor
            }
            
            Rectangle {
                Layout.fillWidth: true
                height: 40
                color: inputBackgroundColor
                border.color: domainInput.activeFocus ? primaryColor : dividerColor
                border.width: domainInput.activeFocus ? 2 : 1
                radius: 8
                
                TextInput {
                    id: domainInput
                    anchors.fill: parent
                    anchors.margins: 12
                    text: window.domainPattern
                    font.pixelSize: 14
                    color: textPrimaryColor
                    selectByMouse: true
                    
                    onTextChanged: {
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
            
            // Warning message
            Text {
                text: "⚠️ Pattern doesn't match the current URL"
                font.pixelSize: 12
                color: errorColor
                visible: window.warningVisible
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
        anchors.bottom: buttonSection.top
        anchors.margins: 20
        anchors.bottomMargin: 10
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
                            anchors.fill: parent
                            spacing: 10
                            
                            // Browser header
                            Text {
                                text: modelData.browserName + " (" + modelData.profiles.length + " profiles)"
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
                                            width: parent.width
                                            height: 70
                                            color: profileMouseArea.containsMouse ? hoverColor : "transparent"
                                            radius: 8
                                            border.color: window.selectedProfile === modelData.name ? primaryColor : "transparent"
                                            border.width: 2
                                            
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
                                                    
                                                    // Browser icon or avatar
                                                    Image {
                                                        anchors.centerIn: parent
                                                        width: 20
                                                        height: 20
                                                        source: modelData.browserIcon || ""
                                                        visible: source != ""
                                                        fillMode: Image.PreserveAspectFit
                                                    }
                                                    
                                                    // Fallback to text avatar
                                                    Text {
                                                        anchors.centerIn: parent
                                                        text: modelData.name ? modelData.name.charAt(0).toUpperCase() : "?"
                                                        font.pixelSize: 18
                                                        font.weight: Font.Bold
                                                        color: modelData.textColor || "#FFFFFF"
                                                        visible: !parent.children[0].visible
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
                                                
                                                // Private mode indicator dot
                                                Rectangle {
                                                    width: 8
                                                    height: 8
                                                    radius: 4
                                                    color: errorColor
                                                    visible: modelData.isPrivate || false
                                                }
                                            }
                                            
                                            MouseArea {
                                                id: profileMouseArea
                                                anchors.fill: parent
                                                hoverEnabled: true
                                                onClicked: {
                                                    window.selectedProfile = modelData.name
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
    }
    
    // Button section
    Rectangle {
        id: buttonSection
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        height: 80
        color: cardColor
        
        // Top border
        Rectangle {
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            height: 1
            color: dividerColor
        }
        
        RowLayout {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 15
            
            // Exit button
            Button {
                text: "Exit"
                font.pixelSize: 14
                Layout.preferredWidth: 100
                Layout.preferredHeight: 40
                
                background: Rectangle {
                    color: parent.pressed ? (isDarkTheme ? "#333333" : "#E0E0E0") : (parent.hovered ? hoverColor : "transparent")
                    border.color: dividerColor
                    border.width: 1
                    radius: 8
                }
                
                contentItem: Text {
                    text: parent.text
                    font: parent.font
                    color: textPrimaryColor
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                
                onClicked: window.cancelled()
            }
            
            Item { Layout.fillWidth: true } // Spacer
            
            // Launch button
            Button {
                text: "Launch"
                font.pixelSize: 14
                Layout.preferredWidth: 120
                Layout.preferredHeight: 40
                enabled: window.selectedProfile !== "" && window.domainPattern.trim() !== ""
                
                background: Rectangle {
                    color: parent.enabled ? (parent.pressed ? primaryDarkColor : (parent.hovered ? primaryColor : primaryColor)) : "#CCCCCC"
                    radius: 8
                    opacity: parent.enabled ? 1.0 : 0.6
                }
                
                contentItem: Text {
                    text: parent.text
                    font: parent.font
                    color: parent.enabled ? "white" : "#666666"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                
                onClicked: {
                    if (window.selectedProfile !== "" && window.domainPattern.trim() !== "") {
                        window.profileSelected(window.selectedProfile, window.domainPattern.trim(), false)
                    }
                }
            }
            
            // Remember and launch button
            Button {
                text: "Remember & Launch"
                font.pixelSize: 14
                Layout.preferredWidth: 160
                Layout.preferredHeight: 40
                enabled: window.selectedProfile !== "" && window.domainPattern.trim() !== ""
                
                background: Rectangle {
                    color: parent.enabled ? (parent.pressed ? "#0288D1" : (parent.hovered ? accentColor : accentColor)) : "#CCCCCC"
                    radius: 8
                    opacity: parent.enabled ? 1.0 : 0.6
                }
                
                contentItem: Text {
                    text: parent.text
                    font: parent.font
                    color: parent.enabled ? "white" : "#666666"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                
                onClicked: {
                    if (window.selectedProfile !== "" && window.domainPattern.trim() !== "") {
                        window.profileSelected(window.selectedProfile, window.domainPattern.trim(), true)
                    }
                }
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
    
    // Initialize selected profile
    Component.onCompleted: {
        // Find first non-private profile across all browsers
        for (var b = 0; b < profileData.length; b++) {
            var browserData = profileData[b]
            if (browserData && browserData.profiles && browserData.profiles.length > 0) {
                for (var i = 0; i < browserData.profiles.length; i++) {
                    if (!browserData.profiles[i].isPrivate) {
                        selectedProfile = browserData.profiles[i].name
                        return
                    }
                }
            }
        }
        
        // If no non-private profiles found, select first available profile
        for (var b = 0; b < profileData.length; b++) {
            var browserData = profileData[b]
            if (browserData && browserData.profiles && browserData.profiles.length > 0) {
                selectedProfile = browserData.profiles[0].name
                return
            }
        }
    }
}