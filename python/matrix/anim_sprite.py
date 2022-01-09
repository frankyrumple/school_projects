import pygame
from pygame.locals import *
import time
import math

class AnimTimer():
    def __init__(self, timer_name="<TIMER>", delay=200) -> None:
        self.timer_name = timer_name
        self.created_on = pygame.time.get_ticks()
        self.last_update = 0
        self.delay = delay
        self.last_elapsed_time = 0

        pass

    def reset(self):
        curr_ticks = pygame.time.get_ticks()
        # Update last elapsed time
        self.last_elapsed_time = curr_ticks - self.last_update
        if self.last_elapsed_time > self.delay:
            # Don't let last elapsed be too huge
            self.last_elapsed_time = self.delay
        self.last_update = curr_ticks
        #print(self.timer_name + " - reset: " + str(self.last_update))

    @property
    def expired(self):
        ret = False

        curr_ticks = pygame.time.get_ticks()
        if (curr_ticks - self.last_update) > self.delay:
            ret = True
        
        if ret == True:
            # reset timer
            curr_ticks = pygame.time.get_ticks()
            self.last_elapsed_time = curr_ticks - self.last_update
            self.last_update = curr_ticks

        return ret

    def is_expired(self, auto_reset=True):
        ret = False
        curr_ticks = pygame.time.get_ticks()
        #print(self.timer_name + " " + str(curr_ticks) + " - " + str(self.last_update) + " -- " + str(curr_ticks - self.last_update)  + " " + str(self.delay))
        if (curr_ticks - self.last_update) > self.delay:
            # Expired
            ret = True
        
        if auto_reset == True and ret == True:
            # print(self.timer_name + ' resetting')
            #print(self.timer_name + " " + str(curr_ticks) + " - " + str(self.last_update) + " -- " + str(curr_ticks - self.last_update)  + " " + str(self.delay))
            self.reset()
        else:
            #print(self.timer_name + " not resetting")
            #print(self.timer_name + " " + str(curr_ticks) + " - " + str(self.last_update) + " -- " + str(curr_ticks - self.last_update)  + " " + str(self.delay))
            pass
        return ret

