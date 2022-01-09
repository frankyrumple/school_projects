
set VERSION=1.0.5
set COMPANY_NAME=CMAGIC
set PRODUCT_NAME=Matrix
set DESCRIPTION="Matrix Screen Saver"
set MAIN_FILE=main.py
set OUT_FILE=Matrix.exe
set DATA_FILE="matrix code nfi.ttf=matrix code nfi.ttf"

set GLEW_DEP_BINS=--include-data-file="C:\Program Files\Python39\share\glew\bin\*.dll=./"
set SDL2_DEP_BINS=--include-data-file="C:\Program Files\Python39\share\sdl2\bin\*.dll=./"
set ANGLE_DEP_BINS=--include-data-file="C:\Program Files\Python39\share\angle\bin\*.dll=./"
set GSTREAMER_DEP_BINS=--include-data-file="C:\Program Files\Python39\share\gstreamer\bin\*.dll=./"
rem build mgmt
rem --windows-disable-console   - if running gui
rem --windows-icon-from-ico=logo_icon.ico
rem --windows-uac-admin  -- force uac prompt
rem --windows-uac-uiaccess    --- ???
rem --windows-company-name=%COMPANY_NAME%
rem --windows-product-name=%PRODUCT_NAME%
rem --windows-file-version=%VERSION%
rem --windows-product-version=%VERSION%
rem --windows-file-description=%DESCRIPTION%
rem --windows-onefile-tempdir  -- use temp folder rather then appdata folder
rem --python-flag=
rem --follow-imports
rem --onefile  - use appdata folder to unpack
rem --windows-dependency-tool=pefile  - collect dependancies if needed
rem --experimental=use_pefile_recurse --experimental=use_pefile_fullrecurse   --- to find more depends if needed

rem python -m nuitka --python-arch=x86 --standalone  %MAIN_FILE%
rem arch   x86 or x86_64
rem --follow-imports ^

rem --windows-disable-console ^

rem --onefile ^
rem --windows-onefile-tempdir-spec=%TEMP%\\matrix_%PID%_%TIME%\\^
rem --enable-plugin=anti-bloat ^

rem --windows-disable-console ^
rem --python-flag=no_site ^
rem --onefile ^
rem --lto=yes ^
rem --enable-plugin=anti-bloat ^
rem -o %OUT_FILE% ^

rem --show-progress ^
rem --show-scons ^
rem --disable-plugin=numpy --disable-plugin=tk-inter --disable-plugin=pyqt5 --disable-plugin=pyside2 ^
rem --windows-disable-console ^
rem --remove-output ^
rem --mingw64 ^

rem %SDL2_DEP_BINS% ^
rem %GSTREAMER_DEP_BINS% ^
rem --lto=yes ^

python -m nuitka ^
    --python-arch=x86_64 ^
    --standalone ^
    --onefile ^
    --clang ^
    --follow-imports ^
    --python-flag=no_site ^
    --include-plugin-files=depends.py ^
    --windows-icon-from-ico=logo_icon.ico ^
    --windows-company-name=%COMPANY_NAME% ^
    --windows-product-name=%PRODUCT_NAME% ^
    --windows-file-version=%VERSION% ^
    --windows-product-version=%VERSION% ^
    --windows-file-description=%DESCRIPTION% ^
    --windows-disable-console ^
    --remove-output ^
    --include-data-file=%DATA_FILE% ^
    %GLEW_DEP_BINS% ^
    %ANGLE_DEP_BINS% ^
    --include-package=kivy ^
    -o %OUT_FILE% ^
    %MAIN_FILE%

copy Matrix.exe Matrix.scr
