@echo off
 
rem check file exists or not.
if not exist video-links.txt (
  echo video-links.txt file not exist
  goto end
)
 
rem read file, one row for each time, and read the first column as default splitted by blank space.
for /f %%i in ('type video-links.txt') do (
  echo %%i
  python twitter-dl.py %%i
)
 
 
:end
echo Press any key to continue
