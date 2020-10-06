@echo off

rem check file exists or not.
if not exist twitter-links.txt (
  echo twitter-links.txt file not exist
  goto end
)

rem read file, one row for each time, and read the first column as default splitted by blank space.
for /f %%i in ('type twitter-links.txt') do (
  echo %%i
  python twitter_list_dl.py %%i -o D:\\Downloads\\twitter -r 1
)


:end
echo Press any key to continue
