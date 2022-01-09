
import pygame
from pygame.locals import *
import time
import random
import math

from pygame.surface import Surface
from anim_sprite import AnimTimer

class FONT_CACHE():
    LETTERS = {}
    RGB_PROGRESS = {}

    @staticmethod
    def preload_cache(pyfont, letters):
        for letter in letters:
            FONT_CACHE.render_character(pyfont, letter)

    @staticmethod
    def render_character(pyfont, letter, render_color=(255, 255, 255, 255), color_key=(0, 0, 0, 255) ):
        letter_key = f"{letter}_{render_color}"
        if letter_key not in FONT_CACHE.LETTERS:
            alpha = 255
            if len(render_color) > 3:
                alpha = render_color[3]
            img = pyfont.render(letter, True, render_color, color_key).convert_alpha()
            img.set_alpha(alpha)
            img2 = Surface(img.get_size()).convert()
            img2.set_colorkey(color_key)
            img2.blit(img, (0,0))
            FONT_CACHE.LETTERS[letter_key] = img2
            del img
        
        return FONT_CACHE.LETTERS[letter_key]

    @staticmethod
    def get_rgb_from_progress(start_color, fade_to_color, progress, opacity):
        rgb_key = progress
        if rgb_key not in FONT_CACHE.RGB_PROGRESS:
            # Calculate the current color based on our progress
            r = fade_to_color[0] - start_color[0]
            r *= progress
            r += start_color[0]

            g = fade_to_color[1] - start_color[1]
            g *= progress
            g += start_color[1]

            b = fade_to_color[2] - start_color[2]
            b *= progress
            b += start_color[2]

            # Clamp values so we don't overflow (no < 0 or > 255)
            r = int(sorted((0, r, 255))[1])
            g = int(sorted((0, g, 255))[1])
            b = int(sorted((0, b, 255))[1])

            # Current Alpha
            a = 255 * opacity
            # Clamp value
            a = int(sorted((0, a, 255))[1])

            FONT_CACHE.RGB_PROGRESS[rgb_key] = (r, g, b, a)
        
        return FONT_CACHE.RGB_PROGRESS[rgb_key]

class TailCharacter():
    # A character left as a tail from a falling line

    # Keep a static list of characters
    tail_characters = []

    @staticmethod
    def update_all(time_elapsed_seconds, clock):
        
        # Do update without needless function calls
        for c in TailCharacter.tail_characters:
            # Is it time to refresh the image? Only refresh every ?? msec
            if not c.update_timer.expired:
                continue

            # Update progress
            elapsed_time = pygame.time.get_ticks() - c.created_on

            c.progress = (elapsed_time / c.fade_time)

            if c.progress > 1.0:
                c.destroy()
                continue

            # Flip the progress so we get the fade out in opacity
            c.opacity = 1.0 - c.progress
            c.opacity = sorted((0, c.opacity, 1.0))[1]

        return
    
    @staticmethod
    def draw_all(screen):
        # Draw all tail characters
        blit_list = []
        for c in TailCharacter.tail_characters:
            c.render_surface()

            if not c.current_frame is None:
                b = (c.current_frame, (c.x, c.y))
                blit_list.append(b)

        screen.blits(blit_list)
        return

    def __init__(self, pyfont, text, x, y, fade_time=2000, update_delay=50, draw_delay=30):
        self.pyfont = pyfont
        self.text = text
        self.last_text = ""
        self.x = x
        self.y = y
        self.fade_time = fade_time
        self.created_on = pygame.time.get_ticks() #time.time()
        self.line_height = self.pyfont.get_linesize()
        self.start_color = (255, 255, 255) # Start white
        self.fade_to_color = (0, 255, 0)  # Fade to green
        self.curr_color = self.start_color
        #self.base_frame = FONT_CACHE.render_character(self.pyfont, self.text)
        self.current_frame = None
        self.opacity = 1.0
        self.last_progress = -1.0
        self.progress = 0.0
        
        self.update_timer = AnimTimer(timer_name="tail_update_timer", delay=update_delay)
        self.draw_timer = AnimTimer(timer_name="tail_draw_timer", delay=draw_delay)
        
        # Add this object to the global list
        TailCharacter.tail_characters.append(self)

    def update(self, time_elapsed_seconds, clock):
        # Is it time to refresh the image? Only refresh every ?? msec
        if not self.update_timer.expired:
            return

        # Update progress
        elapsed_time = pygame.time.get_ticks() - self.created_on

        self.progress = (elapsed_time / self.fade_time)

        if self.progress > 1.0:
            self.destroy()
            return

        # Flip the progress so we get the fade out in opacity
        self.opacity = 1.0 - self.progress
        self.opacity = sorted((0, self.opacity, 1.0))[1]
        
        self.render_surface()
        
        return
    
    def render_surface(self):
        if self.last_progress != self.progress or self.current_frame is None or self.draw_timer.expired:
            self.last_progress = self.progress

            r, g, b, a = FONT_CACHE.get_rgb_from_progress(self.start_color, self.fade_to_color, self.progress, self.opacity)

            self.current_frame = FONT_CACHE.render_character(self.pyfont, self.text, (r, g, b, a))

    def draw(self, screen):
        if self.current_frame is None:
            return
        if self.draw_timer.expired:
            screen.blit(self.current_frame, 
               (self.x, self.y))
        
        return
    
    def destroy(self):
        # Remove from global list
        TailCharacter.tail_characters.remove(self)
        del self.current_frame
        del self

    

