"""Per .vmf vertex / index buffer manager for PyHammer"""

# Zip-it-Yourself Vertex Assembley
# -- Vertex Format can be whatever
# -- Specs need to be known for pointers & shaders
# -- specs = (size, attributes, order, types)
# Should allow for easy performance tuning

### ----- SOLID BUFFER ----- ###
#|  solid    |  displacement  |#
#|  384MB    |     640MB      |#
### ------------------------ ###

### --- 44 bytes SOLID FACE VERTEX FORMAT --- ###
# -- 12 bytes  (3 float32)  Position 
# -- 12 bytes  (3 float32)  Normal
# -- 8  bytes  (2 float32)  UV
# -- 12 bytes  (3 float32)  Colour
## 1 Tri  == 132 bytes
## 1 Quad == 176 bytes
## 1 Cube == 528 bytes

### --- 44 bytes DISPLACEMENT VERTEX FORMAT --- ###
# -- 12 bytes  (3 float32)  Position
# -- 4  bytes  (1 float32)  Alpha
# -- 8  bytes  (padding)    Padding
# -- 8  bytes  (2 float32)  UV
# -- 12 bytes  (3 float32)  Colour
## Power1 == 396   bytes (9   vertices)
## Power2 == 1100  bytes (25  vertices)
## Power3 == 3564  bytes (81  vertices)
## Power4 == 12716 bytes (289 vertices)

### 100 Power 2 Displacements = 110 000 ~ 110MB
### 100 Power 3 Displacements = 35 6400 ~ 360MB
## 100 Power2 + 100 Power3 = 470MB
## ~ 512MB Displacement VRAM
## 200 Cube Solids = 105 600 ~ 106MB

### ----- HARDWARE USAGE EXAMPLES ----- ###
# --- VMF: pl_upward_d
# -- Displacement Brushes: 558  
# -- Non-Displacement Brushes: 1890
# -- Point Entities: 2438
# USAGE:
# ~ 0% CPU (~30% while loading)
# ~ 410MB VRAM
# ~ 400MB RAM (Resting ~200MB)

class BufferManager:
    # MANAGE BRUSHES AND UNDO MEMORY
    # what do we need to render from buffers
    # models, solids, displacements
    # keep vertices / indices in RAM until on GPU
    # keep maps for mutations
    # defrag, minimise unused holes in buffer
    # big move = fresh buffer
    # don't forget Undo Memory
    # use temp files when not in focus?
    # cooperate with other buffers
    def __init__(self, solids=[], entities=[]):
        """solids = vmf.world.solids
entities = vmf.entities
if only one entity / solid is present wrap it in a list"""
        self.solids = solids
        # Dynamic Draw Buffer
        # Vertices, Indices, Solid -> Indices Sequence Map
        solid_vertices = []
        solid_indices = []
        solid_buffer_map = []
        for solid in solids:
            solid.vertices += ...

        # Dynamic Buffer

        # USE glBufferSubData to change UVs
        # IF a brush's bytesize grows it moves to the end of the buffer
        # IF a new brush fits into an old space
        # REMEMBER what spaces contain old / unused buffer_data
        # when prompted, defrag buffers
        # -- remove unused spaces by moving brushes in the GPU
        # -- try to organise nearby brushes together
        # -- leave as few gaps as possible

    def assemble(self, solid):
        """Convert Solid to Vertex Data"""

    def reload_solid(self, solid_index):
        """Refreshes vertex data for solids[solid_index]"""
        old_offset, old_size = self.solid_buffer_map[solid_index]
        solid = self.solids[solid_index]
        data = self.assemble(solid)
        size = len(data)

### ----- UNDO / REDO ----- ###
## Save last 15 big changes
## Types:
##   Vertex
##   Brush
##   Group (More than 1 Brush)
##   Logic (I / O)
## Each big change to be broken down into smaller actions
