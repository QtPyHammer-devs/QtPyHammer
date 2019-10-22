import sys

sys.path.insert(0, "../../src/main/python/utilities")
import vmf


from time import time
times = []
for i in range(16):
    start = time()
    # vmf = dict_from(open('mapsrc/test.vmf'))
    # vmf = dict_from(open('mapsrc/test2.vmf'))
    vmf = dict_from(open('mapsrc/sdk_pl_goldrush.vmf'))
    time_taken = time() - start
    print(f'import took {time_taken:.3f} seconds')
    times.append(time_taken)
print(f'average time: {sum(times) / 16:.3f}')

# filter(lambda x: x['material'] != 'TOOLS/TOOLSNODRAW' and x['material'] != 'TOOLS/TOOLSSKYBOX', all_sides)
# [e['classname'] for e in vmf.dict['entities']]
# all_ents_with_outputs = [e for e in vmf.entities if hasattr(e, 'connections')]
# all_connections = [e.connections for e in all_ents_with_outputs]
# #now add all referenced targetnames to list
# #and create a top-down map of these ents
