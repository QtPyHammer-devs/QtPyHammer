from __future__ import annotations
from typing import List

from . import common


class Brush:
    sides: List[BrushSide]

    def __init__(self):
        ...


class BrushSide(common.BinaryStruct):
    __slots__ = ["origin", "ratio", "material", "uaxis", "vaxis", "rotation",
                 "lightmap_scale", "smoothing_groups"]
    _format = "6i128s9f2h"
    _arrays = {"origin": 3, "arrays": 3, "uaxis": 4, "vaxis": 4}
    # struct BrushSide {
    #     int    plane.origin[3], plane.ratio[3];  /* unpacks into a triangle */
    #     char   material[32];
    # TODO: make material a lookup into a MaterialList lump in the .qph
    #     float  uaxis[4], vaxis[4];  // x y z scalar
    #     float  rotation;
    #     short  lightmap_scale, smoothing_groups; };
    # plane.origin & .ratio explainer:
    # - A = plane.origin + plane.ratio.x
    # - B = plane.origin + plane.ratio.y
    # - C = plane.origin + plane.ratio.z
    # - this way planes are always represented relative to the grid
    # - X+ plane is stored as the ratio 0:1:1
    # - X- as 0:-1:-1
    # ^ this'll be fun
    origin: List[float]
    ratio: List[float]
    material: str
    uaxis: List[float] = (1, 0, 0, .25)
    vaxis: List[float] = (0, 1, 0, .25)  # defaults
    rotation: float = 0
    lightmap_scale: int = 16
    smoothing_groups: int = 0  # bit masks

    def __init__(self, origin, ratio, material, uaxis=uaxis, vaxis=vaxis,
                 rotation=rotation, lightmap_scale=lightmap_scale, smoothing_groups=smoothing_groups):
        super(BrushSide, self).__init__(origin, ratio, material, uaxis, vaxis,
                                        rotation, lightmap_scale, smoothing_groups)
