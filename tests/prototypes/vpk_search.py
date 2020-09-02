import vpk
from io import open as fopen
import fnmatch
import re
import sys
import struct

class VPKSearchable(vpk.VPK):
    def __init__(self, vpk_path, read_header_only=True, path_enc='utf-8', fopen=fopen):
        super().__init__(vpk_path, read_header_only=read_header_only, path_enc=path_enc, fopen=fopen)

        # Path for Sound. Unless set, it will default to same path
        self.searchSoundPath = vpk_path

        # Filter for file name
        self.filefilter = []

        self.shaderfilter = []
        # List of shaders
        # Aftershock
        # Cable
        # Character
        # Core 
        # DecalModulate 
        # EyeRefract 
        # Eyes 
        # Infected 
        # JellyFish
        # Lightmapped_4wayBlend
        # LightmappedGeneric
        # LightmappedReflective
        # LightmappedTwoTexture
        # Modulate
        # MonitorScreen
        # MultiBlend
        # Patch
        # Pyro_vision
        # Refract
        # Sky
        # SplineRope
        # SpriteCard
        # Subrect
        # Teeth
        # UnlitGeneric
        # UnlitTwoTexture
        # VertexLitGeneric
        # VolumeCloud
        # VortWarp
        # Water
        # WindowImposter
        # Wireframe
        # WorldTwoTextureBlend
        # WorldVertexTransition

        #What kind of prop can the model be?
        self.modelFilter = []
        #---------------------------------------------------------------------------------
        #                   \   prop_detail    \   prop_static    \ prop_dynamic \    prop_physics    \   prop_ragdoll
        # $staticprop       \   Y              \   Y              \ Optional     \    Optional        \   N
        # prop_data         \   N              \   N              \ N            \    Y               \   Y
        # $collisionjoints  \   N              \   N              \ Optional     \    N               \   Y
        # $collsionmodel    \   N              \   Optional       \ Optional     \    Y               \   N

        # Notes: "Yes" or "No" means that the prop may be removed from the game, or otherwise not work if done incorrectly. 
        # "Optional" means that the code will work and is usually a good idea. 

        # mdl file format
        # int 
        # int 
        # int 
        # char 
        # int 
        # Vector (12 bytes each)
        # Vector 
        # Vector 
        # Vector 
        # Vector 
        # Vector 
        # int flags <--- Binary flags in little-endian order. 
		#               ex (00000001,00000000,00000000,11000000) means flags for position 0, 30, and 31 are set. 

        # model flags: int flag at 
        # $staticprop is 4th position of the flag in mdl. (positions starts from 0)

        # or just use https://github.com/maxdup/mdl-tools 

    def hasFilter(self):
        if (len(self.shaderfilter) == 0) and ():
            return False
        else:
            return True

    def search(self, keyword):
        #returns internal path
        foundnames = []
        for filename in self:
            #fnmatch.fnmatch(filename, f'*{keyword}*')
            if (filename[-3:] in self.filefilter) and (fnmatch.fnmatch(filename, f'*{keyword}*')):
                foundnames.append(filename)

        #additional filter
        outputarray = []
        if self.hasFilter():
            pass

        for path in foundnames:
            outputarray.append(self.get_file(path))
        return foundnames

    def setShaderFilter(self, *kwargs):
        """Sets filters for Material Searching"""
        self.filefilter = []
        self.filefilter.append(kwargs.get("types", None))
        self.shaderfilter = []
        self.shaderfilter.append(kwargs.get("shaders", None))

class PropSimple:
    #Simple MDL parser just to check which type of prop it can be
    def __init__(self, pak, internalPath):
        self.internalPath = internalPath
        self.propTypeflag = 0

        #takes path as parameter
        try:
            self.mdlfile = pak[internalPath]
        except FileNotFoundError:
            self.mdlfile = None

        internalPhypath = internalPath[0:-3] + "phy"
        # phyfile. also path
        try:
            self.phyfile = pak[internalPhypath]
        except FileNotFoundError:
            self.phyfile = None

        if self.mdlfile != None:
            # model flag byte location
            # 4*3 + 1*64 + 4 + 12*6 = 152
            #.seek(152)
            # flag is int
            #.read(4)
            # position for $staticprop is 4
            # 4th position in bits is 16
            self.mdlfile.seek(152)
            spflag = self.mdlfile.read(4)
            print(f"prop flags: {int.from_bytes(spflag,sys.byteorder)}")
            if int.from_bytes(spflag,sys.byteorder) & 16 == 16:
                self.staticprop = True
            else:
                self.staticprop = False
            lines = self.mdlfile.read()
            #read keyvalue 'prop_data' in mdl
            if bytes('prop_data', 'ascii') in lines:
                self.prop_data = True
            else:
                self.prop_data = False
        
        if self.phyfile != None:
            #Does ragdollconstraint in .phy define collision joint?
            self.phyfile.seek(0)
            lines = self.phyfile.read()
            if bytes('ragdollconstraint', 'ascii') in lines:
                self.collisionjoints = True
            else:
                self.collisionjoints = False

    def __str__(self):
        if self.mdlfile == None:
            m1 = "no MDL associated"
        else:
            m1 = "found MDL"
        if self.phyfile == None:
            m2 = "no PHY associated"
        else:
            m2 = "found PHY"

        return f"PropSimple Object for path {self.internalPath}: {m1} and {m2}"
    
    def isStaticProp(self):
        return self.staticprop

    def isPropData(self):
        return self.prop_data

    def isCollisionJoints(self):
        return self.collisionjoints

    def isCollisionModel(self):
        #does the model have .phy?
        if self.phyfile is None:
            # No Collision Model, No Collision Model
            return False
        else:
            return True

    def writePropTypes(self):
        isStaticProp = self.isStaticProp()
        isPropData = self.isPropData()
        isCollisionJoints = self.isCollisionJoints()
        isCollisionModel = self.isCollisionModel()

        if isStaticProp and not isPropData and not isCollisionJoints and not isCollisionModel: # prop_detail
            self.propTypeflag = self.propTypeflag | 8
        if not isStaticProp and isPropData and isCollisionJoints and not isCollisionModel: # prop_ragdoll
            self.propTypeflag = self.propTypeflag | 16
        if isStaticProp and not isPropData and not isCollisionJoints: #prop_static
            self.propTypeflag = self.propTypeflag | 1
        if isPropData and not isCollisionJoints and isCollisionModel: #prop_physics
            self.propTypeflag = self.propTypeflag | 2
        if not isPropData: #prop_dynamic
            self.propTypeflag = self.propTypeflag | 4

def main():
    path = "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Team Fortress 2\\tf\\tf2_misc_dir.vpk"
    #path = "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Portal 2\\portal2\\pak01_dir.vpk"
    pak = VPKSearchable(path)
    pak.filefilter = ["mdl", "vtx"]

    #tf2 props
    #name = pak.search("player/scout.mdl")
    name = pak.search("props_trainyard/beer_keg001.mdl")

    #p2 prop
    #name = pak.search("props/lab_chair/lab_chair.mdl")

    path = name[0]
    propsimple = PropSimple(pak,path)
    print(propsimple)
    print(f"propsimple propdata? {propsimple.isPropData()}")

if __name__ == "__main__":
    main()