class AnimSprite():
    """
    Animated Sprite - used to show a group of images on a timer
    """
    # Static place where all instances of this class can share images
    # with other similar instances - e.g. load explosions once instead
    # of loading images for each explosion
    shared_images = None
    
    # List of active objects of this type - used to help keep track
    # of all bullets or all enemies... When active = False - will clean
    # them up
    active_objects = None
    
    def __init__(self, frame_timer=200, update_timer=200):
        type(self).ensure_static_init()
        self.x = 0
        self.y = 0
        self.speed = 0
        self.scale = 1.0
        self.active = True
        self.direction = 0
        self.display_bounding_box = True

        # How long to show the current frame for
        self.frame_timer = AnimTimer(timer_name="sprite_frame_timer", delay=frame_timer)
        self.update_timer = AnimTimer(timer_name="sprite_update_timer", delay=update_timer)
        
        self.current_frame_index = 0
        self.images = list()
        self.local_bounding_box = Rect(0, 0, 0, 0)
        self.bounding_box = Rect(0, 0, 0, 0)
        self.empty_image = pygame.Surface((128,128)).convert() # pygame.Surface((128,128), flags=SRCALPHA, depth=32).convert_alpha()
        self.empty_image.set_colorkey((0, 0, 0))
        self.image = self.empty_image
        
        # Add this object to the list of objects
        type(self).active_objects.append(self)
    
    def draw(self, screen):
        if screen is None:
            raise Exception("Draw requires a screen!!!")
            return
        
        # Draw the ship at the current location with the
        # current frame
        #print("Drawing: " + str(self.x) + "/" + str(self.y))
        screen.blit(self.get_current_frame(), 
            (self.x, self.y))
        
        #pygame.draw.rect(screen, (255, 0, 0), self.local_bounding_box, 3)
        
        # Draw the bounding box
        if self.display_bounding_box is True:
            pygame.draw.rect(screen, (0, 255, 0), self.bounding_box, 1)
        #if str(type(self)) == "<class 'enemy.Enemy'>":
        #print("BOX: " + str(self.bounding_box))

        # Draw a small area for the X/Y center
        #pygame.draw.rect(screen, (255, 0, 0), Rect(self.x, self.y, 1, 1) , 2)

        # Draw small area for center of bounding box
        #pygame.draw.rect(screen, (200, 200, 0), 
        #    Rect(self.bounding_box.centerx, self.bounding_box.centery, 1, 1),
        #    2)
        
    
    def move_step(self, time_elapsed_seconds):
        # Trig to move along a line given direction and speed

        # Get elapsed seconds from timer
        time_elapsed_seconds = self.update_timer.last_elapsed_time
        
        # Need radians - not degrees
        radians = (self.direction * math.pi) / 180
        
        # How far did we move this frame?
        if time_elapsed_seconds == 0:
            # prevent divide by 0 error
            time_elapsed_seconds = 0.0000000001
        curr_speed = self.speed * time_elapsed_seconds
        
        # Calculate new X,Y
        new_x = self.x + math.cos(radians) * curr_speed
        new_y = self.y + math.sin(radians) * curr_speed
        
        return new_x, new_y
        
    
    def update(self, time_elapsed_seconds):
        if self.frame_timer.expired:
            # Go to next frame
            self.current_frame_index += 1
            if self.current_frame_index >= len(self.images):
                self.current_frame_index = 0

        # Update frame if update timer has past
        if self.update_timer.expired:        
            # Set the current bounding box
            self.bounding_box = self.local_bounding_box.move(self.x, self.y)
    
    def center_on_point(self, x=0, y=0):
        # Center the surface here!
        # Due to the x/y of this being in the upper left corner, the image will be drawn
        # below and off to the right of the normal X/Y, so make sure our "center" is here.

        # NOTE - bounding_box is NOT the same as the surface dimensions
        x_diff = self.local_bounding_box.centerx - self.x
        y_diff = self.local_bounding_box.centery - self.y

        self.x = x - x_diff
        self.y = y - y_diff

    def calculate_bounding_box(self):
        # Look at all the pixels, make the smallest possible
        # box around lit pixels so we have an accurate bounding
        # box
        surface = self.get_current_frame()
        img_w = surface.get_width()
        img_h = surface.get_height()
        
        max_x = 0
        min_x = img_w
        max_y = 0
        min_y = img_h
        
        key_pixel = (0, 0, 0, 0)
        # Grab upper left corner pixel
        key_pixel = surface.get_at((0, 0))
        # print("Using Key Pixel: " + str(key_pixel))
        
        for x in range(0, img_w):
            # Loop through X and keep the max x and least x for
            # non transparent pixels
            for y in range(0, img_h):
                pixel = surface.get_at((x, y))
                if pixel != key_pixel:
                    # Not transparent, see if this is the farthest
                    # extreme where a pixel is located and record it
                    # to auto detect our bounding_box
                    if x > max_x:
                        max_x = x
                    if x < min_x:
                        min_x = x
                    if y > max_y:
                        max_y = y
                    if y < min_y:
                        min_y = y
        
        # Should have a bounding box now
        self.local_bounding_box = Rect(min_x, min_y,
            max_x-min_x, max_y-min_y)
        print("Calculated Bounding Box: " + str(self.local_bounding_box) + " - " + str(type(self)))
    
    def add_image(self, image_file):
        surface = None

        # See if this image is already loaded
        if image_file in type(self).shared_images:
            # print("Image already loaded - using shared image: " + str(image_file))
            surface = type(self).shared_images[image_file]
        else:
            # Load the file and add convert it to the current color format
            # print("Loading Image File: " + str(image_file))
            surface = pygame.image.load(image_file).conver()
            # Save a copy of this in the shared_images list
            type(self).shared_images[image_file] = surface

        if surface is None:
            # Unable to find/load the surface
            print("ERROR finding or loading surface!")
            return
        
        # print("Shared Image Count: " + str(len(type(self).shared_images)))
        # Add this surface to the local copy
        self.images.append(surface)
        
        # Make sure to calculate the bounding box
        if self.local_bounding_box == Rect(0, 0, 0, 0):
            self.calculate_bounding_box()
    
    def add_images(self, image_files):
        # Add each surface
        for s in image_files:
            self.add_image(s)
    
    def get_current_frame_index(self):
        # Figure out the current frame for this animation
        
        if len(self.images) < 1:
            # No images at all? Return -1 for error
            return -1
        
        # Make sure it isn't too low or too high
        if self.current_frame_index < 0:
            self.current_frame_index = 0
        if self.current_frame_index >= len(self.images):
            # If too high, wrap around back to 0
            self.current_frame_index = 0
        return self.current_frame_index
    
    def get_current_frame(self):
        frame_index = self.get_current_frame_index()
        # If we are < 0 then send back an empty surface so things don't
        # blow up
        if len(self.images) == 0:
            return self.image

        if frame_index >= 0:
            # Set the current image
            self.image = self.images[frame_index]
            
        # Return the current frame
        return self.image
    
    def destroy(self):
        # Set to inactive and it will get cleaned up by update
        self.active = False
    
    @classmethod
    def ensure_static_init(cls):
        if cls.shared_images is None:
            cls.shared_images = dict()
        if cls.active_objects is None:
            cls.active_objects = list()

    @classmethod
    def draw_all(cls, screen):
        cls.ensure_static_init()

        # Tell objects to draw themselves
        # print(str(cls) + " len " + str(len(cls.active_objects)) + str(cls.__name__))
        for o in cls.active_objects:
            o.draw(screen)
    
    @classmethod
    def update_all(cls, time_elapsed_seconds):
        cls.ensure_static_init()

        # Tell each object to update
        for o in cls.active_objects:
            o.update(time_elapsed_seconds)
        
        cls.clean_up_inactive_objects()
    
    @classmethod
    def clean_up_inactive_objects(cls):
        # Clean out old objects
        if len(cls.active_objects) > 0 and \
            cls.active_objects[0].active is not True:
            o = cls.active_objects.pop(0)
            print("Destroying object ..." + str(cls))
