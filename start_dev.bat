@echo off
REM -------------------------------
REM Fichier : start_dev.bat
REM Objectif : Prépare l’environnement de développement
REM -------------------------------

REM Se positionner dans le répertoire du script (racine du projet)
cd /d "%~dp0%"

REM Activation de l'environnement virtuel
if exist "Venv\Scripts\activate.bat" (
    call Venv\Scripts\activate.bat
) else (
    echo ERREUR : L'environnement virtuel n'a pas été trouvé dans le dossier Venv.
    pause
    exit /b 1
)

REM Définir les variables d'environnement pour Flask
set FLASK_APP=Code/app.py
set FLASK_ENV=development

REM (Optionnel) Mettre à jour la base de données
echo Mise à jour de la base de données...
flask db upgrade

REM (Optionnel) Lancer l'application Flask
REM Pour lancer l'application directement, décommentez la ligne suivante :
REM flask run

REM Ouvrir une invite de commandes interactive avec l'environnement activé
echo.
echo "L'environnement de développement est prêt."
echo "Vous pouvez désormais lancer vos commandes (ex. : 'flask run' ou 'python Code/scripts/extract_visio.py')."
cmd /k
