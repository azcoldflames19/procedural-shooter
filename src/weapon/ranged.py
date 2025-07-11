# weapon/ranged.py — simple ranged weapon cooldown logic
# Spawns bullets via BulletManager and tracks fire rate
# Extend to support multiple weapon types/levels
class RangeWeapon:
    def __init__(self, tile_size):
        self.tile_size = tile_size

        self.cooldown = 12
        self.cooldown_timer = 0
    
    def shoot(self):
        if self.cooldown_timer <= 0:
            self.cooldown_timer = self.cooldown
            return True
        return 

    def update(self, delta_time):
        self.dt = delta_time

        if self.cooldown_timer > 0:
            self.cooldown_timer -= self.dt
