import sys
import unittest

sys.path.insert(0, "../src/main/python/")
from utilities import solid

brush = solid(""""id" "1"
side
{
        "id" "1"
        "plane" "(64 64 -64) (64 -64 64) (64 64 64)"
        "material" "tools/toolsnodraw"
        "uaxis" "[1 0 0 0] 0.25"
        "vaxis" "[0 -1 0 0] 0.25"
        "rotation" "0"
        "lightmapscale" "16"
        "smoothing_groups" "0"
}
side
{
        "id" "2"
        "plane" "(-64 -64 -64) (-64 64 64) (-64 -64 64)"
        "material" "tools/toolsnodraw"
        "uaxis" "[1 0 0 0] 0.25"
        "vaxis" "[0 -1 0 0] 0.25"
        "rotation" "0"
        "lightmapscale" "16"
        "smoothing_groups" "0"
}
side
{
        "id" "3"
        "plane" "(-64 64 -64) (64 64 64) (-64 64 64)"
        "material" "tools/toolsnodraw"
        "uaxis" "[1 0 0 0] 0.25"
        "vaxis" "[0 -1 0 0] 0.25"
        "rotation" "0"
        "lightmapscale" "16"
        "smoothing_groups" "0"
}
side
{
        "id" "4"
        "plane" "(64 -64 -64) (-64 -64 64) (64 -64 64)"
        "material" "tools/toolsnodraw"
        "uaxis" "[1 0 0 0] 0.25"
        "vaxis" "[0 -1 0 0] 0.25"
        "rotation" "0"
        "lightmapscale" "16"
        "smoothing_groups" "0"
}
side
{
        "id" "5"
        "plane" "(64 -64 64) (-64 64 64) (64 64 64)"
        "material" "tools/toolsnodraw"
        "uaxis" "[1 0 0 0] 0.25"
        "vaxis" "[0 -1 0 0] 0.25"
        "rotation" "0"
        "lightmapscale" "16"
        "smoothing_groups" "0"
}
side
{
        "id" "6"
        "plane" "(-64 -64 -64) (64 64 -64) (-64 64 -64)"
        "material" "tools/toolsnodraw"
        "uaxis" "[1 0 0 0] 0.25"
        "vaxis" "[0 -1 0 0] 0.25"
        "rotation" "0"
        "lightmapscale" "16"
        "smoothing_groups" "0"
}
editor
{
        "color" "255 0 255"
        "visgroupshown" "1"
"visgroupautoshown" "1"
}""")

print(brush.__dict__)
