# Kivy Matrix Screen Saver

Copy matrix.exe to matrix.scr and past into c:\windows\system32 folder (64 bit only - you can re-compile using 32bit python if you want 32 bit)

Written in Python + Kivy 2.0.


## Compiling with Nuitka and Kivy

Using Kivy with Nuitka requires a few workarounds.
- Need to set KIVY_DATA_DIR so that files can be found when compiled with --onefile
- Need to disable console logging when compiling with --windows-disable-console (os.environ['KIVY_NO_CONSOLELOG'] = "1")
- Need to copy over DLLs manually to the dist folder (see build_nuitka.cmd - --include-data-file= parameters for GLEW, etc...)
- Need to modify kivy/\_\_init__.py to not crash when it tries to import kivy_deps.* (see https://github.com/kivy/kivy/issues/7743)

## Edit c:/program files/python39/Lib/site-packages/kivy/\_\_init__.py
Starting at lin 294, add the second Exception below to your kivy code to keep it from crashing when compiled.

```python
_logging_msgs = []
for importer, modname, package in _packages:
    try:
        mod = importer.find_module(modname).load_module(modname)

        version = ''
        if hasattr(mod, '__version__'):
            version = ' {}'.format(mod.__version__)
        _logging_msgs.append(
            'deps: Successfully imported "{}.{}"{}'.
            format(package, modname, version))
    except ImportError as e:
        Logger.warning(
            'deps: Error importing dependency "{}.{}": {}'.
            format(package, modname, str(e)))
#### ADD THIS NEW EXCEPTION SO APP DOESN'T CRASH WHEN COMPILED            
    except Exception as e:
        Logger.warning(
            'deps: Error importing dependency "{}.{}": {}'.
            format(package, modname, str(e)))
```

## Kivy Rendering Many Small Sprites
Kivy uses graphic acceleration so it can handle many small sprites. You can NOT make them widgets thoug (e.g. > 300 items starts to get really slow). 

This means that business apps work great, but when you start rendering many small sprites (> 300), you need to do it using canvas instructions (rectangles)
rather then making a widget for each item.  In the app you can see that the main window is a widget, but the FPS counter is a generic python object
that will add its canvas drawing instructions (color/rectangle) to the main widgets canvas object. The object renders a texture as needed. In this
case the FPSControl object uses CoreLabel to render to a texture. Other objects use the same technique.

## Too Many Events
After a few hunderd events, it gets to bee too much. As such, each instance of the falling line object (generally < 300) uses the on_step event every frame. For the tailing characters
(around 2000-4000) it is more efficient to catch one event and loop over them. The main widget does this once per frame.

## Result - FAST
Kivy is potentially much faster then pygame if you don't use widgets. With this method, I get 40fps on a dual screen monitor at about 3k resolution running as python. Compiled with nuitka it jumps to 60+ fps. The pygame version is closer to 30fps compiled.