class FallingLine():
    # A vertical line that will fall down the screen and restart at the top

    # An array of random characters that can be used
    chararray = []

    @staticmethod
    def draw_all(screen, lines):
        # Get all the render lines and send them in one blits together

        blits = []
        for line in lines:
            if line.current_frame is None:
                next
            blit = (line.current_frame, (line.x, line.y))
            blits.append(blit)
            # See if past the end of the screen
            if line.y > line.screen_h:
                line.restart_line()

        screen.blits(blits)

    @staticmethod
    def static_init(pyfont):
        # Make sure our char array is full of characters
        if len(FallingLine.chararray) < 1:
            chars = []

            # Limited font...
            for i in range(0x21, 0x7e):
                # print(i, chr(i))
                if FallingLine.is_chr_printable(pyfont, chr(i)):
                    chars.append(chr(i))
            
            # # Latin Characters
            # for i in range(0x30, 0x80):
            #     # print(i, chr(i))
            #     if FallingLine.is_chr_printable(pyfont, chr(i)):
            #         chars.append(chr(i))
            
            # # Greek Characters
            # for i in range(0x390, 0x3d0):
            #     # print(i, chr(i))
            #     if FallingLine.is_chr_printable(pyfont, chr(i)):
            #         chars.append(chr(i))
            
            # # hebrew characters
            # for i in range(0x5d0, 0x5eb):
            #     # print(i, chr(i))
            #     if FallingLine.is_chr_printable(pyfont, chr(i)):
            #         chars.append(chr(i))
            
            # # cyrillic characters
            # for i in range(0x400, 0x450):
            #     # print(i, chr(i))
            #     if FallingLine.is_chr_printable(pyfont, chr(i)):
            #         chars.append(chr(i))

            # Put chars into the static value
            FallingLine.chararray = chars[:]

            FONT_CACHE.preload_cache(pyfont, FallingLine.chararray)
    
    @staticmethod
    def is_chr_printable(pyfont, chr):
        return True
        ret = False
        # Render this font, see if it prints anything. Ugly, but I don't know a quicker way.
        txt_color = (255, 255, 255)
        bg_color = (0, 0, 0)
        out = pyfont.render("A", 0, txt_color, bg_color).convert_alpha()
        # Look at the pixels for any white character, should be all black if non printable
        out_w, out_h = out.get_size()
        for y in range(0, out_h):
            for x in range(0, out_w):
                pix = out.get_at((x, y))[:3] # Get just RGB, not RGBA
                if pix == txt_color:
                    # print("Found White Pixel")
                    return True
        print("No white pixel found!")
        return ret

    def __init__(self, pyfont, movement_delay=40, update_delay=70, draw_delay=30):
        # Make sure static values are init
        FallingLine.static_init(pyfont)

        self.screen_w = pygame.display.Info().current_w
        self.screen_h = pygame.display.Info().current_h

        # Save the font to be used later
        self.pyfont = pyfont
        # Where to draw
        self.text = random.choice(FallingLine.chararray)
        self.char_width, self.char_height = self.pyfont.size("H")
        self.line_height = self.pyfont.get_linesize()
        self.delay = random.randint(1, 30)
        self.state = "DEAD" # FALLING, DEAD
        self.current_frame = None
        self.direction = 90  # Always fall down - 0 is to the right
        self.opacity = 1.0
        self.color = (255, 255, 255)  # Fade to Green

        self.update_timer = AnimTimer(timer_name="falling_line_timer", delay=update_delay)
        self.movement_timer = AnimTimer(timer_name="falling_line_update_timer", delay=movement_delay)
        self.draw_timer = AnimTimer(timer_name="falling_line_draw_timer", delay=draw_delay)
        
        # Keep track of the last character so we know when it is time to make a new one
        self.last_tail_character = None
        
        self.restart_line()

    def restart_line(self):
        self.x = random.randint(1, self.screen_w + 1)
        self.y = random.randint(1, 500) * -1
        self.speed = random.randint(50, 450)
        self.start_new_tail_character()
        

    def render_surface(self, text, color, opacity=1.0):
        self.current_frame = FONT_CACHE.render_character(self.pyfont, self.text)

        return
    
    def calc_step(self, time_elapsed_seconds):
        # Deal with movement
        time_elapsed_seconds = self.movement_timer.last_elapsed_time
        #print(time_elapsed_seconds)
        # Need radians - not degrees
        radians = (self.direction * math.pi) / 180
        
        # How far did we move this frame?
        if time_elapsed_seconds == 0:
            # prevent divide by 0 error
            time_elapsed_seconds = 0.0000000001
        curr_speed = (self.speed / 1000) * time_elapsed_seconds
        
        # Calculate new X,Y
        new_x = self.x + math.cos(radians) * curr_speed
        new_y = self.y + math.sin(radians) * curr_speed
        
        return new_x, new_y

    def start_new_tail_character(self):
        # Make a new tail character
        tc = TailCharacter(self.pyfont, self.text, self.x, self.y)
        self.last_tail_character = tc
        # Set new character
        self.text = random.choice(FallingLine.chararray)
        # print("new text: " + self.text + " - ")
        # print(ord(self.text))


    def update(self, time_elapsed_seconds, clock):
        # Is it time to refresh the image? Only refresh every ?? msec
        if self.update_timer.expired:
            # Update our image
            self.render_surface(self.text, self.color, self.opacity)

        if self.movement_timer.expired:
            # Move down
            self.x, self.y = self.calc_step(time_elapsed_seconds)

        # Is it time to start a new tail character?
        draw_after = self.line_height * 0.9
        
        if (self.last_tail_character is None) or \
                (self.y - self.last_tail_character.y > draw_after) :
            self.start_new_tail_character()

        return
    
    def draw(self, screen):
        if self.current_frame is None:
            #print("None Frame")
            return
        
        if self.draw_timer.expired:
            screen.blit(self.current_frame, 
                (self.x, self.y))
    
            if self.y > self.screen_h:
                # Past end of screen, restart it
                self.restart_line()
            
        return
