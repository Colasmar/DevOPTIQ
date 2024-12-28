@echo off
REM Script pour configurer et lancer l'environnement de développement Flask.

REM 1. Définir le répertoire racine de votre projet.
set PROJECT_DIR=C:\Users\Hubert.AFDEC\A.F.D.E.C\Projet OPTIQ - DevOPTIQ

REM 2. Aller dans le répertoire du projet.
cd "%PROJECT_DIR%"

REM 3. Vérification des outils nécessaires.
echo Vérification de la version de Git...
git --version
if errorlevel 1 (
    echo Erreur : Git n'est pas trouvé. Installez Git ou ajoutez-le au PATH.
    pause
    exit /b 1
)

echo Vérification de la version de Python...
python --version
if errorlevel 1 (
    echo Erreur : Python n'est pas trouvé. Installez Python ou ajoutez-le au PATH.
    pause
    exit /b 1
)

REM 4. Activer l'environnement virtuel Python.
echo Activation de l'environnement virtuel Python...
call "%PROJECT_DIR%\Venv\Scripts\activate.bat"
if errorlevel 1 (
    echo Erreur : Impossible d'activer l'environnement virtuel. Vérifiez le dossier Venv.
    pause
    exit /b 1
)

REM 5. Installer les dépendances.
echo Installation/mise à jour des dépendances Python...
pip install -r "%PROJECT_DIR%\requirements.txt"
if errorlevel 1 (
    echo Erreur : Échec de l'installation des dépendances. Vérifiez requirements.txt.
    pause
    exit /b 1
)

REM 6. Vérification des chemins de fichiers critiques.
if not exist "%PROJECT_DIR%\Code\app.py" (
    echo Erreur : Le fichier app.py est introuvable dans le répertoire Code.
    pause
    exit /b 1
)

REM 7. Configurer Flask pour le lancement.
echo Configuration de l'application Flask...
set FLASK_APP=app.py
set FLASK_ENV=development

REM 8. Naviguer dans le répertoire contenant le code.
cd "%PROJECT_DIR%\Code"

REM 9. Lancer l'application Flask.
echo Lancement de l'application Flask...
flask run
if errorlevel 1 (
    echo Erreur : Échec du lancement de l'application Flask.
    pause
    exit /b 1
)

REM 10. Pause pour maintenir la fenêtre ouverte en cas d'erreur.
pause
