from io import open as fopen
import fnmatch
import sys

import vpk


class VPKSearchable(vpk.VPK):
    def __init__(self, vpk_path, read_header_only=True, path_enc="utf-8", fopen=fopen):
        super().__init__(vpk_path, read_header_only=read_header_only, path_enc=path_enc, fopen=fopen)

        # Path for Sound. Unless set, it will default to same path
        self.searchSoundPath = vpk_path

        # Filter for file name
        self.filefilter = []

        self.shaderfilter = []
        # shaders = ["Aftershock", "Cable", "Character", "Core", "DecalModulate",
        #            "EyeRefract", "Eyes", "Infected", "JellyFish", "Lightmapped_4wayBlend",
        #            "LightmappedGeneric", "LightmappedReflective", "LightmappedTwoTexture",
        #            "Modulate", "MonitorScreen", "MultiBlend", "Patch", "Pyro_vision",
        #            "Refract", "Sky", "SplineRope", "SpriteCard", "Subrect",
        #            "Teeth", "UnlitGeneric", "UnlitTwoTexture", "VertexLitGeneric",
        #            "VolumeCloud",  "VortWarp", "Water", "WindowImposter",
        #            "Wireframe", "WorldTwoTextureBlend", "WorldVertexTransition"]

        # What kind of prop can the model be?
        self.modelFilter = []
        # -------------------------------------------------------------------------------------------------------------
        #                   \   prop_detail    \   prop_static    \ prop_dynamic \    prop_physics    \   prop_ragdoll
        # $staticprop       \   Y              \   Y              \ Optional     \    Optional        \   N
        # prop_data         \   N              \   N              \ N            \    Y               \   Y
        # $collisionjoints  \   N              \   N              \ Optional     \    N               \   Y
        # $collsionmodel    \   N              \   Optional       \ Optional     \    Y               \   N

        # Notes: "Yes" or "No" means that the prop may be removed from the game, or otherwise not work if done incorrectly.
        # "Optional" means that the code will work and is usually a good idea.

        # mdl file format
        # int[3]
        # char
        # int
        # Vector[6] (float[3][6])
        # int flags <--- Binary flags in little-endian order.
        # - (00000001, 00000000, 00000000, 11000000) means flags for position 0, 30, and 31 are set.

        # model flags: int flag at
        # $staticprop is 4th position of the flag in mdl. (positions starts from 0)

        # or just use https://github.com/maxdup/mdl-tools (pre-alpha)

    def hasShaderFilter(self):
        if (len(self.shaderfilter) == 0):
            return False
        else:
            return True

    def search(self, keyword):
        # returns internal path
        foundnames = []
        for filename in self:
            # fnmatch.fnmatch(filename, f"*{keyword}*")
            if (filename[-3:] in self.filefilter) and (fnmatch.fnmatch(filename, f"*{keyword}*")):
                foundnames.append(filename)

        return foundnames

    def modelSearch(self, keyword, propsearchflag):
        orgfilefilter = self.filefilter
        self.filefilter = ["mdl"]
        pathlist = self.search(keyword)
        filearray = []
        for path in pathlist:
            filearray.append(PropSimple(self, path))

        outputarray = []
        for prop in filearray:
            if prop.propTypeflag & propsearchflag == propsearchflag:
                print(f"{prop.internalPath} has flag {prop.propTypeflag}")
                outputarray.append(prop.internalPath)

        self.filefilter = orgfilefilter
        return outputarray

    # def setShaderFilter(self, *kwargs):
    #     """Sets filters for Material Searching"""
    #     self.filefilter = []
    #     self.filefilter.append(kwargs.get("types", None))
    #     self.shaderfilter = []
    #     self.shaderfilter.append(kwargs.get("shaders", None))

    def textureSearch(self, keyword):
        # get paths, creates VMTFile class for each names, returns an array of VMTFiles.
        # this should allow easier iteration
        orgfilefilter = self.filefilter
        self.filefilter = ["vmt"]
        pathlist = self.search(keyword)
        # filearray = []
        # for path in pathlist:
        # filearray.append(vmtlib.VmtObject(self,path))

        # revert to original file filter
        self.filefilter = orgfilefilter

        return pathlist


