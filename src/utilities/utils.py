# utilities/utils.py — misc helper functions
# Currently provides get_offset(tile/entity,size) for grid calculations
# Expand for additional shared helpers as needed
def get_offset(entity, size):
    return entity.rect.x//size[0], entity.rect.y//size[1]
