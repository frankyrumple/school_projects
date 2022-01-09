import pygame
from pygame.locals import *
import time
from anim_sprite import AnimSprite, AnimTimer

class FPSCounter(AnimSprite):
    
    def __init__(self, x, y, font_name='calibri', font_size=24,
                 color=(255, 255, 255), clock=None, screen=None, update_freq=50):
        super().__init__()
        self.clock = clock
        self.screen = screen
        self.update_freq = update_freq
        self.x = x
        self.y = y
        self.font_name = font_name
        self.font_size = font_size
        self.color = color
        self.text = "FPS OBJECT!"
        self.speed = 0
        self.last_fps = 0
        self.frame_count = 0
        self.time_elapsed = 0.0001

        self.display_bounding_box = False
        
        self.font = pygame.font.SysFont(self.font_name, self.font_size)

        #self.font.set_bold(True)
    
    def redraw_surface(self):
        self.text = "FPS: " + str("%.2f" % float(self.clock.get_fps()))
        #print("redraw..." + self.text)
        image = self.font.render(self.text, True, self.color)  #.convert_alpha()
        tmp = pygame.Surface(image.get_size()).convert() #.convert_alpha()
        # Fill with grey
        tmp.fill((96, 96, 96, 200))
        tmp.blit(image, (0, 0))
        self.image = tmp # .convert_alpha()
        #self.calculate_bounding_box()
        #self.image = pygame.Surface((200, 200))
        #self.image.fill((200, 200, 200))

    def update(self):
        #super().update(time_elapsed_seconds)
        self.redraw_surface()
                
        # if self.update_timer.expired:
        #     self.last_fps = int(self.clock.get_fps())
        #     self.redraw_surface()
        
        # Calculate current FPS
        #self.frame_count += 1
        #self.time_elapsed += time_elapsed_seconds
        
        # curr_fps = int(self.frame_count / self.time_elapsed)
        #curr_fps = int(clock.get_fps())
        
        #print("update..." + str(curr_fps))
        
        # Redraw the surface w the new text if it changed
        # if self.last_fps != curr_fps:
        #     self.last_fps = curr_fps
        #     self.redraw_surface()

    def draw(self):
        super().draw(self.screen)

        
        