"""
    Matrix Screen Example
    
"""

import ctypes
from ctypes import wintypes
import profile
import pygame
from pygame.locals import *
from pygame._sdl2 import Window, Texture, Image, Renderer, get_drivers, messagebox  # *
import sys
import os
import time
import random
import click
import cProfile, pstats, io

from fps_counter import FPSCounter
from falling_line import FallingLine, TailCharacter


# NOTE - When running as EXE, cd to current folder
# NOTE - Screen saver - need to copy scr file to both system32 and syswow64 (if 32 bit app running in 64 bit windows)
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = app_path()

    return os.path.join(base_path, relative_path)

def app_path():
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__)) # os.path.abspath(".")

    return base_path
base_path = app_path()
#print(base_path)
os.chdir(base_path)

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


def main():
    global screen_saver_param, screen_saver_show_in_hwnd, base_path
    
    # Make sure we deal with hi res large screens
    ctypes.windll.user32.SetProcessDPIAware()
    # Single monitor
    #desktop_size = (ctypes.windll.user32.GetSystemMetrics(0),ctypes.windll.user32.GetSystemMetrics(1))
    # multi monitor - use 78,79
    desktop_size = (ctypes.windll.user32.GetSystemMetrics(78), ctypes.windll.user32.GetSystemMetrics(79))

    font_size = 22

    # Start w desktop size - if embedded, change resolution then
    window_size = desktop_size
    window_pos = (0, 0)
    loop_delay = 1
    max_framerate = 60
    flags = NOFRAME # | FULLSCREEN | HWSURFACE # DOUBLEBUF | FULLSCREEN | SWSURFACE | HWSURFACE
    depth = 16
    show_fps = False
    PROFILE_APP = False

    if screen_saver_param == "p":
        # Preview mode
        # Note - this only works for pygame 1.9 - pygame 2 needs rework w sdl_createwindowfrom to work
        # Works now for pygame 2.1?
        os.environ['SDL_VIDEO_DRIVER'] = 'windib'
        os.environ['SDL_WINDOWID'] = str(screen_saver_show_in_hwnd)
        #window_size = (100, 100)
        try:
            win_id = screen_saver_show_in_hwnd
        except:
            # If no win id, just exit
            print("No hwnd provided!")
            sys.exit()

        win_rect = wintypes.RECT()
        ret = ctypes.windll.user32.GetWindowRect(win_id, ctypes.pointer(win_rect))
        #print(win_rect)
        win_w = win_rect.right - win_rect.left
        win_h = win_rect.bottom - win_rect.top
        window_size = (win_w, win_h)
        window_pos = (win_rect.left, win_rect.top)
        # Which flags for this surface?
        flags = NOFRAME
        loop_delay = 50
    else:
        # Set position at 0,0 if not embedded
        os.environ['SDL_VIDEO_WINDOW_POS'] = '%i,%i' % window_pos
        #os.environ['SDL_VIDEO_CENTERED'] = '0'

    if screen_saver_param == "c":
        # Show config screen
        #ctypes.windll.user32.MessageBoxW(0, "No Config Options", "Matrix Screen Saver", 1)
        #time.sleep(5)
        answer = messagebox(
            "No config options available.",
            "Config Options",
            info=True,
            buttons=("Close",),
            return_button=0,
            escape_button=0
        )
        sys.exit(0)

    # If screen_saver_param == "s" or not set, run screen saver

    pygame.init()
    #pygame.display.init()
    #pygame.display.set_caption("Matrix")
    pygame.mouse.set_visible(False)
    # Make key down events only happen once (e.g. not repeat over and over again)
    pygame.key.set_repeat(0)  # pygame.key.set_repeat(1000, 10)

    #print(f"Win Size: {window_size}")
    screen = pygame.display.set_mode(window_size, flags=flags, depth=depth)
    screen.set_alpha(True)
    #print(screen.get_size())
    
    # Setup always on top
    win_id = pygame.display.get_wm_info()['window']
    ctypes.windll.user32.SetWindowPos(win_id, -1, window_pos[0], window_pos[1], 0, 0, 0x0001)

    # Setup font
    font_path = os.path.join(base_path, "matrix code nfi.ttf")
    matrix_font = pygame.font.Font(font_path, font_size) #.SysFont(self.font_name, self.font_size)

    matrix_font_w, matrix_font_h = matrix_font.size("H")

    # Do about ??% of lines possible
    max_lines = int( (screen.get_width() / matrix_font_w) * 0.85 ) #+ 20

    lines = []

    for i in range(max_lines):
        lines.append(FallingLine(matrix_font))
        

    if PROFILE_APP:
        profile_obj = cProfile.Profile()
        profile_obj.enable()

    clock = pygame.time.Clock()
    fps = FPSCounter(10, 10, screen=screen, clock=clock)
    # chr(0x42a)
    # tc = TailCharacter(matrix_font, "Ъ", 600, 500)

    # Game loop
    running = True
    while running == True:
        # Clock tics
        time_elapsed_seconds = clock.tick(max_framerate) / 1000.0

        # Check for input
        for event in pygame.event.get():
            #print("event: " + str(event))
            if event.type == KEYDOWN and event.key == K_f:
                # toggle fps
                if show_fps:
                    show_fps = False
                else:
                    show_fps = True
                # print("press f " + str(show_fps))
            elif event.type == QUIT or \
                (event.type == KEYDOWN and event.key != K_f) or \
                (event.type == MOUSEBUTTONDOWN):
                #(event.type == MOUSEMOTION) or \
                #(event.type == KEYDOWN and event.key == K_ESCAPE):
                #sys.exit()
                running = False
                break
            elif screen_saver_param == "s" and event.type == MOUSEMOTION:
                # Get relative movement
                x, y = mouse_position = pygame.mouse.get_rel()
                # If it is enough distance, then quit
                if x > 20 or y > 20:
                    print("mouse move, exiting...")
                    running = False
                    break
        
        TailCharacter.update_all(time_elapsed_seconds, clock)
    
        for line in lines:
            line.update(time_elapsed_seconds, clock)
                
        # Fill the screen with black - need to paint over
        # all the stuff from last frame
        screen.fill((0, 0, 0))

        # Draw objects
        TailCharacter.draw_all(screen)
        
        FallingLine.draw_all(screen, lines)
        # for line in lines:
        #     line.draw(screen)

        if show_fps is True:
            fps.update()
            fps.draw()
        
        # Show the current frame on the screen
        pygame.display.flip() #.update() # flip()
        
        
        #pygame.time.wait(loop_delay)
        #clock.tick(60)
        #pygame.time.delay(loop_delay)

    if PROFILE_APP:
        profile_obj.disable()
        #stats_io = io.StringIO()
        #pstat = pstats.Stats(profile_obj, stream=stats_io).sort_stats(SortKey.CUMULATIVE)
        #pstat = pstats.Stats(profile_obj, stream=stats_io).sort_stats("time")
        pstat = pstats.Stats(profile_obj).sort_stats("time")
        pstat.print_stats(10)
        #print(stats_io.getvalue())

    # Cleanup
    pygame.quit()
    sys.exit()

def load_img(img_file):
    global base_path
    return pygame.image.load(os.path.join(base_path, img_file))

if __name__ == "__main__":
    # Parse args
    click_main()
    # Call main from click_main - function doesn't return
