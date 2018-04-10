del /S /Q *.pyc
del /S /Q *.bak
for /r .\ %%i in (__pycache__) do (
    rd /S /Q %%i
)
del MailOutInfo.txt
del procLog_
del procLog_*.log
del /S /Q dir_temp_data\*.*