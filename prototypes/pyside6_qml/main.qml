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
    title: "Mjölnir"

    menuBar: MenuBar {
        // TODO: assign shortcuts from some Config object
        Menu {
            title: "&File"
            Action { text: "&New"; shortcut: "Ctrl+N"; enabled: false }
            Action { text: "&Open"; shortcut: "Ctrl+O"; onTriggered: fileDialog.open() }
            Action { text: "&Save"; shortcut: "Ctrl+S"; enabled: false }
            Action { text: "Save &As"; shortcut: "Ctrl+Shift+S"; enabled: false}
            MenuSeparator {}
            Action { text: "E&xit"; shortcut: "Ctrl+Q"; onTriggered: window.close() }
        }
    }

    VmfInterface {
        id: vmf
        function openFile(filename) { vmf.source = filename }
        onStatusChanged: {
            console.log("vmf status changed to %1".arg(vmf.status))
            if (vmf.status == "Loaded") {
                brushCollection.loadVmf()
            }
            // TODO: communicate loading errors to the user
        }
    }

    FileDialog {
        id: fileDialog
        // can we reuse this dialog for saving files?
        title: "select a .vmf file"
        // currentFolder: ...  // TODO: get mapsrc dir from configs
        nameFilters: ["Valve Map Files (*.vmf)", "All files (*)"]
        onAccepted: { vmf.openFile(currentFile) }
    }

    // TEST: open .vmf immediately
    // Component.onCompleted: { vmf.openFile("/home/bikkie/Documents/Code/GitHub/QtPyHammer/Team Fortress 2/tf/mapsrc/raycast_test.vmf") }

    // TODO: give the 3D view it's own object in another .qml
    // -- define relationship to active file
    // -- connections to key bindings & program state
    // -- split 3D view into 4 views with view modes etc.
    // -- link to active .vmf file
    View3D {
        id: view
        anchors.fill: parent

        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Color
            // NOTE: QtQuick3D could handle skyboxes itself
            clearColor: "#707070"
        }

        PerspectiveCamera { z: 500 }  // TODO: camera controls

        Node {
            id: brushCollection
            property var brushes: []

            // TODO: methods for handling visible state
            // -- would need to understand groups & selections
            // -- quickHide, unHide etc.

            // TODO: selection bounds -> Brush.from_bounds -> VmfInterface -> BrushGeometry
            function addBrush(geometry, colour) {
                var brushComponent = Qt.createComponent("./BrushModel.qml")
                if (brushComponent.status == Component.Error)
                    console.log(brushComponent.errorString())
                var brush = brushComponent.createObject(brushCollection, {"geometry": geometry, "colour": colour})
                brushes.push(brush)
            }

            function loadVmf() {  // BUG: crashes silently after a few brushes? out of memory?
                console.log("called brushCollection.loadVmf")
                for (var i = 0; i < vmf.brushCount; i++) {
                    brushCollection.addBrush(vmf.brushGeometryAt(i), vmf.brushColourAt(i))
                }
                // TODO: cannot see generated brushes? is this a camera issue or a rendering issue?
            }
        }

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

        // Model {
        //     id: testCube
        //     source: "#Cube"
        //     NumberAnimation on eulerRotation.x {
        //         from: 0; to: 360
        //         duration: 5000
        //         loops: -1
        //     }
        //     NumberAnimation on eulerRotation.y {
        //         from: 0; to: 360
        //         duration: 3000
        //         loops: -1
        //     }
        //     materials: DefaultMaterial {
        //         diffuseColor: "#44EE44"
        //         lighting: DefaultMaterial.NoLighting
        //     }
        // }
    }
}
