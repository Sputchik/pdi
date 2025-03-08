@echo off
setlocal EnableDelayedExpansion

if "%~1" == "--help" (
	echo.
	echo Usage: pdi.bat [--passive] [--output Path] [--select Programs]
	echo.
	echo    --passive            Jumps to a download process for programs defined using --select Flag
	echo.
	echo    --no-install         Exits upon downloading programs
	echo.
	echo    --output Path        Download Path
	echo.
	echo    --select Programs    Select Programs, Separate them by semicolon `;`
	echo                         Example: --select "Telegram Portable;Librewolf;Discord;Steam"
	exit /b
)

cls
net session >nul 2>&1
if !ErrorLevel! NEQ 0 (
	echo Run this script as an admin!
	echo Though, you can continue
	echo.
	echo Keep in mind most ZIP installation will fail ^(Access to %PF%^)
	pause
)

call :CheckInternet
set "CWD=%~dp0"
set "DLPath=%CWD%pdi_downloads"
for /f "tokens=2*" %%a in ('reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion" /v ProgramFilesDir') do set "PF=%%b"
set FetchedURLs=0
set "UserAgent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:135.0) Gecko/20100101 Firefox/135.0"
set "URLsURL=https://raw.githubusercontent.com/Sputchik/pdi/refs/heads/main/urls.txt"
set "ChooseFolder=powershell -Command "(new-object -ComObject Shell.Application).BrowseForFolder(0,'Please choose a folder.',0,0).Self.Path""
set "Extensions=msi;zip"

if exist "%TEMP%" ( set "TempPath=%TEMP%"
) else set "TempPath=%~dp0"

set "vbsFilePath=%TempPath%\createShortcut.vbs"
set "urlPath=%TempPath%\urls.txt"

:Start

if %FetchedURLs% == 0 (
	call :FetchURLs
) else (
	call :ClearSelected
	cls
	goto :MAIN_MENU
)

set passive=0
set EOF_Download=0

if "%~1" == "" goto :MAIN_MENU

for %%G in (%*) do (
	set /a arg_index+=1
	set "arg=%%~G"

	if defined selecting (
		set "arg=!arg: =_!"

		for %%H in (!arg!) do (
			set "selected_%%H=1"
		)

	) else if defined outputting (
		set "DLPath=!arg!"
		set outputting=

	) else (

		if "!arg!"=="--select" (
			set selecting=1

		) else if "!arg!" == "--passive" (
			set passive=1

		) else if "!arg!" == "--output" (
			set outputting=1
		) else if "!arg!" == "--no-install" (
			set EOF_Download=1
		)

	)
)

if %passive% == 1 goto :DownloadAll

:MAIN_MENU
set index=1

echo Select category:
for %%G in (!Categories!) do (
	set "cat=%%G"
	set "cat=!cat:_= !"
	echo [!index!] !cat!
	set /a index+=1
)
echo [9] Download Selected
echo.
echo Suggest program - @kufla in Telegram

choice /C 123456789 /N /M "Option: "

if !ErrorLevel! == 9 (
	call :CheckInternet
	cls
	goto :DownloadAll
)
call :MANAGE_CATEGORY !ErrorLevel!

goto :eof

:MANAGE_CATEGORY
set "num=%~1"
set "category=!cat_%num%!"
set "programs=!%category%!"

:DISPLAY_LIST

cls
echo Category: %category:_= %

set index=1

for %%G in (!programs!) do (
	set "RawProgName=%%G"
	set "ProgName=!RawProgName:_= !"
	set "IsSelected=!selected_%%G!"

	if !IsSelected! == 1 (
		echo [!index!] [*] !ProgName!
	) else (
		echo [!index!] [ ] !ProgName!
	)

	set /a index+=1
)
echo.
echo [A] Toggle All    [Q] Go back

:USER_SELECTION

set /p selection=""
cls

if /I "%selection%" == "Q" goto MAIN_MENU
if /I "%selection%" == "A" goto TOGGLE_ALL

