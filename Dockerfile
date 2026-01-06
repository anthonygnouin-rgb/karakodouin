FROM python:3.9-slim

# 1. Installation des outils système
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# 2. On définit le dossier de travail
WORKDIR /app

# 3. On copie tes fichiers
COPY . .

# 4. On crée un dossier cache accessible à tout le monde (pour éviter les erreurs de permission)
RUN mkdir -p /app/.cache && chmod -R 777 /app/.cache
ENV XDG_CACHE_HOME=/app/.cache

# 5. Installation des librairies
RUN pip install --no-cache-dir -r requirements.txt

# 6. ASTUCE PRO : On force le téléchargement du modèle MAINTENANT
# Cela évite que l'app plante au démarrage en essayant de le télécharger
RUN python -c "import whisper; whisper.load_model('base')"

# 7. Ouverture du port
EXPOSE 7860

# 8. Lancement de l'application
CMD ["flet", "run", "app.py", "--web", "--port", "7860", "--host", "0.0.0.0"]
