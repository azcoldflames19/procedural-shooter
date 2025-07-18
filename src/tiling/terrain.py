# tiling/terrain.py — procedural terrain generation helpers
# generate_world_data returns noise-based dict mapping positions to tile types
# Utilised by Game.load() to build ground & object layers
import noise
import math

def generate_world_data(world_size, terrain_data:dict, seed):
    tiles = {}
    center_x, center_y = world_size[0] // 2, world_size[1] // 2  # Center of the map
    max_distance = math.sqrt(center_x ** 2 + center_y ** 2)  # Max possible distance from center

    for y in range(world_size[1]):
        for x in range(world_size[0]):
            # Generate Perlin noise
            value = noise.pnoise2(x * 0.05, y * 0.08, octaves=2, persistence=0.5, base=seed)

            # Calculate falloff factor (0 at center, 1 at edges)
            dx, dy = x - center_x, y - center_y
            distance = math.sqrt(dx**2 + dy**2)
            t = distance / max_distance
            falloff = (1 - math.cos(t * math.pi)) * 0.8

            # Apply falloff (reduces terrain values near edges)
            value -= falloff  

            # Determine terrain type
            terrain_type = 'air'
            for data in terrain_data:
                if data[0] <= value <= data[1]:
                    terrain_type = terrain_data[data]
                    break
            tiles[(x, y)] = terrain_type
    
    return tiles
