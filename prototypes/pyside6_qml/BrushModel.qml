import QtQuick
import QtQuick3D


Model {
    id: brushModel
    property string colour: "#FF00FF"
    // NOTE: Geometry is initialised externally
    // -- geometry: BrushGeometry { _brush: ... }
    visible: true

    materials: DefaultMaterial {
        diffuseColor: brushModel.colour
        lighting: DefaultMaterial.NoLighting
    }
}