set /a index=1
for %%G in (!programs!) do (
	if %selection% == !index! (
		if !selected_%%G! == 1 (
			set "selected_%%G=0"
		) else (
			set "selected_%%G=1"
		)
		goto DISPLAY_LIST
	)
	set /a index+=1
)

:TOGGLE_ALL

for %%G in (!programs!) do (
	if !selected_%%G! == 1 (
		set "selected_%%G=0"
	) else (
		set "selected_%%G=1"
	)
)

goto DISPLAY_LIST

:ClearSelected

for %%G in (!Categories!) do (
	set "programs=!%%G!"

	for %%H in (!programs!) do (
		set "selected_%%H="
	)
)

goto :eof

:FetchURLs

curl -A "%UserAgent%" -s %URLsURL% -o "%urlPath%"
:: set "urlPath=urls.txt"
for /f "usebackq tokens=1* delims==" %%G in ("%urlPath%") do (
	set "%%G=%%H"
)

set index=1
for %%G in (!Categories!) do (
	set "cat=%%G"
	set "cat_!index!=!cat!"
	set /a index+=1
)

set FetchedURLs=1
goto :eof

:CheckInternet

ping -n 1 -w 1000 1.1.1.1 >nul 2>&1

if !ErrorLevel! == 1 (
	cls
	echo Woopise, no internet...
	echo.
	timeout /T 1 >nul
) else (
	goto :eof
)

