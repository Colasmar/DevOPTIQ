@echo off
REM ========================================
REM Script de démarrage sans clé OpenAI 
REM (la clé est chargée depuis .env par app.py)
REM ========================================

echo Activation de l'environnement virtuel...
call "%~dp0Venv\Scripts\activate.bat"

echo Installation des dépendances...
pip install -r requirements.txt

echo Forçage de la version openai (0.28)...
pip install openai==0.28

echo Lancement de l'application Flask...
python Code\app.py

echo Terminal ouvert pour continuer...
cmd /k

REM ========================================
REM Une fois dans le terminal intégré, naviguez (si nécessaire)
REM jusqu’à la racine du projet et exécutez .\run_app_no_key.bat
REM ou réactivez l'environnement avec .\Venv\Scripts\Activate
REM ========================================
