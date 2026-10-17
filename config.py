# -*- coding: utf-8 -*-
"""Configuration du site — change ici tes mots de passe."""
import os

# Mot de passe des ETUDIANTS (à donner aux élèves)
STUDENT_PASSWORD = "hackerlab2026"

# Ton mot de passe ADMIN (upload / suppression des PDF) — ne le donne à personne
ADMIN_PASSWORD = "admin2026"

# Durée de session (jours)
SESSION_DAYS = 7

# Clé de signature des sessions.
# Sur Vercel : définis SESSION_SECRET dans "Settings -> Environment Variables".
# En local : la valeur par défaut ci-dessous est utilisée.
SECRET = os.environ.get("SESSION_SECRET", "hackerlab-secret-2026-a7f3")
