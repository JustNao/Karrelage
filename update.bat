@echo off

REM Check if .git directory exists
IF NOT EXIST ".git" (
    echo Initializing Git repository...
    git init
    git remote add origin https://github.com/JustNao/Karrelage.git
    echo Git repository initialized and remote set.
)

REM Perform git pull or git clone based on existence of .git directory
IF EXIST ".git" (
    echo Updating the project...
    git pull origin master
) ELSE (
    echo There was an error initializing the Git repository.
    echo Please check if Git is installed and try again.
)

pause