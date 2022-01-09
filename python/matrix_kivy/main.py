import random
import click
import os
import sys
import cProfile, pstats

# Set path for nuitka to find resources
is_nuitka = "__compiled__" in globals()
if is_nuitka:
    print("Running Compiled...")
    # Use this for standalone (folder) builds
    #exec_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
    # Use this for onefile builds
    exec_dir = os.path.dirname(os.path.realpath(__file__))
    #print(f"EXEC DIR: {exec_dir}")
    os.environ['KIVY_DATA_DIR'] = os.path.join(exec_dir, 'kivy', 'data')
    # Disable console logs
    os.environ['KIVY_NO_CONSOLELOG'] = "1"
else:
    print("Running ByteCode...")

# Need here for nuitka compile to find them
#import kivy_deps.angle
#import kivy_deps.glew
#import kivy_deps.sdl2

from kivy.config import Config
Config.set('graphics', 'resizable', True) 
# Enable FPS
#Config.set('modules', 'monitor', '1')

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.core.text import Label as CoreLabel
#from kivy.uix.label import CoreLabel
from kivy.graphics.texture import Texture
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty, StringProperty
from kivy.clock import Clock
from kivy.lang import Builder


# sys.path.append('C:\\Program Files\\Brainwy\\PyVmMonitor 2.0.2\\public_api')
# import pyvmmonitor
# pyvmmonitor.connect()




# Kivy App (created in main)
global app

def app_path():
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__)) # os.path.abspath(".")

    return base_path

def get_desktop_size():
    import ctypes
    from ctypes import wintypes
    # Make sure we deal with hi res large screens
    ctypes.windll.user32.SetProcessDPIAware()
    # Single monitor
    #desktop_size = (ctypes.windll.user32.GetSystemMetrics(0),ctypes.windll.user32.GetSystemMetrics(1))
    # multi monitor - use 78,79
    desktop_size = (ctypes.windll.user32.GetSystemMetrics(78), ctypes.windll.user32.GetSystemMetrics(79))
    return desktop_size

def get_hwnd_pos_size(hwnd):
    import ctypes
    from ctypes import wintypes

    if hwnd is None or int(hwnd) < 1:
        return None

    r = wintypes.RECT()
    ret = ctypes.windll.user32.GetWindowRect(hwnd, ctypes.pointer(r))

    pos = (r.left, r.top)
    size = (r.right - r.left, r.bottom - r.top)

    return pos, size

# For screen saver - params
# /c - show settings dialog box
# /p <HWND>  - show preview in this window
# /s - run screen saver
screen_saver_param = ""
screen_saver_show_in_hwnd = 0


#@click.group()
@click.command()
@click.option("/c", required=False, default=False, is_flag=True, type=bool, help="Show Config Box")
@click.option("/s", required=False, default=False, is_flag=True, type=bool, help="Run Screen Saver")
@click.option("/p", required=False, default=-1, nargs=1, help="Show Preview")
def click_main(c, s, p):
    global screen_saver_param, screen_saver_show_in_hwnd

    if c is True:  # show config box
        screen_saver_param = "c"
    elif s is True:  # run screen saver
        screen_saver_param = "s"
    elif p > -1:   # Show preview
        screen_saver_param = "p"
        screen_saver_show_in_hwnd = p
    
    main()

class FONT_CACHE:
    # A class to cache rendered fonts so we don't have to re-draw them constantly
    _FONT_TEXTURES = dict()

    @staticmethod
    def get_font_texture(key):
        if key in FONT_CACHE._FONT_TEXTURES:
            return FONT_CACHE._FONT_TEXTURES[key]
        
        return None
    
    @staticmethod
    def set_font_texture(key, value):
        if not key in FONT_CACHE._FONT_TEXTURES:
            FONT_CACHE._FONT_TEXTURES[key] = value
    

