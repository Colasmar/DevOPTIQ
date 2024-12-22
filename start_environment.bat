@echo off
REM Ce script réinitialise l'environnement de développement et lance l'application Flask.

REM Emplacement du projet (adapté à votre situation)
set PROJECT_DIR=C:\Users\Hubert.AFDEC\A.F.D.E.C\Projet OPTIQ - DevOPTIQ

REM Se placer dans le répertoire du projet
cd "%PROJECT_DIR%"

echo Vérification de la version de Git...
git --version
if errorlevel 1 (
    echo Git n'est pas trouvé. Veuillez installer Git ou vérifier votre variable PATH.
    pause
    exit /b 1
)

echo Vérification de la version de Python...
python --version
if errorlevel 1 (
    echo Python n'est pas trouvé. Veuillez installer Python ou vérifier votre variable PATH.
    pause
    exit /b 1
)

echo Activation de l'environnement virtuel Python...
call "%PROJECT_DIR%\Venv\Scripts\activate.bat"
if errorlevel 1 (
    echo Impossible d'activer l'environnement virtuel. Vérifiez que le dossier Venv existe et est un environnement Python valide.
    pause
    exit /b 1
)

echo Installation/mise à jour des dépendances...
pip install -r "%PROJECT_DIR%\requirements.txt"
if errorlevel 1 (
    echo Echec de l'installation des dépendances. Vérifiez votre connexion internet ou le fichier requirements.txt.
    pause
    exit /b 1
)

REM Se positionner dans le répertoire Code avant de lancer l'application
cd "%PROJECT_DIR%\Code"

echo Tout est prêt. Nous allons lancer l'application Flask.
python app.py

pause
