# main.py — application entry point for "Escape From The Abyss"
# Initializes pygame, creates the Game instance, and runs the async update/render loop
# Adjusts window/FPS and delegates gameplay to src.game.Game
import pygame
import asyncio
from src.game import Game

pygame.init()

window = pygame.display.set_mode([640, 360], pygame.SCALED)
pygame.display.set_caption('1 Blast')

# Pre-render a vertical gradient background (inspired by supplied image palette)

GRADIENT_COLORS = [
    (185, 119, 255),  # bright lavender surface
    (116, 65, 214),   # mid purple depth
    (35, 4, 84)       # deep violet abyss
]


def generate_vertical_gradient(size, colors):
    """Return a Surface with a smooth vertical gradient through the given colors."""
    width, height = size
    surf = pygame.Surface((width, height), pygame.SRCALPHA).convert_alpha()

    segments = len(colors) - 1
    segment_height = height / segments

    for y in range(height):
        # Determine which segment this y falls into
        seg_idx = int(y // segment_height)
        seg_ratio = (y % segment_height) / segment_height

        if seg_idx >= segments:
            seg_idx = segments - 1
            seg_ratio = 1

        c1 = colors[seg_idx]
        c2 = colors[seg_idx + 1]

        r = int(c1[0] + (c2[0] - c1[0]) * seg_ratio)
        g = int(c1[1] + (c2[1] - c1[1]) * seg_ratio)
        b = int(c1[2] + (c2[2] - c1[2]) * seg_ratio)

        pygame.draw.line(surf, (r, g, b), (0, y), (width, y))
    return surf


# Create once and reuse every frame
gradient_bg = generate_vertical_gradient(window.get_size(), GRADIENT_COLORS)

# Start game immediately (no homepage menu)
game = Game(window)
clock = pygame.time.Clock()
font = pygame.font.Font(None, 32)

dt_setting = 60
fps_event = pygame.USEREVENT
pygame.time.set_timer(fps_event, 250)
pygame.mouse.set_visible(0)


async def run():
    running = True

    while running:
        for event in pygame.event.get():
            # Global quit
            if event.type == pygame.QUIT:
                running = False

            # Forward controls straight to game
            game.event_controls(event)

        # Delta time
        dt = clock.tick(1000) / 1000.0
        dt *= dt_setting
        dt = min(dt, 3)

        # Always update game state
        game.update(dt)

        pygame.display.flip()
        await asyncio.sleep(0)


if __name__ == '__main__':
    asyncio.run(run())
    # pygame.quit()
