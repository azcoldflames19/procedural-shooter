# src/menu.py — retro-style menu system (currently unused)
# Provides bitmap / default font menu options and navigation logic
# Originally drew Play/Records buttons before being bypassed
import pygame

# Pre-defined 5x7 bitmap font for required capital letters
CHAR_PATTERNS = {
    "A": [
        "01110",
        "10001",
        "10001",
        "11111",
        "10001",
        "10001",
        "10001",
    ],
    "B": [
        "11110",
        "10001",
        "10001",
        "11110",
        "10001",
        "10001",
        "11110",
    ],
    "C": [
        "01110",
        "10001",
        "10000",
        "10000",
        "10000",
        "10001",
        "01110",
    ],
    "D": [
        "11110",
        "10001",
        "10001",
        "10001",
        "10001",
        "10001",
        "11110",
    ],
    "E": [
        "11111",
        "10000",
        "10000",
        "11110",
        "10000",
        "10000",
        "11111",
    ],
    "I": [
        "11111",
        "00100",
        "00100",
        "00100",
        "00100",
        "00100",
        "11111",
    ],
    "L": [
        "10000",
        "10000",
        "10000",
        "10000",
        "10000",
        "10000",
        "11111",
    ],
    "O": [
        "01110",
        "10001",
        "10001",
        "10001",
        "10001",
        "10001",
        "01110",
    ],
    "P": [
        "11110",
        "10001",
        "10001",
        "11110",
        "10000",
        "10000",
        "10000",
    ],
    "R": [
        "11110",
        "10001",
        "10001",
        "11110",
        "10100",
        "10010",
        "10001",
    ],
    "S": [
        "01111",
        "10000",
        "10000",
        "01110",
        "00001",
        "00001",
        "11110",
    ],
    "T": [
        "11111",
        "00100",
        "00100",
        "00100",
        "00100",
        "00100",
        "00100",
    ],
    "Y": [
        "10001",
        "10001",
        "01010",
        "00100",
        "00100",
        "00100",
        "00100",
    ],
    "1": [
        "00100",
        "01100",
        "00100",
        "00100",
        "00100",
        "00100",
        "11111",
    ],
    "F": [
        "11111",
        "10000",
        "10000",
        "11110",
        "10000",
        "10000",
        "10000",
    ],
    "H": [
        "10001",
        "10001",
        "10001",
        "11111",
        "10001",
        "10001",
        "10001",
    ],
    "M": [
        "10001",
        "11011",
        "10101",
        "10101",
        "10001",
        "10001",
        "10001",
    ],
}