class MainWidget(Widget):
    # Keep an easy way to get the root widget
    _ROOT_WIDGET = None

    # Show extra stats in the FPS label
    _EXTRA_STATS = False
    # Multiplier for number of falling lines to create
    _num_lines_mult = 0.7

    def __init__(self, **kwargs):
        super().__init__(*kwargs)

        if MainWidget._ROOT_WIDGET is None:
            MainWidget._ROOT_WIDGET = self
        
        # Setup our event for each frame - other object can get this event too
        self.register_event_type("on_step")

        # Bind widget size so it resizes
        #self.main_widget.bind(size=self.update_rect, pos=self.update_rect)
        Window.bind(on_resize=self.resized)

        self.desktop_size = get_desktop_size()

        # Default to full screen
        self.window_size = self.desktop_size
        self.window_pos = (0, 0)
        
        # Decide size of screen - full screen or running in preview window
        if screen_saver_param == "p":
            # Need to make it smaller and position it in where the HWND window is...
            self.window_pos, self.window_size = get_hwnd_pos_size(screen_saver_show_in_hwnd)
            #print(f"{self.window_pos} {self.window_size}")
            if self.window_size == (0,0):
                self.window_size = self.desktop_size
            
        # Position/size the window
        Window.size = self.window_size
        Window.left = self.window_pos[0]
        Window.top = self.window_pos[1]
        # Do we need this? Running as screen saver?
        Window.allow_screensaver = False
        Window.borderless = True
        Window.show_cursor = False
        
        # Setup the drawing instructions for our widget
        with self.canvas.before:
            # Background - clear to black
            Color(0, 0, 0, 1)
            Rectangle(pos=(0,0), size=(self.width, self.height))

        # Add an FPS control
        self._fps_control = FPSControl()

        Clock.schedule_interval(self._on_step, 0)  # Run every frame

        # Get some keys/mouse control
        self._keyboard = Window.request_keyboard(self._on_keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_key_down)
        self.last_mouse_pos = None
        Window.bind(mouse_pos=self._on_mouse_pos)

    def _on_mouse_pos(self, instance, pos):
        if self.last_mouse_pos is None:
            self.last_mouse_pos = pos
            return
        
        # See if we have moved too much and need to close the app (close screen saver)
        max_diff = 30
        moved = False

        if (abs(pos[0] - self.last_mouse_pos[0]) > max_diff or \
            abs(pos[1] - self.last_mouse_pos[1]) > max_diff):
            moved = True
         
        if moved:
            # Mouse moved - close app
            a = App.get_running_app()
            if a:
                print("Closing - mouse moved.")
                a.stop()


    def _on_keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None
    
    def _on_key_down(self, keyboard, keycode, text, modifiers):
        if keycode[1] == "f":
            # Toggle FPS
            self._fps_control.visible = not self._fps_control.visible
            pass
        elif keycode[1] == "e":
            # Toggle extra stats
            MainWidget._EXTRA_STATS = not MainWidget._EXTRA_STATS
            pass
        elif keycode[1] == "up":
            # Increase falling lines
            MainWidget._num_lines_mult += 0.1
            self.add_falling_lines()
            pass
        elif keycode[1] == "down":
            # Decrease falling lines
            MainWidget._num_lines_mult -= 0.1
            self.add_falling_lines()
            pass
        elif keycode[1] == "escape":
            # Close app
            App.get_running_app().stop()
            pass

        #print(f"{keycode}")

        return True

    def _on_step(self, dt):
        # Send events down the stack
        self.dispatch("on_step", dt)

    def on_step(self, dt):
        
        # Update the tail characters
        for tc in TailCharacter._tail_characters.copy():
            tc.on_step(self, dt)

        pass
    
    def resized(self, instance, width, height):
        # Make sure we add/remove falling lines
        # print(f"resized: {instance.width} -> {width} ")
        self.width = width
        self.height = height
        self.add_falling_lines()

    def add_falling_lines(self):
        # Make a temp falling line so we can get the font width
        fl = FallingLine("H", -50, -50)
        char_width = fl.size[0]
        fl.destroy()
        
        # Get about 90% coverage
        num_lines = int( (self.width / char_width) * MainWidget._num_lines_mult) + 1
        #print(f"AddFallingLins: {num_lines}")
        # Remove if too many (after resize)
        while len(FallingLine._falling_lines) > num_lines:
            l = FallingLine._falling_lines.pop()
            l.destroy()
            
        
        # Make sure we have enough (if smaller, and resized bigger)
        while len(FallingLine._falling_lines) < num_lines:
            l = FallingLine()

        pass

