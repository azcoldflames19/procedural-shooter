# src/game.py — core Game class and world management
# Handles world generation, entity updates, camera, rendering layers, and game state
# Acts as central hub called each frame from main.py
import pygame, random, math
from pygame.math import Vector2 as vec2

from src.tiling.terrain import generate_world_data
from src.tiling.tile import Tile, auto_tile

from src.entities.player import Player
from src.weapon.bullet import BulletManager
from src.entities.enemy import EnemyManager
from src.weapon.ranged import RangeWeapon
from src.effects.shockwave import Shockwave
from src.utilities.camera import Camera
from src.effects.particle import Particle
from src.utilities.cursor import Cursor

from src.utilities.text import TextManager
from src.utilities.utils import *

class Game:
    def __init__(self, window):
        self.window = window
        self.WIDTH, self.HEIGHT = self.window.get_size()
        self.chunk_size = [32, 18]
        self.WORLD_MAP_SIZE = [self.WIDTH//16 * 5, self.HEIGHT//16 * 5]
        self.fade = self.window.copy()

        self.tile_size = 16

        # Background colour (cyan theme)
        self.water_blue = (0, 180, 180)

        self.cursor = Cursor(self.tile_size)
        self.text_manager = TextManager(self.tile_size, (self.WIDTH, self.HEIGHT))
        self.camera = Camera((self.WIDTH, self.HEIGHT), self.tile_size)
        
        self.shockwaves = []
        self.particles = []

        self.chunk_surfs = {} # cached tiles on chunk surfaces only used for rendering
        self.ground_tiles = {}
        self.tiles = {}

        self.load()

        spawn_area =  [pos for pos, tile in self.ground_tiles.items() if tile.tile_type not in ('air', 'edge')]
        self.spawn_area = [pos for pos in spawn_area if self.tiles[pos].tile_type in ('air', 'edge')]
        spawn_point = random.choice([pos for pos in self.spawn_area if ((pos[0] - self.WORLD_MAP_SIZE[0]//2)**2 + (pos[1] - self.WORLD_MAP_SIZE[1]//2)**2)**0.5 < self.WORLD_MAP_SIZE[1]/3])
        self.player = Player(self.tile_size, spawn_point)

        self.game_started = False
        self.lost = False
        self.upgraded = False
        self.wave = 1
        self.enemy_manager = EnemyManager(self.tile_size)
        self.enemy_spawn_rate = 10
        self.spawn_enemies(self.enemy_spawn_rate)

        self.weapon = RangeWeapon(self.tile_size)
        self.bullet_manager = BulletManager(self.tile_size)

        self.radius = 0
        self.fade_in = False
        self.text_manager.queue_text(f"Wave {self.wave}", self.text_manager.BIG_FONT, {'center': (self.WIDTH/2, self.HEIGHT/2)})
    
    def spawn_enemies(self, amount):
        for i in range(amount):
            self.enemy_manager.spawn(random.choice(self.spawn_area))

    def chunking(self, tiles):
        tiles = tiles.copy()
        for pos in tiles:
            # Skip chunking air tiles - let background show through
            if tiles[pos].tile_type == 'air':
                continue
                
            chunk_offset = (pos[0] // self.chunk_size[0], pos[1] // self.chunk_size[1])
            if chunk_offset not in self.chunk_surfs:
                self.chunk_surfs[chunk_offset] = pygame.Surface((self.chunk_size[0] * self.tile_size, self.chunk_size[1] * self.tile_size), pygame.SRCALPHA).convert_alpha()
            
            tiles[pos].draw(self.chunk_surfs[chunk_offset], [chunk_offset[0] * self.chunk_size[0] * self.tile_size, chunk_offset[1] * self.chunk_size[1] * self.tile_size])

    def restart(self):
        self.chunk_surfs = {} # cached tiles on chunk surfaces only used for rendering
        self.ground_tiles = {}
        self.tiles = {}

        self.load()

        spawn_area =  [pos for pos, tile in self.ground_tiles.items() if tile.tile_type not in ('air', 'edge')]
        self.spawn_area = [pos for pos in spawn_area if self.tiles[pos].tile_type in ('air', 'edge')]
        spawn_point = random.choice([pos for pos in self.spawn_area if ((pos[0] - self.WORLD_MAP_SIZE[0]//2)**2 + (pos[1] - self.WORLD_MAP_SIZE[1]//2)**2)**0.5 < self.WORLD_MAP_SIZE[1]/3])
        self.player = Player(self.tile_size, spawn_point)

        self.game_started = False
        self.lost = False
        self.upgraded = False
        self.wave = 1
        self.enemy_manager = EnemyManager(self.tile_size)
        self.enemy_spawn_rate = 10
        self.spawn_enemies(self.enemy_spawn_rate)

        self.weapon = RangeWeapon(self.tile_size)
        self.bullet_manager = BulletManager(self.tile_size)

        self.radius = 0
        self.fade_in = False
        self.text_manager.queue_text(f"Wave {self.wave}", self.text_manager.BIG_FONT, {'center': (self.WIDTH/2, self.HEIGHT/2)})

    def load(self):
        seed = random.randint(0, 256)
        terrain_data = {(-0.3, 1): 'dirt', (-0.5, -0.3): 'dirt2', (-1, -0.5): 'air'} # map data
        tile_data = {(0.2, 1): 'dirt', (0, 0.2): 'dirt2', (-1, 0): 'air'} # tile data
        
        world_data = generate_world_data(self.WORLD_MAP_SIZE, terrain_data, seed)
        obj_data = generate_world_data(self.WORLD_MAP_SIZE, tile_data, seed)

        datas = [world_data, obj_data]
        offices = [self.ground_tiles, self.tiles]

        for i, data in enumerate(datas): # loop through world data and obj data
            for pos in data:
                terrain_type = data[pos]

                if terrain_type == 'dirt' or terrain_type == 'dirt2':
                    
                    # if there is no tile (void | out of world) on top of current tile, make the current tile air tile
                    if (pos[0], pos[1] - 1) not in data:
                        terrain_type = 'air'
                    
                    # if there is no tile (void | out of world) underneath current tile, make the current tile edge tile
                    if (pos[0], pos[1] + 1) not in data:
                        terrain_type = 'edge' if (pos[0], pos[1] - 1) in data and data[(pos[0], pos[1] - 1)] in ['dirt', 'dirt2'] else 'air'
                    
                    # if there is tile underneath dirt tile and it is air tile, make the current tile edge tile
                    elif data[(pos[0], pos[1] + 1)] == 'air':
                        terrain_type = 'edge' if (pos[0], pos[1] - 1) in data and data[(pos[0], pos[1] - 1)] in ['dirt', 'dirt2'] else 'air'

                    # terrain_type = 'dirt2'
            
                offices[i][pos] = Tile(terrain_type, self.tile_size, pos)
 
        # --- Apply outline-distance gradient colouring ---
        from collections import deque

        BASE_COLOUR = (150, 100, 230)  # core purple

        # Collect all dirt positions from ground layer (walkable)
        dirt_positions = [p for p, t in self.ground_tiles.items() if t.tile_type in ("dirt", "dirt2", "edge")]

        # Identify outline (tiles with at least one non-dirt neighbour)
        outline = []
        dirt_set = set(dirt_positions)
        for pos in dirt_positions:
            for off in ((1,0),(-1,0),(0,1),(0,-1)):
                if (pos[0]+off[0], pos[1]+off[1]) not in dirt_set:
                    outline.append(pos)
                    break

        # BFS to compute distance from outline for each dirt tile
        dist = {p: None for p in dirt_positions}
        q = deque()
        for p in outline:
            dist[p] = 0
            q.append(p)

        max_d = 0
        while q:
            p = q.popleft()
            for off in ((1,0),(-1,0),(0,1),(0,-1)):
                nb = (p[0]+off[0], p[1]+off[1])
                if nb in dist and dist[nb] is None:
                    dist[nb] = dist[p] + 1
                    max_d = max(max_d, dist[nb])
                    q.append(nb)

        # Apply gradient to ground_tiles (walkable foreground)
        for pos, gtile in self.ground_tiles.items():
            if pos in dist and dist[pos] is not None and gtile.tile_type in ("dirt", "dirt2", "edge"):
                d = dist[pos]
                t = d / max_d if max_d else 1
                brightness = 0.6 + 0.4 * t
                colour = tuple(int(c * brightness) for c in BASE_COLOUR)
                gtile.image.fill(colour)

        # Give tiles uniform darker purple so background is consistent
        BG_COLOUR = (40, 20, 80)
        for pos, tile in self.tiles.items():
            if tile.tile_type in ("dirt", "dirt2", "edge"):
                tile.image.fill(BG_COLOUR)

        # --------- Create smooth gradient surface for ground layer ---------
        import pygame
        grad_lowres = pygame.Surface((self.WORLD_MAP_SIZE[0], self.WORLD_MAP_SIZE[1])).convert()
        for (x, y), d in dist.items():
            if d is None:
                continue
            t = d / max_d if max_d else 1
            b = 0.4 + 0.4 * t  # overall darker (0.4–0.8)
            colour = tuple(int(c * b) for c in BASE_COLOUR)
            grad_lowres.set_at((x, y), colour)

        # supersample to reduce blockiness
        super_scale = 4  # moderate supersample; avoids excessive memory
        big = pygame.transform.smoothscale(
            grad_lowres,
            (self.WORLD_MAP_SIZE[0] * self.tile_size * super_scale,
             self.WORLD_MAP_SIZE[1] * self.tile_size * super_scale),
        )
        self.gradient_surf = pygame.transform.smoothscale(
            big, (self.WORLD_MAP_SIZE[0] * self.tile_size, self.WORLD_MAP_SIZE[1] * self.tile_size)
        )
        self.gradient_surf.set_alpha(255)

        # --------- Create ocean radial gradient (background) ---------
        ocean_lowres = pygame.Surface((self.WORLD_MAP_SIZE[0], self.WORLD_MAP_SIZE[1])).convert()
        cx, cy = self.WORLD_MAP_SIZE[0]/2, self.WORLD_MAP_SIZE[1]/2
        max_r = (cx**2 + cy**2) ** 0.5

        inner_col = (64, 209, 225)   # light aqua
        mid_col   = (15, 47, 112)    # deep blue
        outer_col = (0, 0, 0)        # near-black

        for x in range(self.WORLD_MAP_SIZE[0]):
            for y in range(self.WORLD_MAP_SIZE[1]):
                dx = x - cx
                dy = y - cy
                t = min(((dx*dx + dy*dy) ** 0.5) / max_r, 1)
                if t < 0.5:
                    # interpolate inner -> mid
                    tt = t*2
                    r = int(inner_col[0] + (mid_col[0]-inner_col[0])*tt)
                    g = int(inner_col[1] + (mid_col[1]-inner_col[1])*tt)
                    b = int(inner_col[2] + (mid_col[2]-inner_col[2])*tt)
                else:
                    tt = (t-0.5)*2
                    r = int(mid_col[0] + (outer_col[0]-mid_col[0])*tt)
                    g = int(mid_col[1] + (outer_col[1]-mid_col[1])*tt)
                    b = int(mid_col[2] + (outer_col[2]-mid_col[2])*tt)
                ocean_lowres.set_at((x, y), (r, g, b))

        ocean_big = pygame.transform.smoothscale(
            ocean_lowres,
            (self.WORLD_MAP_SIZE[0] * self.tile_size * super_scale,
             self.WORLD_MAP_SIZE[1] * self.tile_size * super_scale),
        )
        self.ocean_surf = pygame.transform.smoothscale(
            ocean_big,
            (self.WORLD_MAP_SIZE[0] * self.tile_size, self.WORLD_MAP_SIZE[1] * self.tile_size),
        )

        self.ground_tiles = auto_tile(self.ground_tiles, self.tile_size)
        self.tiles = auto_tile(self.tiles, self.tile_size)
        
        self.chunking(self.ground_tiles)
        self.chunking(self.tiles)

    def draw(self, camera_offset):
        # Clear window with ocean color to prevent black background
        self.window.fill(self.water_blue)  # cyan background
        
        # DEBUG: Draw simple colored rectangles instead of complex surfaces
        # Draw ocean background - full window cyan rectangle (slightly darker)
        pygame.draw.rect(self.window, (0, 150, 150), (0, 0, self.WIDTH, self.HEIGHT))
        
        # Draw terrain background - offset purple rectangle
        pygame.draw.rect(self.window, (120, 80, 180), 
                        (100 - camera_offset[0], 100 - camera_offset[1], 400, 200))
        
        # Original surface rendering (commented out for debug)
        # self.window.blit(self.ocean_surf, (-camera_offset[0], -camera_offset[1]))
        # self.window.blit(self.gradient_surf, (-camera_offset[0], -camera_offset[1]))

        player_chunk_offset = get_offset(self.player, (self.chunk_size[0] * self.tile_size, self.chunk_size[1] * self.tile_size))
        neighbor_offsets = [(-1, -1), (0, -1), (1, -1),
                            (-1, 0), (0, 0), (1, 0),
                            (-1, 1), (0, 1), (1, 1)]

        for offset in neighbor_offsets:
            chunk_offset = (player_chunk_offset[0] + offset[0], player_chunk_offset[1] + offset[1])
            try:
                self.window.blit(self.chunk_surfs[chunk_offset], [chunk_offset[0] * self.chunk_size[0] * self.tile_size - camera_offset[0], chunk_offset[1] * self.chunk_size[1] * self.tile_size - camera_offset[1]])
            except KeyError:
                pass

        self.enemy_manager.draw(self.window, camera_offset)
        self.player.draw(self.window, camera_offset)
        self.bullet_manager.draw(self.window, camera_offset)

        for shockwave in self.shockwaves.copy():
            shockwave.draw(self.window, camera_offset)
            if shockwave.update(self.dt):
                self.shockwaves.remove(shockwave)
        
        for particle in self.particles.copy():
            particle.draw(self.window, camera_offset)
            if particle.update(self.dt):
                self.particles.remove(particle)

        # render player health
        for i in range(self.player.health):
            pygame.draw.rect(self.window, 'red', (10 + i * self.tile_size, 10, self.tile_size/1.5, self.tile_size/1.5))
            pygame.draw.rect(self.window, 'white', (10 + i * self.tile_size, 10, self.tile_size/1.5, self.tile_size/1.5), 1)

    def minimap(self):
        pygame.draw.rect(self.window, (0, 0, 0), (self.WIDTH - self.WORLD_MAP_SIZE[0], 0, self.WORLD_MAP_SIZE[0], self.WORLD_MAP_SIZE[1]), 1)
        for entity in self.enemy_manager.enemies:
            enemy_offset = get_offset(entity, [self.tile_size]*2)
            pygame.draw.rect(self.window, 'white', (enemy_offset[0] + self.WIDTH - self.WORLD_MAP_SIZE[0], enemy_offset[1], 2, 2))
        player_offset = get_offset(self.player, [self.tile_size]*2)
        pygame.draw.rect(self.window, 'blue', (player_offset[0] + self.WIDTH - self.WORLD_MAP_SIZE[0], player_offset[1], 2, 2))

    def entities_collisions(self):
        for entity in self.enemy_manager.enemies:
            for bullet in self.bullet_manager.bullets:
                
                # enemy bullet collision
                if entity.rect.colliderect(bullet.rect):
                    if entity.deduct_health(bullet.damage):
                        self.camera.start_shake(4)
                        self.particles += [Particle((entity.rect.centerx + random.randint(8, 10), entity.rect.centery + random.randint(8, 10)), bullet.angle + random.randint(10, 30) * random.choice([-1, 1]), self.tile_size) for i in range(random.randint(1, 4))]

                        entity.ext_vel = vec2(1, 0).rotate(bullet.angle).normalize() * 4 # knockback
                        entity.get_pursue()

                        if entity.health <= 0:
                            self.shockwaves.append(Shockwave(entity.rect.center, self.tile_size))
                            self.enemy_manager.enemies.remove(entity)

                        bullet.piercing -= 1
                        if bullet.piercing <= 0:
                            self.bullet_manager.bullets.remove(bullet)

            # enemy player collision
            if entity.rect.colliderect(self.player.rect):
                if self.player.deduct_health(entity.damage):
                    self.camera.start_shake(6)
                            
                    dx = entity.rect.centerx - self.player.rect.centerx
                    dy = entity.rect.centery - self.player.rect.centery

                    angle = math.degrees(math.atan2(dy, dx))

                    self.player.ext_vel = vec2(-1, 0).rotate(angle).normalize() * self.tile_size # kb

                    self.game_state()

    def tile_bullet_collision(self):
        for bullet in self.bullet_manager.bullets:
            destroy = bullet.destroy()
            collided = bullet.collision(self.tiles.get(get_offset(bullet, [self.tile_size]*2), None))
            if destroy or collided:
                self.particles += [Particle((bullet.rect.centerx + random.randint(8, 10), bullet.rect.centery + random.randint(8, 10)), bullet.angle + random.randint(10, 30) * random.choice([-1, 1]), self.tile_size) for i in range(random.randint(1, 4))]
                self.bullet_manager.bullets.remove(bullet)

    def game_state(self):
        if self.player.health <= 0:
            self.lost = True
            self.fade_in = True
            self.shockwaves.append(Shockwave(self.player.rect.center, self.tile_size))

    def upgrade(self):
        if len(self.enemy_manager.enemies) <= 0:
            chance = random.randint(0, 2)
            if self.wave % 4 == 0 and self.upgraded == False:
                if chance == 1:
                    if self.bullet_manager.damage < 6:
                        self.bullet_manager.damage += 0.5
                        'Bullets deal more damage'
                        self.text_manager.queue_text("Bullets Damage: +0.5", self.text_manager.BIG_FONT, {'center': (self.WIDTH/2, self.HEIGHT/2 + self.tile_size/2)}, 180)
                elif chance == 2:
                    if self.weapon.cooldown > 4:
                        self.weapon.cooldown -= 1
                        'Reduced weapon cooldown'
                        self.text_manager.queue_text("Weapon Cooldown: -1", self.text_manager.BIG_FONT, {'center': (self.WIDTH/2, self.HEIGHT/2 + self.tile_size/2)}, 180)
                else:
                    if self.player.health < 10:
                        self.player.health += 1
                        "Buffed player health"
                        self.text_manager.queue_text("Player Health: +1", self.text_manager.BIG_FONT, {'center': (self.WIDTH/2, self.HEIGHT/2 + self.tile_size/2)}, 180)

            # not limiting the enemy buffs to make the game harder and challenging overtime
            if self.wave % 2 == 0 and self.upgraded == False:
                if chance == 1:
                    self.enemy_manager.damages.append(self.enemy_manager.damages[-1]+1) # add one damage
                    'enemy deals more damage'
                    self.text_manager.queue_text("Buffed monster attack damage", self.text_manager.BIG_FONT, {'center': (self.WIDTH/2, self.HEIGHT/2 - self.tile_size/2)}, 180)
                elif chance == 2:
                    self.enemy_manager.dash_speed.append(self.enemy_manager.dash_speed[-1]+1)
                    'enemy speed buffed'
                    self.text_manager.queue_text("Buffed monster speed", self.text_manager.BIG_FONT, {'center': (self.WIDTH/2, self.HEIGHT/2 - self.tile_size/2)}, 180)
                else:
                    self.enemy_manager.healths.append(self.enemy_manager.healths[-1]+1)
                    'enemy health buffed'
                    self.text_manager.queue_text("Buffed monster health", self.text_manager.BIG_FONT, {'center': (self.WIDTH/2, self.HEIGHT/2 - self.tile_size/2)}, 180)
                
                self.upgraded = True

    def spawn_wave(self):
        if len(self.enemy_manager.enemies) <= 0:
            if self.enemy_manager.can_spawn():
                self.enemy_spawn_rate = random.randint(5, 10) + self.enemy_spawn_rate
                self.spawn_enemies(self.enemy_spawn_rate)
                self.enemy_manager.spawn_cooldown_timer = self.enemy_manager.spawn_cooldown
                self.wave += 1
                self.upgraded = False
                self.text_manager.queue_text(f"Wave {self.wave}", self.text_manager.BIG_FONT, {'center': (self.WIDTH/2, self.HEIGHT/2)})

    def shoot(self, mx, my, mbutton, camera_offset):
        angle = math.degrees(math.atan2(my + camera_offset[1] - self.player.rect.centery, mx + camera_offset[0] - self.player.rect.centerx))
        if mbutton[0]:
            if self.weapon.shoot():
                self.bullet_manager.add_bullet(self.player.rect.center, angle + random.randint(-3, 3))

                self.player.ext_vel = vec2(-1, 0).rotate(angle).normalize() * 1 # knockback
                if abs(self.player.ext_vel.x) > abs(self.player.ext_vel.y):
                    self.player.scale(0.8, 1)
                else:
                    self.player.scale(1, 0.8)

    def update(self, delta_time):
        self.dt = delta_time
        mx, my = pygame.mouse.get_pos()
        mbutton = pygame.mouse.get_pressed()
                
        camera_offset = self.camera.offset(self.player, self.dt, mx, my)
        self.player.update(self.dt)
        
        if self.game_started and self.lost == False:
            self.shoot(mx, my, mbutton, camera_offset)

            # make all the enemies chase as soon as player moves or shoots
            if len(self.bullet_manager.bullets) > 0 or self.player.rect.topleft != self.player.ori_pos:
                self.enemy_manager.pursued = True

            player_offset = get_offset(self.player, [self.tile_size]*2)
            collide_tiles = []
            for offset in [(-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)]:
                tile_offset = (player_offset[0] + offset[0], player_offset[1] + offset[1])
                if tile_offset in self.ground_tiles:
                    collide_tiles.append(self.ground_tiles[tile_offset]) if self.ground_tiles[tile_offset].tile_type in ['air', 'edge'] else None
                if tile_offset in self.tiles:
                    collide_tiles.append(self.tiles[tile_offset]) if self.tiles[tile_offset].tile_type not in ['air', 'edge'] else None
            self.player.move(collide_tiles)

            self.enemy_manager.update(self.dt, self.player, self.ground_tiles, self.tiles)
            self.weapon.update(self.dt)
            self.bullet_manager.update(self.dt)
            self.tile_bullet_collision()
            self.entities_collisions()

            self.upgrade()
            self.spawn_wave()

        self.draw(camera_offset)
        self.minimap()
        self.cursor.update(self.dt, self.window, (mx, my))
        
        # UI 
        # will only run once at the start of the program
        if self.game_started == False:
            if self.radius < self.WIDTH/2 + self.tile_size * 5:
                self.radius += 10 * self.dt
            else:
                self.game_started = True

        if self.lost:
            # fade in 
            if self.fade_in:
                if self.radius > 0:
                    self.radius -= 10 * self.dt
                else:
                    self.text_manager.queue_text("You Died", self.text_manager.BIG_FONT, {'center': (self.WIDTH/2, self.HEIGHT/2 - self.tile_size)}, None)
                    self.text_manager.queue_text("Press R to restart", self.text_manager.BIG_FONT, {'center': (self.WIDTH/2, self.HEIGHT/2 + self.tile_size)}, None)
                    self.text_manager.queue_text("Thank you for playing!", self.text_manager.SMALL_FONT, {'center': (self.WIDTH/2, self.HEIGHT - self.tile_size)}, None)

            # fade out
            else:
                if self.radius < self.WIDTH/2 + self.tile_size * 5:
                    self.radius += 10 * self.dt
                else:
                    self.lost = False

        if self.game_started == False or self.lost:      
            self.fade.fill(self.water_blue)  # Use cyan for fade bg
            self.fade.set_colorkey((255, 255, 255))
            pygame.draw.circle(self.fade, (255, 255, 255), (self.WIDTH/2, self.HEIGHT/2), self.radius)
            self.window.blit(self.fade, (0, 0))

        self.text_manager.draw(self.window, self.dt)

    def event_controls(self, event):
        if event.type == pygame.KEYUP:
            self.player.keyup(event.key)

        if event.type == pygame.KEYDOWN:
            self.player.keydown(event.key)
            if self.text_manager.need_input:
                if event.key == pygame.K_r:
                    self.fade_in = False
                    self.text_manager.render_queue.clear()
                    self.restart()