class PropSimple:
    # Simple MDL parser just to check which type of prop it can be
    def __init__(self, pak, internalPath):
        self.internalPath = internalPath
        self.propTypeflag = 0

        # takes path as parameter
        try:
            self.mdlfile = pak[internalPath]
        except KeyError:
            self.mdlfile = None

        internalPhypath = internalPath[0:-3] + "phy"
        # phyfile. also path
        try:
            self.phyfile = pak[internalPhypath]
        except KeyError:
            self.phyfile = None

        if self.mdlfile is not None:
            # model flag byte location
            # 4*3 + 1*64 + 4 + 12*6 = 152
            # .seek(152)
            # flag is int
            # .read(4)
            # position for $staticprop is 4
            # 4th position in bits is 16
            self.mdlfile.seek(152)
            spflag = self.mdlfile.read(4)
            if int.from_bytes(spflag, sys.byteorder) & 16 == 16:
                self.staticprop = True
            else:
                self.staticprop = False
            lines = self.mdlfile.read()
            # read keyvalue "prop_data" in mdl
            if bytes("prop_data", "ascii") in lines:
                self.prop_data = True
            else:
                self.prop_data = False

        if self.phyfile is not None:
            self.collisionmodel = True
            # Does ragdollconstraint in .phy define collision joint?
            self.phyfile.seek(0)
            lines = self.phyfile.read()
            if bytes("ragdollconstraint", "ascii") in lines:
                self.collisionjoints = True
            else:
                self.collisionjoints = False
        else:
            self.collisionmodel = False
            self.collisionjoints = False

        self.writePropTypes()
        del self.mdlfile
        del self.phyfile

    def __str__(self):
        if self.mdlfile is None:
            m1 = "no MDL associated"
        else:
            m1 = "found MDL"
        if self.phyfile is None:
            m2 = "no PHY associated"
        else:
            m2 = "found PHY"
        return f"PropSimple Object for path {self.internalPath}: {m1} and {m2}"

    def writePropTypes(self):
        if self.staticprop and not self.prop_data and not self.collisionjoints and not self.collisionmodel:  # prop_detail
            self.propTypeflag = self.propTypeflag | 8
        if not self.staticprop and self.prop_data and self.collisionjoints and not self.collisionmodel:  # prop_ragdoll
            self.propTypeflag = self.propTypeflag | 16
        if self.staticprop and not self.prop_data and not self.collisionjoints:  # prop_static
            self.propTypeflag = self.propTypeflag | 1
        if self.prop_data and not self.collisionjoints and self.collisionmodel:  # prop_physics
            self.propTypeflag = self.propTypeflag | 2
        if not self.prop_data:  # prop_dynamic
            self.propTypeflag = self.propTypeflag | 4


def main():
    path = "D:/SteamLibrary/steamapps/common/Team Fortress 2/tf/tf2_misc_dir.vpk"
    # path = "C:/Program Files (x86)/Steam/steamapps/common/Team Fortress 2/tf/tf2_misc_dir.vpk"
    # path = "C:/Program Files (x86)/Steam/steamapps/common/Portal 2/portal2/pak01_dir.vpk"
    pak = VPKSearchable(path)

    # tf2 props
    # name = pak.search("player/scout.mdl")
    # name = pak.search("props_trainyard/beer_keg001.mdl")
    # paths = pak.modelSearch("", 4)
    paths = pak.textureSearch("concrete")
    for path in paths:
        print(path)

    # p2 prop
    # name = pak.search("props/lab_chair/lab_chair.mdl")

    # path = name[0]
    # propsimple = PropSimple(pak,path)
    # print(propsimple)
    # print(f"propsimple propdata? {propsimple.isPropData()}")


if __name__ == "__main__":
    main()
