import pygame 
import sys
import os 
from scripts.utils import load_image, load_images 
from scripts.tilemap import Tilemap

RENDER_SCALE = 2.0
MAX_BRUSH_SIZE = 5

class Game:
    def __init__(self):
        pygame.init()
        self.undo_stack = []
        self.redo_stack = []
        self.show_grid = False 
        self.brush_size = 1 
        self.palette_scroll = {}
        pygame.display.set_caption('Platformer Level Editor')
        self.screen = pygame.display.set_mode((640,480))
        self.display = pygame.Surface((320,240))
        
        self.clock = pygame.time.Clock()

        self.assets = {
            'decor' : load_images('tiles/decor'),
            'grass' : load_images('tiles/grass'),
            'large_decor' : load_images('tiles/large_decor'),
            'stone' : load_images('tiles/stone'),
            'spawners' : load_images('tiles/spawners'),
        }
        self.movement = [False, False, False, False]
        self.tilemap = Tilemap(self, tile_size=16)
        self.scroll = [0, 0]

        try:
            self.tilemap.load('default_map.json')
        except FileNotFoundError:
            pass

        self.tile_list = list(self.assets)
        self.tile_group = 0
        self.tile_variant = 0

        self.clicking = False 
        self.right_clicking = False
        self.shift = False
        self.ongrid = True 
    def save_as(self):
        filename = input("Enter filename to save: ")
        if filename:
            if not filename.endswith('.json'):
                filename += '.json'
            path = f"assets/maps/{filename}"
            if os.path.exists(path):
                overwrite = input(f"Do you want to overwrite existing {filename}? y/n: ")
                if overwrite != 'y':
                    return 
            self.tilemap.save('assets/maps/'+filename)
            print(f"Saved map as {filename}")

    def draw_cursor(self):
        pygame.mouse.set_visible(False)

        mpos = pygame.mouse.get_pos()
        world_x = (mpos[0] / RENDER_SCALE) + self.scroll[0]
        world_y = (mpos[1] / RENDER_SCALE) + self.scroll[1]

        if self.ongrid:
            grid_x = int(world_x // self.tilemap.tile_size) * self.tilemap.tile_size
            grid_y = int(world_y // self.tilemap.tile_size) * self.tilemap.tile_size
        else:
            grid_x = world_x
            grid_y = world_y

        current_tile_img = self.assets[self.tile_list[self.tile_group]][self.tile_variant]
        current_tile_img.set_alpha(200)

        self.display.blit(current_tile_img, (grid_x - self.scroll[0], grid_y - self.scroll[1]))
    def draw_tile_palette(self, mpos=None, click=False):
        tile_size = 16
        padding = 2
        palette_height = tile_size + 2*padding
        palette_y = self.display.get_height() - palette_height
        palette_width = len(self.tile_list) * (tile_size + padding) - padding


        self.palette_rects = []

        x_offset = 5
        y_offset = self.display.get_height() - palette_height + padding
        pygame.draw.rect(self.display, (30, 30, 30), (x_offset, palette_y, palette_width, palette_height))

        for i, tile_type in enumerate(self.tile_list):
            variants = self.assets[tile_type]
            #curent variant offset for scroll
            scroll_idx = self.palette_scroll.get(i, 0)
            variant_img = variants[scroll_idx]
            rect = pygame.Rect(x_offset, y_offset, tile_size, tile_size)
            scaled_img = pygame.transform.scale(variant_img, (tile_size, tile_size))
            self.display.blit(scaled_img, rect.topleft)
            self.palette_rects.append((rect, i, scroll_idx))
            x_offset += tile_size + padding

    def undo(self):
        if self.undo_stack:
            snapshot = self.undo_stack.pop()
            self.redo_stack.append({
                "tilemap": self.tilemap.tilemap.copy(),
                "offgrid_tiles": self.tilemap.offgrid_tiles.copy()
            })
            self.tilemap.tilemap.clear()
            self.tilemap.offgrid_tiles.clear()
            self.tilemap.tilemap = snapshot["tilemap"]
            self.tilemap.offgrid_tiles = snapshot["offgrid_tiles"]
    def redo(self):
            if self.redo_stack:
                snapshot = self.redo_stack.pop()
                self.undo_stack.append({
                    "tilemap": self.tilemap.tilemap.copy(),
                    "offgrid_tiles": self.tilemap.offgrid_tiles.copy()
                })
                self.tilemap.tilemap = snapshot["tilemap"]
                self.tilemap.offgrid_tiles = snapshot["offgrid_tiles"]


    def save_state(self):
        snapshot = {
            "tilemap": self.tilemap.tilemap.copy(),
            "offgrid_tiles": self.tilemap.offgrid_tiles.copy()
        }
        self.undo_stack.append(snapshot)

    
    def run(self):
        while True:

            self.display.fill((0,0,0))

            self.scroll[0] += (self.movement[1] - self.movement[0]) * 2
            self.scroll[1] += (self.movement[3] - self.movement[2]) * 2

            render_scroll = (int(self.scroll[0]),int(self.scroll[1]))
            self.tilemap.render(self.display, offset=render_scroll)

            current_tile_img = self.assets[self.tile_list[self.tile_group]][self.tile_variant]
            current_tile_img.set_alpha(255)
            #transparency^

            mpos = pygame.mouse.get_pos()
            mpos = (mpos[0] / RENDER_SCALE, mpos[1] / RENDER_SCALE)

            tile_pos = (int((mpos[0] + self.scroll[0]) // self.tilemap.tile_size), int((mpos[1] + self.scroll[1]) // self.tilemap.tile_size))
            hover_allowed = True
            for rect, _, _ in getattr(self, "palette_rects", []):
                if rect.collidepoint(mpos):
                    hover_allowed = False
                    break

            if hover_allowed:
                if self.ongrid:
                    self.display.blit(current_tile_img, (tile_pos[0] * self.tilemap.tile_size - self.scroll[0], tile_pos[1] * self.tilemap.tile_size - self.scroll[1]))
                else:
                    self.display.blit(current_tile_img, mpos)

            if self.show_grid:
                tile_size = self.tilemap.tile_size
                x_offset = self.scroll[0] % tile_size
                y_offset = self.scroll[1] % tile_size

                for x in range(-x_offset, self.display.get_width(), tile_size):
                    pygame.draw.line(self.display, (50, 50, 50, 0.2), (x, 0), (x, self.display.get_height()))
                for y in range(-y_offset, self.display.get_height(), tile_size):
                    pygame.draw.line(self.display, (50, 50, 50, 0.2), (0, y), (self.display.get_width(), y))
                rect = pygame.Rect(tile_pos[0]*tile_size - self.scroll[0], tile_pos[1]*tile_size - self.scroll[1], tile_size, tile_size)
                pygame.draw.rect(self.display, (200, 200, 200), rect, 2)

            self.draw_tile_palette(mpos, click=self.clicking)

            if self.right_clicking:
                for dx in range(self.brush_size):
                    for dy in range(self.brush_size):
                        x = tile_pos[0] + dx
                        y = tile_pos[1] + dy
                        tile_loc = f"{x};{y}"

                        if tile_loc in self.tilemap.tilemap:
                            self.save_state()
                            del self.tilemap.tilemap[tile_loc]

                        for tile in self.tilemap.offgrid_tiles.copy():
                            tile_img = self.assets[tile['type']][tile['variant']]
                            tile_rect = pygame.Rect(
                                tile['pos'][0] - self.scroll[0],
                                tile['pos'][1] - self.scroll[1],
                                tile_img.get_width(),
                                tile_img.get_height()
                            )
                            cell_rect = pygame.Rect(
                                x * self.tilemap.tile_size - self.scroll[0],
                                y * self.tilemap.tile_size - self.scroll[1],
                                self.tilemap.tile_size,
                                self.tilemap.tile_size
                            )
                            if tile_rect.colliderect(cell_rect):
                                self.save_state()
                                self.tilemap.offgrid_tiles.remove(tile)
                        
            if self.clicking: 
                for dx in range(self.brush_size):
                    for dy in range(self.brush_size):
                        if self.ongrid:
                            pos = tile_pos[0] + dx, tile_pos[1] + dy
                            tile_key = f"{pos[0]};{pos[1]}"
                            self.tilemap.tilemap[tile_key] = {'type': self.tile_list[self.tile_group],'variant': self.tile_variant,'pos': pos}
                        else:
                            pos = mpos[0] + self.scroll[0] + dx * self.tilemap.tile_size, mpos[1] + self.scroll[1] + dy * self.tilemap.tile_size

                            self.tilemap.offgrid_tiles.append({'type': self.tile_list[self.tile_group],'variant': self.tile_variant,'pos': pos})

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mods = pygame.key.get_mods()
                    if event.button == 1 and (mods & pygame.KMOD_SHIFT):

                        pygame.mouse.set_cursor(*pygame.cursors.diamond) 
                        tile_pos = (int((mpos[0] + self.scroll[0]) // self.tilemap.tile_size),
                                    int((mpos[1] + self.scroll[1]) // self.tilemap.tile_size))
                        tile_key = f"{tile_pos[0]};{tile_pos[1]}"
                        if tile_key in self.tilemap.tilemap:
                            tile_info = self.tilemap.tilemap[tile_key]
                            self.tile_group = self.tile_list.index(tile_info['type'])
                            self.tile_variant = tile_info['variant']
                    elif event.button == 1:
                        pygame.mouse.set_cursor(*pygame.cursors.tri_left) 
                        palette = False 
                        for rect, tile_i, variant_i in getattr(self, "palette_rects", []):
                            if rect.collidepoint(mpos):
                                self.tile_group = tile_i
                                self.tile_variant = variant_i
                                palette = True 
                                break
                        if not palette:
                            self.clicking = True 
                            self.save_state()


                    if event.button in (4, 5): 
                        for rect, tile_i, variant_i in getattr(self, "palette_rects", []):
                            if rect.collidepoint(mpos):
                                if event.button == 4:
                                    self.palette_scroll[tile_i] = max(0, self.palette_scroll.get(tile_i, 0) - 1)
                                if event.button == 5:
                                    max_variants = len(self.assets[self.tile_list[tile_i]]) - 1
                                    self.palette_scroll[tile_i] = min(max_variants, self.palette_scroll.get(tile_i, 0) + 1)
                                break

                    if event.button == 3:
                        pygame.mouse.set_cursor(*pygame.cursors.broken_x) 

                        self.right_clicking = True
                    if self.shift:
                        if event.button == 4:
                            self.tile_variant = (self.tile_variant - 1) % len(self.assets[self.tile_list[self.tile_group]])
                        if event.button == 5:
                            self.tile_variant = (self.tile_variant + 1) % len(self.assets[self.tile_list[self.tile_group]])
                            #how does this loop work
                    else:
                        if event.button == 4:
                            self.tile_group = (self.tile_group - 1) % len(self.tile_list)
                            self.tile_variant = 0
                        if event.button == 5:
                            self.tile_group = (self.tile_group + 1) % len(self.tile_list)
                            self.tile_variant = 0

                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        pygame.mouse.set_cursor(*pygame.cursors.arrow)
                        self.clicking = False 
                    if event.button == 3:
                        pygame.mouse.set_cursor(*pygame.cursors.arrow)

                        self.right_clicking = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_z and (event.mod & pygame.KMOD_CTRL) and (event.mod & pygame.KMOD_SHIFT):
                        self.redo()
                    elif event.key == pygame.K_z and (event.mod & pygame.KMOD_CTRL):
                        self.undo()
                    if event.key == pygame.K_g:
                        self.show_grid = not self.show_grid
                    if event.key == pygame.K_EQUALS and (event.mod & pygame.KMOD_SHIFT):
                        self.brush_size = min(self.brush_size + 1, MAX_BRUSH_SIZE)
                    if event.key == pygame.K_MINUS and (event.mod & pygame.KMOD_SHIFT):
                        self.brush_size = max(self.brush_size - 1, 1)

                    if event.key == pygame.K_a:
                        self.movement[0] = True
                    if event.key == pygame.K_d:
                        self.movement[1] = True
                    if event.key == pygame.K_w:
                        self.movement[2] = True
                    if event.key == pygame.K_s and (event.mod & pygame.KMOD_CTRL) and (event.mod & pygame.KMOD_SHIFT):
                        self.save_as()

                    elif event.key == pygame.K_s and (event.mod & pygame.KMOD_CTRL):
                        self.tilemap.save('default_map.json')
                    
                    elif event.key == pygame.K_s:
                        self.movement[3] = True
                    if event.key == pygame.K_LCTRL:
                        self.shift = True
                    if event.key == pygame.K_SPACE:
                        self.ongrid = not self.ongrid 
                    if event.key == pygame.K_t:
                        self.tilemap.autotile()

                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_a:
                        self.movement[0] = False
                    if event.key == pygame.K_d:
                        self.movement[1] = False
                    if event.key == pygame.K_w:
                        self.movement[2] = False
                    if event.key == pygame.K_s:
                        self.movement[3] = False
                    if event.key == pygame.K_LCTRL:
                        self.shift = False


            self.screen.blit(pygame.transform.scale(self.display,self.screen.get_size()),(0,0))
            
            pygame.display.update()
            self.clock.tick(60)

Game().run()
