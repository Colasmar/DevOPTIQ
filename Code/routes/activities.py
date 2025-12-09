# Code/routes/activities.py
#
# Fichier "agrégateur" qui remplace l'ancien activities.py trop lourd.
# Il importe le blueprint et les différents sous-modules pour couvrir
# toutes les fonctionnalités (affichage, constraints, form, performance, etc.).

from .activities_bp import activities_bp

# On importe les sous-fichiers pour avoir le même comportement que l'ancien code monolithique.
from .activities_view import *
from .activities_form import *
from .activities_constraints import *
from .activities_performance import *
from .activities_render import *
from .activities_data import *
from .activities_cartography import *
from .activities_map import *