class FPSControl(object):
    def __init__(self):
        self.pos = (0, 0)
        self.size = (10, 10)
        self.max_width = 10
        self.visible = True
        
        self._fps_label = CoreLabel(text="Test", font_size=20, color=(1, 1, 1, 1), markup=True)
        self._fps_label.refresh()  # Core label needs to refresh to make the texture available

        # Kivy drawing instructions
        self._canvas_fps_text = Rectangle(
            pos = self.pos, size=self.size, texture=self._fps_label.texture
        )
        self._canvas_text_color = Color(self._fps_label.options['color'])
        self._canvas_background_color = Color(.75, .75, .75, 0.3)
        self._canvas_background_texture = Rectangle(
            pos=self.pos, size=self._fps_label.texture.size
        )
        # Add to canvas drawing list
        MainWidget._ROOT_WIDGET.canvas.add(self._canvas_background_color)
        MainWidget._ROOT_WIDGET.canvas.add(self._canvas_background_texture)
        MainWidget._ROOT_WIDGET.canvas.add(self._canvas_text_color)
        MainWidget._ROOT_WIDGET.canvas.add(self._canvas_fps_text)

        # Catch frame update event
        MainWidget._ROOT_WIDGET.bind(on_step=self.on_step)
        
    
    def on_step(self, sender, dt):
        # print("FPS on_step")
        self.update_fps()
        pass

    def update_fps(self):
        if not self.visible:
            # Hiden, use an empty texture
            self._canvas_fps_text.texture = None
            self._canvas_fps_text.size = (0,0)
            self._canvas_background_texture.size = (0, 0)
            return

        fps_text = f"FPS: {round(Clock.get_fps(), 2)}"

        if MainWidget._EXTRA_STATS:
            # Render extra information
            ex = f"\nFalling Lines: {len(FallingLine._falling_lines)}\n" + \
            f"TailChars: {len(TailCharacter._tail_characters)}\n" + \
            f"Free TailChars: {len(TailCharacter._free_tail_characters)}\n" + \
            f"FontCache: {len(FONT_CACHE._FONT_TEXTURES)}\n"
            if len(FallingLine._falling_lines) > 0:
                fl = next(iter(FallingLine._falling_lines))
                ex += f"\n - FL[0]: {round(fl.x,2)}/{round(fl.y,2)} {fl.text:<30}\n"
            fps_text += ex
        
        # Redraw the label and set the texture/pos so it gets rendered
        self._fps_label.text = fps_text
        self._fps_label.refresh()

        self.size = self._fps_label.texture.size

        # Help background keep from "jumping" around when width changs constantly
        curr_width = self.size[0] + 10
        if curr_width < self.max_width:
            curr_width = self.max_width
        self.max_width = curr_width

        self._canvas_fps_text.texture = self._fps_label.texture
        self._canvas_fps_text.size = self._fps_label.texture.size
        self._canvas_fps_text.pos = (10, MainWidget._ROOT_WIDGET.height - 10 - self._fps_label.texture.size[1])
        self._canvas_background_texture.pos = (self._canvas_fps_text.pos[0] - 5, self._canvas_fps_text.pos[1] - 5)
        self._canvas_background_texture.size = (curr_width, self._canvas_fps_text.size[1] + 10)

