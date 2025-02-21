@echo off
REM ========================================
REM Script de démarrage sans clé OpenAI 
REM (la clé est chargée depuis .env par app.py)
REM ========================================

REM 1) Activer l'environnement virtuel
REM    Ajuste le chemin si nécessaire
call "C:\path\to\mon\projet\Venv\Scripts\activate.bat"

REM 2) Installer les dépendances listées dans requirements.txt
pip install -r requirements.txt

REM 3) (Optionnel) Forcer la version openai si nécessaire
pip install openai==0.28

REM 4) Lancer l'application Flask
REM    (en supposant que app.py se trouve dans Code\app.py)
python Code\app.py

REM 5) Rester en pause à la fin (pour voir les logs)
pause
REM 6) Une fois dans le terminal intégré, navigue (si nécessaire) jusqu’à la racine de ton projet (là où se trouve le fichier run_app_no_key.bat) et exécute .\run_app_no_key.bat