def render_retro_text(text: str, cell: int, color_front, color_shadow, outline_color=None, depth_offset=(2, 2)) -> pygame.Surface:
    """Return a surface with retro-styled block letters; supports multi-line input via \n."""
    # Split into lines for wrapping
    lines = text.upper().split("\n")
    spacing = 1  # columns between letters in bitmap space

    line_surfaces: list[pygame.Surface] = []
    max_width_px = 0

    for line in lines:
        # Determine pixel width of this line in glyph-grid units (5 columns per char by default)
        glyph_cols = sum(len(CHAR_PATTERNS.get(ch, [""])[0]) + spacing for ch in line if ch != " ") - spacing
        glyph_cols = max(glyph_cols, 1)
        surf_line = pygame.Surface((glyph_cols * cell, 7 * cell), pygame.SRCALPHA).convert_alpha()

        x_cursor = 0
        for ch in line:
            if ch == " ":
                x_cursor += (5 + spacing) * cell
                continue
            pattern = CHAR_PATTERNS.get(ch)
            if pattern is None:
                continue
            for row, pattern_row in enumerate(pattern):
                for col, pix in enumerate(pattern_row):
                    if pix == "1":
                        rect = pygame.Rect((x_cursor + col * cell, row * cell), (cell, cell))
                        surf_line.fill(color_front, rect)
            x_cursor += (len(pattern[0]) + spacing) * cell

        # Add crisp 1-px outline around glyphs
        if outline_color is not None:
            mask = pygame.mask.from_surface(surf_line)
            outline_px = mask.to_surface(setcolor=outline_color, unsetcolor=(0, 0, 0, 0))
            outlined = pygame.Surface(surf_line.get_size(), pygame.SRCALPHA)
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                outlined.blit(outline_px, (dx, dy))
            outlined.blit(surf_line, (0, 0))
            surf_line = outlined

        # Drop shadow / depth effect
        if depth_offset != (0, 0):
            shadow_w = surf_line.get_width() + depth_offset[0]
            shadow_h = surf_line.get_height() + depth_offset[1]
            shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
            shadow_mask = pygame.mask.from_surface(surf_line)
            shadow_col = shadow_mask.to_surface(setcolor=color_shadow, unsetcolor=(0, 0, 0, 0))
            shadow_surf.blit(shadow_col, depth_offset)
            shadow_surf.blit(surf_line, (0, 0))
            surf_line = shadow_surf

        line_surfaces.append(surf_line)
        max_width_px = max(max_width_px, surf_line.get_width())

    # Stack lines vertically with 3*cell spacing
    line_spacing_px = cell * 3
    total_height_px = sum(s.get_height() for s in line_surfaces) + line_spacing_px * (len(line_surfaces) - 1)
    final_surf = pygame.Surface((max_width_px, total_height_px), pygame.SRCALPHA).convert_alpha()

    y_offset = 0
    for s in line_surfaces:
        final_surf.blit(s, ((max_width_px - s.get_width()) // 2, y_offset))
        y_offset += s.get_height() + line_spacing_px

    return final_surf


class Menu:
    """Simple menu using default pygame font with boxed buttons."""

    def __init__(self, window):
        self.window = window
        self.W, self.H = window.get_size()

        # Menu options
        self.options = ["PLAY", "RECORDS"]
        self.selected = 0

        # Colors and styling based on reference
        self.bg_box = (0, 0, 0)            # black fill
        self.border_default = (120, 120, 120)
        self.border_selected = (255, 255, 255)
        self.outline = (255, 255, 255)
        self.text_color = (255, 255, 255)

        # Fonts
        self.title_font = pygame.font.Font(None, 72)
        self.button_font = pygame.font.Font(None, 48)

        # Prepare title surface (single line for simplicity)
        self.title_surf = self.title_font.render("EDWARD GAME", True, self.text_color)
        self.title_rect = self.title_surf.get_rect(center=(self.W // 2, self.H // 4))

        # Build button rects (will update x/y each draw)
        self.button_rects: list[pygame.Rect] = []
        for opt in self.options:
            txt_surf = self.button_font.render(opt, True, self.text_color)
            rect = txt_surf.get_rect()
            rect.inflate_ip(40, 20)  # padding
            self.button_rects.append(rect)

    # --------------------------------- EVENT HANDLING ---------------------------------
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.options[self.selected]
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            for idx, rect in enumerate(self.button_rects):
                if rect.collidepoint(mx, my):
                    return self.options[idx]
        return None

    # -------------------------------------- DRAW --------------------------------------
    def draw(self):
        # Draw title
        self.window.blit(self.title_surf, self.title_rect.topleft)

        # Vertical layout (stacked)
        spacing = 30
        total_h = sum(rect.height for rect in self.button_rects) + spacing * (len(self.button_rects) - 1)
        start_y = self.H // 2 - total_h // 2

        for idx, (opt, rect) in enumerate(zip(self.options, self.button_rects)):
            rect.centerx = self.W // 2
            rect.y = start_y + idx * (rect.height + spacing)

            # Draw background
            pygame.draw.rect(self.window, self.bg_box, rect)
            # Border width & colour depending on selection
            border_col = self.border_selected if idx == self.selected else self.border_default
            border_width = 4 if idx == self.selected else 2
            pygame.draw.rect(self.window, border_col, rect, border_width)

            # Render text centered inside box
            txt_surf = self.button_font.render(opt, True, self.text_color)
            txt_rect = txt_surf.get_rect(center=rect.center)
            self.window.blit(txt_surf, txt_rect) 