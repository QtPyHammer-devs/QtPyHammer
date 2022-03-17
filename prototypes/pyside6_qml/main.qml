import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick3D
import QtQuick3D.Helpers

import Vmf


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
            Action { text: "&Open"; onTriggered: openFileDialog.open() }
            Action { text: "&Save"; enabled: false }
            Action { text: "Save &As"; enabled: false}
            MenuSeparator {}
            Action { text: "E&xit"; onTriggered: window.close() }
        }
    }

    VmfInterface {
        // NOTE: an external singleton that passes geometry to the rendered scene might be better
        id: vmf
    }

    FileDialog {
        id: openFileDialog
        // can we reuse this dialog for saving files?
        title: "select a .vmf file"
        // currentFolder: ...  // TODO: get mapsrc dir from configs
        nameFilters: ["Valve Map Files (*.vmf)", "All files (*)"]
        onAccepted: { console.log("Opening: %1".arg(currentFile)) }
    }

    // TODO: give the 3D view it's own object in another .qml
    // -- define relationship to active file
    // -- connections to key bindings & program state
    // -- split 3D view into 4 views with view modes etc.
    // -- link to active .vmf file
    View3D {
        id: view
        anchors.fill: parent

        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Color  // NOTE: skyboxes are an option
            clearColor: "black"
        }

        PerspectiveCamera { z: 500 }

        Model {
            id: testGrid
            geometry: GridGeometry {
                horizontalStep: 64
                verticalStep: 64
            }
            materials: DefaultMaterial {
                    diffuseColor: "#CECECE"
                    lighting: DefaultMaterial.NoLighting
            }
        }

        Model {
            id: testCube
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