cls
echo You are not connected to internet :^(
echo.
echo [1] Retry Connection
echo [2] Exit
choice /C 12 /N /M " "
echo.

if !ErrorLevel! == 1 goto :WaitForConnection
exit /b

:WaitForConnection

ping -n 1 -w 1000 1.1.1.1 >nul 2>&1

if !ErrorLevel! == 1 (
	echo Retrying in 2 seconds...
	goto :WaitForConnection

) else (
	cls
	goto :eof
)

exit /b

:DownloadFile

set "NAME=%~1%"
set "URL=%~2%"
set "OUTPUT=%~3%"

:loop

echo If download is very slow, try pressing Ctrl+C and `N` ^(Don't terminate script^)
echo.
echo Downloading !NAME!...
echo.

curl -# -A "%UserAgent%" -L -C - -o "%OUTPUT%" "%URL%"

if !ErrorLevel! NEQ 0 (
	echo.
	echo Download interrupted...
	echo.
	echo [1] Retry
	echo [2] Skip
	choice /C 12 /N /M " "
	cls

	if !ErrorLevel! == 1 (
		goto :loop
	) else (
		goto :eof
	)
)

goto :eof

:DownloadAll

mkdir "%DLPath%" 2>nul

for %%G in (!Categories!) do (
	for %%H in (!%%G!) do (
		set "ProgramRaw=%%H"
		set "ProgramSpaced=!ProgramRaw:_= !"

		if "!selected_%%H!" == "1" (
			set "DownloadURL=!url_%%H!"

			if DownloadURL NEQ "" (
				set FileExt=0

				for %%I in (!Extensions!) do (
					for %%J in (!%%I!) do (
						if "!ProgramRaw!" == "%%J" set FileExt=%%I
					)
				)

				:: Default to .exe if no specific extension is found
				if !FileExt! == 0 set FileExt=exe

				if !FileExt! NEQ zip (
					set "ProgramFinal=!ProgramRaw!_Setup"
				) else set "ProgramFinal=!ProgramSpaced!"

				call :DownloadFile "!ProgramSpaced!" "!DownloadURL!" "%DLPath%\!ProgramFinal!.!FileExt!"
				cls

			) else (
				echo Error: Download URL for !prog! is missing..?
			)
		)
	)
)

if %EOF_Download% == 1 goto :eof

:AfterDownload
echo Programs downloaded ^(%DLPath%^)
echo.
choice /C YN /N /M "Try installing them? [Y/N] "

set DoInstall=%ErrorLevel%
set DoneMSI=0
set DoneZip=0

if %DoInstall% == 1 (
	set DoneAll=0
	goto :DirCheck
) else (
	set DoneAll=1
	goto :AfterInstall
)

goto :eof

:DirCheck

::EXE
dir "%DLPath%\*_Setup.exe" /b /a-d >nul 2>&1
set err_exe=!ErrorLevel!
::MSI
dir "%DLPath%\*_Setup.msi" /b /a-d >nul 2>&1
set err_msi=!ErrorLevel!
::ZIP
dir "%DLPath%\*.zip" /b /a-d >nul 2>&1
set err_zip=!ErrorLevel!

if %err_zip% == 0 (
	set DoneZip=0
) else if %err_msi% == 0 (
	set DoneZip=1
) else if %err_exe% == 0 (
	set DoneZip=1
	set DoneMSI=1
) else (
	echo.
	echo You have no programs dumb ass
	timeout /T 1 >nul
	goto :Start
)

:AfterInstall

if %DoneAll% == 1 (
	cd "%CWD%"
	cls
	echo Everything's Set Up^!
	echo.
	echo [1] Exit
	echo [2] Go Back
	echo [3] Delete
	echo [4] Move programs folder

	choice /C 1234 /N /M " "

	if !ErrorLevel! == 1 ( exit /b
	) else if !ErrorLevel! == 2 ( goto :Start
	) else if !ErrorLevel! == 3 (
		echo.
		del /Q "%DLPath%\*" 2>nul

	) else if !ErrorLevel! == 4 ( call :MovePrograms )

	goto :AfterInstall
)

call :ProcessInstallation
goto :eof

:ProcessInstallation
if %DoneMSI% == 1 (
	call :HandleInstall "EXE" %err_exe%
	set DoneAll=1
) else if %DoneZip% == 1 (
	call :HandleInstall "MSI" %err_msi%
	set DoneMSI=1
) else if %DoneZip% == 0 (
	call :HandleInstall "ZIP" %err_zip%
	set DoneZip=1
)
goto :AfterInstall

:HandleInstall
if %~2 == 0 (
	cls
	echo %~1 Programs
	echo.
	echo [1] Install
	echo [2] Proceed further

	choice /C 12 /N /M " "
	echo.

	if !ErrorLevel! == 2 goto :eof

	cd "%DLPath%"
	call :%~1
	cd "%CWD%"
	timeout /T 1
)

goto :eof

:MovePrograms
for /f "usebackq delims=" %%G in (`%ChooseFolder%`) do set "SelectedFolder=%%G"

if defined SelectedFolder (
	move /y "%DLPath%" "%SelectedFolder%"
	timeout /T 1
)

goto :eof

:CreateShortcut

set "exePath=%~1"
set "shortcutName=%~2"

echo Set objShell = CreateObject("WScript.Shell") > "%vbsFilePath%"
echo Set objShortcut = objShell.CreateShortcut(objShell.SpecialFolders("Programs") ^& "\%shortcutName%.lnk") >> "%vbsFilePath%"
echo objShortcut.TargetPath = "%exePath%" >> "%vbsFilePath%"
echo objShortcut.Save >> "%vbsFilePath%"
wscript.exe "%vbsFilePath%"

goto :eof

:ZIP

if exist "Autoruns.zip" (
	echo Installing Autoruns...
	call :Extract "Autoruns"
	xcopy /Q /Y "Autoruns\Autoruns64.exe" "%%PF%%\Autoruns\"
	rmdir /S /Q "Autoruns"
	call :CreateShortcut "%PF%\Autoruns\Autoruns64.exe" "Autoruns"
)
if exist "Gradle.zip" (
	echo Installing Gradle...
	xcopy /E /I /Q /Y "Gradle\" "C:\Gradle\"
	rmdir /S /Q "Gradle"
)
if exist "FFmpeg.zip" (
	echo Installing FFmpeg...
	tar -xf "FFmpeg.zip"
	ren "ffmpeg-master-latest-win64-gpl" "FFmpeg"
	xcopy /E /I /Q /Y "FFmpeg\" "%PF%\FFmpeg\"
	rmdir /S /Q "FFmpeg"
	call :SetPath "%PF%\FFmpeg\bin\"
)

for %%G in (!zipm!) do (
	set "progName=%%G"
	set "progName=!progName:_= !"

	if exist "!progName!.zip" (
		echo Installing !progName!...
		rmdir /S /Q "!progName!" 2>nul
		call :Extract "!progName!"
		call :FindExe "!progName!"

		if exeDir NEQ 0 (
			set "destPath=%PF%\!progName!"
			cd "!exeDir!"
			mkdir "!destPath!" 2>nul
			xcopy /E /I /Q /Y ".\" "!destPath!\"
			call :CreateShortcut "!destPath!\!exeName!" "!progName!"
			cd "%DLPath%"
			rmdir /S /Q "!progName!"
		)
	)
)

set DoneZip=1
goto :eof

:MSI

for %%G in ("%DLPath%\*_Setup.msi") do (
	set "progName=%%~nG"
	set "progPath=%%G"
	set "readableName=!progName:_= !"
	set "readableName=!readableName:~0,-6!"

	echo Running !readableName!...
	"!progPath!" /passive
)

set DoneMSI=1
goto :eof

:EXE

:: TO-DO
:: RE-WRITE CUSTOM EXE INSTALLATIONS - 33% Done

for %%G in (!pfexe!) do (
	set "progName=%%G"

	if exist "!progName!_Setup.exe" (
		set "readableName=!progName:_= !"
		set "PF_Dir=%PF%\!readableName!\"
		echo Installing !readableName!...

		move /Y "!progName!_Setup.exe" "!progName!.exe"
		mkdir "%PF%\!readableName!\" 2>nul
		xcopy /Q /Y "!progName!.exe" "!PF_Dir!"

		call :CreateShortcut "!PF_Dir!!progName!.exe" "!readableName!"
		del /S /Q "!progName!.exe"
		echo.
	)
)

choice /N /M "Install Silently? (Not Recommended) [Y/N] "
echo.

@REM Silent Installation
if !ErrorLevel! == 1 (
	for %%G in (!Flags!) do (
		for %%H in (!Flagged_%%G!) do (

			set "progName=%%H"
			set "flag=%%G"
			set "readableName=!progName:~0,-6!"

			if exist "!progName!_Setup.exe" (
				echo Installing !progName!...
				echo.
				start /wait "" "!progName!_Setup" /!flag!
				move /Y "!progName!_Setup.exe" "!progName!.exe"
			)
		)
	)

)

@REM Manual Installation
for %%G in ("%DLPath%\*_Setup.exe") do (
	set "progName=%%~nG"
	set "progPath=%%G"
	set "readableName=!progName:_= !"
	set "readableName=!readableName:~0,-6!"

	echo Running !readableName!...
	"!progPath!"
)

set DoneAll=1
goto :eof

:Extract
set "ZipName=%~1"
mkdir "%ZipName%" 2>nul
tar -xf "%DLPath%\%ZipName%.zip" -o -C "%DLPath%\%ZipName%"
goto :eof

:FindExe
set "searchPath=%~1"
set exeDir=0

for /r "%searchPath%" %%G in (*.exe) do (
	set "exeName=%%~nxG"
	set "exeDir=%%~dpG"
	goto :eof
)

:SetPath
set "dir=%~1"

REM Retrieve the system PATH from the registry
set "syspath="
for /f "skip=2 tokens=2,*" %%A in (
	'reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul'
) do set "syspath=%%B"

REM Check if the directory is already present in the system PATH
echo "!syspath!" | find /i "%dir%" >nul
if !errorlevel! EQU 0 (
	echo Directory "%dir%" is already in PATH.
	goto :eof
)

REM Trim extra semicolons from the end of syspath
:TrimSemicolons
if "!syspath:~-1!"==";" (
	set "syspath=!syspath:~0,-1!"
	goto TrimSemicolons
)

REM Set the updated PATH, making sure there's exactly one semicolon
setx /M PATH "!syspath!;%dir%;"

echo Directory "%dir%" was successfully added to PATH.

endlocal
goto :eof