class FallingLine(object):
    # Keep track of all our falling line objects
    _falling_lines = set()

    # Base font size
    _font_size = 32
    # Random value to scale by
    _font_scale_min = 0.3

    # List of characters we can use from the font
    _characters = list()

    def __init__(self, text="", x=0, y=0, **kwargs):
         # Make sure our list of characters exists
         # Make sure characters are filled in
        if len(FallingLine._characters) < 1:
            # Fill in available characters
            for i in range(0x21, 0x7e):
                FallingLine._characters.append(chr(i))

        # Make sure things are initialized/randomized
        self.font_name = os.path.join(app_path(), "matrix code nfi.ttf")
        FallingLine._falling_lines.add(self)

        self.pos = (x, y)
        self.x = x
        self.y = x
        self.drop_y = 0  # When last time we dropped tail character - start very high so we start dropping right away

        self.tail_life = 4
        self.font_size = FallingLine._font_size
        self.scale = 1.0
        self.size = (0, 0)
        self.color = (1.0, 1.0, 1.0, 1.0)
        self.text = text

        # Make sure we have a "label" so we can render the sprite for the font
        self.label_base = CoreLabel(
                text=self.text, font_size=self.font_size, font_name=self.font_name,
                color=self.color,
                )
        self.label_base.refresh()
        self.size = self.label_base.texture.size

        # Set scaled size
        self.scaled_size = (self.size[0] * self.scale, self.size[1] * self.scale)
        
        # Canvas Drawing Instructions
        self._canvas_text_color = Color(self.label_base.options['color'])
        self._canvas_text_instruction = Rectangle(
            pos=self.pos, size=self.scaled_size, texture=self.label_base.texture
        )

        MainWidget._ROOT_WIDGET.canvas.add(self._canvas_text_color)
        MainWidget._ROOT_WIDGET.canvas.add(self._canvas_text_instruction)

        # Catch frame update event
        MainWidget._ROOT_WIDGET.bind(on_step=self.on_step)

        self.reset_item()
        # print(f"NEW {self.pos}")

    def new_character(self):
        # New random text
        self.text = random.choice(FallingLine._characters)
        self.label_base.text = self.text
        self.label_base.refresh()
        self.current_frame = self.label_base.texture
        self.size = self.label_base.texture.size

    def reset_item(self):
        # Called to reset/randomize this item
        self.text = random.choice(FallingLine._characters)
        self.label_base.text = self.text
        self.font_size = FallingLine._font_size
        self.label_base.options["font_size"] = self.font_size
        self.label_base.refresh()
        self.current_frame = self.label_base.texture
        self.size = self.label_base.texture.size
        self.scale = random.random() + FallingLine._font_scale_min
        self.scaled_size = (self.size[0] * self.scale, self.size[1] * self.scale)

        # NOTE - coord in kivy are (0, 0) at bottom left       
        rnd_x = random.randint(0, MainWidget._ROOT_WIDGET.width)
        rnd_y = MainWidget._ROOT_WIDGET.height + 10 + random.randint(0, 150)
        self.x = rnd_x
        self.y = rnd_y
        self.pos = (rnd_x, rnd_y)

        self.speed = random.randint(40, 200) # how fast to move
        self.tail_life = random.randint(0, 2) + 3

        # Make sure to reset drop_y so we start dropping again after a reset
        self.drop_y = 0

    def on_step(self, sender, dt):
        # If we are too low, reset to the top.
        if self.y < -30:
            self.reset_item()

        # print("fl step.")
        # Move thigs a little
        self.y -= self.speed * dt
        self.pos = (self.x, self.y)

        # Update the canvas object
        self._canvas_text_instruction.texture = self.label_base.texture
        self._canvas_text_instruction.pos = self.pos
        self._canvas_text_instruction.size = self.scaled_size
        
        # Is it time to drop a tailing character?
        if self.drop_y < self.y:
            # Make sure drop_y is never below current y
            self.drop_y = self.y

        drop_distance = self.size[1] * .90
        if self.drop_y - self.y > drop_distance:
            # Time to drop one.
            self.drop_tail_character()
            self.drop_y = self.y

    def drop_tail_character(self):
        # Make sure we are on the screen
        if not MainWidget._ROOT_WIDGET.collide_point(self.x, self.y):
            # Not on the screen, skip out early
            return
        
        #("Drop TC")
        TailCharacter.create(self.text, self.x, self.y, self.tail_life, self.font_size, self.scale)
        self.new_character()


    def destroy(self):
        if self in FallingLine._falling_lines:
            FallingLine._falling_lines.remove(self)

        # Remove from canvas drawing
        MainWidget._ROOT_WIDGET.canvas.remove(self._canvas_text_color)
        MainWidget._ROOT_WIDGET.canvas.remove(self._canvas_text_instruction)

        # Remove self from event notifications
        MainWidget._ROOT_WIDGET.unbind(on_step=self.on_step)
        
        del self


