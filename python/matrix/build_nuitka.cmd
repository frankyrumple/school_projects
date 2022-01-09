
set VERSION=1.0.4
set COMPANY_NAME=CMAGIC
set PRODUCT_NAME=Matrix
set DESCRIPTION="Matrix Screen Saver"
set MAIN_FILE=main.py
set OUT_FILE=Matrix.exe
set DATA_FILE="matrix code nfi.ttf=matrix code nfi.ttf"
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

rem -o %OUT_FILE% ^
python -m nuitka ^
    --python-arch=x86_64 ^
    --python-flag=no_site ^
    --standalone ^
    --onefile ^
    --windows-disable-console ^
    --windows-icon-from-ico=logo_icon.ico ^
    --windows-company-name=%COMPANY_NAME% ^
    --windows-product-name=%PRODUCT_NAME% ^
    --windows-file-version=%VERSION% ^
    --windows-product-version=%VERSION% ^
    --windows-file-description=%DESCRIPTION% ^
    --include-data-file=%DATA_FILE% ^
    --lto=yes ^
    --enable-plugin=anti-bloat ^
    --disable-plugin=numpy --disable-plugin=tk-inter --disable-plugin=pyqt5 --disable-plugin=pyside2 ^
    -o %OUT_FILE% ^
    %MAIN_FILE%

copy Matrix.exe Matrix.scr
