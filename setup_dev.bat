@echo off
echo Initialisation de l'environnement de développement...

:: Activer l'environnement virtuel
echo Activation de l'environnement virtuel...
call Venv\Scripts\activate

:: Vérification des modules requis
echo Vérification des dépendances...
pip install -r requirements.txt

:: Vérification des variables d'environnement Flask
echo Configuration des variables d'environnement...
set FLASK_APP=Code/app.py
set FLASK_ENV=development

:: Lancer le serveur Flask
echo Lancement du serveur Flask...
python -m flask run

:: Fin du script
echo Environnement prêt. Vous pouvez commencer à développer.
pause
