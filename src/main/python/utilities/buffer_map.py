# (start, length) tuple, a "span"

# can add vertices to wherever
# but indices still need to point to index * vertex format size
# want all our indices together

# V | B | B |       |
# I |B|B|           |

# glBufferSubData / glGetBufferSubData
# args: target_buffer offset(start) size(length) *data

# glDrawElements
# args: mode(GL_TRIANGLES) count(length) type(GL_UNSIGNED_INT) *indices(start)

# Brush:
# Vertices (start, length) in bytes
# Indices (start, length) in bytes / 4
# add vertices.start / vertex.size to each

class span:
    def __init__(self, start, length):
        self.start = start
        self.length = length
        self._end = start + length

    @property
    def end(self):
        return self.start + self.length

    def __add__(self, other):
        if hasattr(other, "__iter_"):
            return sum(other, start=self)
        if self.end < other.start or other.end < self.start:
            return self, other # no overlap
        else:
            start = min([self.start, other.start])
            end = max([self.end, other.end])
            return span(start, end - start)

    def __eq__(self, other):
        if self.start == other.start and self.length == other.length:
            return True
        else:
            return False
    
    def __repr__(self):
        return f"{self.__class__.__name__}({self.start}, {self.length})"

    def __sub__(self, other):
        out = span(self.start, 0)
	if self.start == other.start:
            length_remaining = max([self.length - other.length, 0])
            out = span(other.end, length_remaining)
            if other.end < self.end:
                out = (out, span(other.end, self.end - other.end))
                return out
	elif self.start < other.start < other.end <= self.end:
            out = (self.start, other.start - self.start)
	return out
    # CASES
    # other.start <= self.start, return 1 span (tail)
    # self.start < other.start and self.end < other.end, return 2 spans (head & tail)
    # self.start < other.start and other.end <=

    def is_in(self, other):
        self_end = self.start + self.length
        other_end = other.start + other.length
        if other.start <= self.start < self_end <= other_end:
            return True
        else:
            return False
    

class buffer_map:
    def __init__(self, limit):
        self.free_spaces = [(0, limit)]
        self.brushes = {} # brush_index: span <(start, length)>
        self.brush_zones = [] # merged brush spans

    def free_brush(brush_index):
        start, length = self.brushes[brush_index]
        end = start + length
        for i, zone in enumerate(self.brush_zones[::]):
            zone_start, zone_length = zone
            zone_end = zone_start + zone_length
            if start == zone_start: # start of the zone
                if length == zone_length: # zone is only this brush, remove it
                    self.brush_zones.pop(i)
                    return
                # ends before end of the zone
                self.brush_zones[i] = (end, zone_length - length)
            elif start > zone_start: # starts inside the zone
                self.brush_zones[i] = (zone_start, start - zone_start)
            if zone_end > end: # some of the zone remains
                self.brush_zones.insert(i + 1, (end, zone_end - end))
            # if zone_end < end:
            #   something has gone horribly wrong

    def malloc_brush(brush):
        brush_length = len(brush.vertices)
        index_length = len(brush.indices)
        # find the best slot
        # add vertex offset / vertex size to each index
        # if we're doing as few glBufferSubData calls when assigning ...
        # we need to take these spans and arrange ordered touching spans
        # of each brush when we compile the data to ship to the GPU

##buffer_map.malloc_brush(brush_index) -> (start, length)
##buffer_map.malloc_displacement(brush_index, face_index) -> (start, length)
##
##buffer_map.free_brush(brush_index)
##buffer_map.free_displacement(brush_index, face_index)

if __name__ == "__main__":
    A = span(0, 9) # MAIN
    B = span(3, 3) # OVERLAP MIDDLE
    C = span(-3, 1) # BEFORE, NO OVERLAP
    D = span(12, 1) # AFTER, NO OVERLAP
    E = span(-1, 4) # OVERLAP BEFORE
    F = span(8, 4) # OVERLAP AFTER
    G = span(-1, 12) # OVERLAP ALL