class TailCharacter(object):
    _tail_characters = set()

    _free_tail_characters = set()

    # Keep a list of calculated colors
    _colors = dict()
    
    @staticmethod
    def create(text, x, y, life=4, font_size=20, scale=1.0, **kwargs):
        # Is there a free one?
        if len(TailCharacter._free_tail_characters) > 0:
            r = TailCharacter._free_tail_characters.pop()
            r.__init__(text, x, y, life, font_size, scale, **kwargs)
            return r
        else:
            # None free, make a new one.
            return TailCharacter(text, x, y, life, font_size, scale, **kwargs)

    def __init__(self, text, x, y, life=4, font_size=20, scale=1.0, **kwargs):
        if not hasattr(self, "is_init"):
            super().__init__(**kwargs)
        self.destroyed = False
        self.font_name = os.path.join(app_path(), "matrix code nfi.ttf")
        self.text = text
        self.font_size = font_size
        self.scale = scale
        self.x = x
        self.y = y
        self.pos = (x, y)
        self.size = (0, 0)
        self.color_start = (255, 255, 255)
        self.color_end = (0, 255, 0)
        self.color = self.color_start
        self.opacity = 1.0
        self.max_life = life
        self.life = 0
        self.last_progress = 0.0
        self.progress = 0.0
                
        # Make sure we have a "label" so we can render the sprite for the font
        if not hasattr(self, "label_base"):
            self.label_base = CoreLabel(
                    text=self.text, font_size=self.font_size, font_name=self.font_name,
                    color=self.color,
                    )

        self.label_base.text = self.text
        self.label_base.options["font_size"] = self.font_size
        self.label_base.refresh()
        #self.label_base.texture.wrap='clamp_to_edge'
        self.size = self.label_base.texture.size

        # Calculate the scaled size
        self.scaled_size = (self.size[0] * self.scale, self.size[1] * self.scale)

        # Setup canvas instructions
        if not hasattr(self, "_canvas_text_instruction"):
            self._canvas_text_color = Color(self.color)
            self._canvas_text_instruction = Rectangle(
                pos=self.pos, size=(0, 0), texture=None
            )
        MainWidget._ROOT_WIDGET.canvas.add(self._canvas_text_color)
        MainWidget._ROOT_WIDGET.canvas.add(self._canvas_text_instruction)

        self.calculate_rgb_from_progress()
        self.render_text()

        TailCharacter._tail_characters.add(self)

        # Don't catch events on tail characters - there are thousands and that many events is bad
        # We call the on_step function from the main widget in a loop
        #MainWidget._ROOT_WIDGET.bind(on_step=self.on_step)

    def on_step(self, sender, dt):
        if self.destroyed:
            # Don't draw if inactive
            return

        self.move_step(dt)
        pass
        
    def render_text(self):
        if self.progress != self.last_progress:
            self.last_progress = self.progress

            self.calculate_rgb_from_progress()
            
            # See if the image is cached
            cache_key = f"{self.text}_{self.progress}" # _{self.color}
            t = FONT_CACHE.get_font_texture(cache_key)
            if t is None:
                # Need to draw a new texture
                
                self.label_base.text = self.text
                self.label_base.options['font_size'] = self.font_size
                self.label_base.options['color'] = self.color
                self.label_base.refresh()
                # Need to make a copy of the texture so we can reuse the original later for the next character
                t = Texture.create(size=self.label_base.size, colorfmt='rgba')
                t.blit_buffer(self.label_base.texture.pixels, colorfmt='rgba', bufferfmt='ubyte')
                FONT_CACHE.set_font_texture(cache_key, t)
        
            # Calculate the scaled size
            self.size = t.size
            self.scaled_size = (self.size[0] * self.scale, self.size[1] * self.scale)

            # Update canvas update instruction
            self._canvas_text_instruction.texture = t
            self._canvas_text_instruction.size = self.scaled_size
            self._canvas_text_instruction.pos = self.pos

        #self.last_drawn = curr_text_key

    def calculate_rgb_from_progress(self):
        # Figure out what the current color should be based on progress

        # Use cache!
        if self.progress in TailCharacter._colors:
            self.color = TailCharacter._colors[self.progress]
            return

        fade_to_color = self.color_end
        start_color = self.color_start

        # Calculate the current color based on our progress
        r = fade_to_color[0] - start_color[0]
        r *= self.progress
        r += start_color[0]

        g = fade_to_color[1] - start_color[1]
        g *= self.progress
        g += start_color[1]

        b = fade_to_color[2] - start_color[2]
        b *= self.progress
        b += start_color[2]

        # Clamp values so we don't overflow (no < 0 or > 255)
        r = int(sorted((0, r, 255))[1])
        g = int(sorted((0, g, 255))[1])
        b = int(sorted((0, b, 255))[1])

        # Current Alpha
        a = 255 * self.opacity
        # Clamp value
        a = int(sorted((0, a, 255))[1])

        # Convert colors to 0.0 - 1.0 instead of 0-255 for kivy
        r = r / 255
        g = g / 255
        b = b / 255
        a = a / 255
        # Store in current color
        self.color = (r, g, b, a)

        # Add color to the cache
        TailCharacter._colors[self.progress] = (r, g, b, a)


    def move_step(self, dt):
        # Kill any that are off the screen
        if not MainWidget._ROOT_WIDGET.collide_point(self.x, self.y):
            self.destroy()
            return

        # Change color and fade out slowly...
        #self.life += 1
        self.life += dt
        
        # How far have we gone?
        self.progress = round(self.life / self.max_life, 1)
        
        # Fade out
        self.opacity = 1.0 - self.progress

        # Render the current frame
        self.render_text()

        if self.life > self.max_life:
            self.destroy()
        pass
    
    def destroy(self):
        self.destroyed = True

        if self in TailCharacter._tail_characters:
            TailCharacter._tail_characters.remove(self)
        
        #MainWidget._ROOT_WIDGET.unbind(on_step=self.on_step)

        # Set canvas object to NOT draw rather then removing
        # self._canvas_text_instruction.texture = None
        # self._canvas_text_instruction.size = (0,0)
        # Remove from canvas drawing
        MainWidget._ROOT_WIDGET.canvas.remove(self._canvas_text_instruction)
        MainWidget._ROOT_WIDGET.canvas.remove(self._canvas_text_color)
        
        # Put self in the free tail characters so we can reuse it later
        TailCharacter._free_tail_characters.add(self)


class MatrixApp(App):
    def build(self):
        self.main_widget = MainWidget()
        
        return self.main_widget
    
def main():
    global app
    PROFILE_APP = False
    PROFILE_OBJ = None

    if PROFILE_APP:
        PROFILE_OBJ = cProfile.Profile()
        PROFILE_OBJ.enable()

    app = MatrixApp()
    app.run()

    if PROFILE_APP:
        PROFILE_OBJ.disable()
        pstat = pstats.Stats(PROFILE_OBJ).sort_stats("time")
        pstat.print_stats(10)

if __name__ == "__main__":
    click_main()
