@echo off
setlocal enabledelayedexpansion


set "start_dir=%~dp0"

echo Starting search in: "%start_dir%"


set "photos_dir=%start_dir%photos"
if not exist "%photos_dir%" (
    echo Creating directory: "%photos_dir%"
    mkdir "%photos_dir%"
)


for /d %%D in ("%start_dir%*") do (
    if /i not "%%~nxD"=="photos" (
        echo Processing folder: %%D


        set "folder_name=%%~nxD"
        set "base_name=!folder_name:~0,10!_!folder_name:~11,2!-!folder_name:~14,2!"


        set /a img_counter=0


        for %%F in ("%%D\*.jpg", "%%D\*.jpeg", "%%D\*.gif") do (
            set /a img_counter+=1
            set "img_name=!base_name!"
            if !img_counter! gtr 1 (
                set "img_name=!base_name!(!img_counter!)"
            )


            set "target_file=%photos_dir%\!img_name!%%~xF"

            echo Copying "%%F" to "!target_file!"
            copy "%%F" "!target_file!"
        )
    )
)

echo Operation completed.
pause
