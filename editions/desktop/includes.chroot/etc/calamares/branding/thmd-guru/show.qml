import QtQuick 2.0;
import calamares.slideshow 1.0;

Presentation
{
    id: presentation

    Slide {
        Image {
            id: bg1
            source: "/usr/share/pixmaps/thmd-guru-logo.svg"
            width: 160; height: 160
            anchors.centerIn: parent
        }
        Text {
            anchors.top: bg1.bottom
            anchors.topMargin: 20
            anchors.horizontalCenter: parent.horizontalCenter
            text: "Chào mừng đến với THMD-Guru Linux 1.0 (Genesis)\nTHMD-Guru Global Tech Academy — Learn Deep. Build Real. Secure Everything."
            color: "#D4AF37"
            font.pixelSize: 18
            horizontalAlignment: Text.AlignHCenter
        }
    }
}
