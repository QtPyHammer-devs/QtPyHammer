import QtQuick
import QtQuick.Controls
import QtQuick3D


ApplicationWindow {
    id: window
    visible: true
    x: 64; y: 64
    width: 960; height: 576
    title: "3D View"

    menuBar: MenuBar {
        Menu {
            title: "&File"
            Action { text: "&New"; enabled: false }  // TODO: gather shortcuts from QObject <- .ini
            Action { text: "&Open"; enabled: false }
            Action { text: "&Save"; enabled: false }
            Action { text: "Save &As"; enabled: false}
            MenuSeparator {}
            Action { text: "E&xit"; onTriggered: window.close() }
        }
    }

    View3D {
        id: view
        anchors.fill: parent

        PerspectiveCamera { z: 500; }

        Model {
            source: "#Cube"

            NumberAnimation on eulerRotation.x {
                from: 0; to: 360
                duration: 5000
                loops: -1
            }

            NumberAnimation on eulerRotation.y {
                from: 0; to: 360
                duration: 3000
                loops: -1
            }

            materials: DefaultMaterial {
                diffuseColor: "#44EE44"
                lighting: DefaultMaterial.NoLighting
            }
        }
    }
}
