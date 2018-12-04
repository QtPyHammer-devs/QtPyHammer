"""Per .vmf vertex / index buffer manager for PyHammer"""

# Zip-it-Yourself Vertex Assembley
# -- Vertex Format can be whatever
# -- Specs need to be known for pointers & shaders
# -- specs = (size, attributes, order, types)
# Should allow for easy performance tuning

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
