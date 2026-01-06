FROM python:3.9-slim

# 1. Installation des outils système (ffmpeg est vital pour le son)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# 2. Création du dossier de travail
WORKDIR /app

# 3. Copie de tous tes fichiers GitHub vers le serveur
COPY . .

# 4. Installation des librairies Python (Flet, Whisper...)
RUN pip install --no-cache-dir -r requirements.txt

# 5. Création d'un dossier cache pour le modèle Whisper (évite les erreurs de permission)
RUN mkdir -p /.cache && chmod 777 /.cache

# 6. Ouverture du port standard Hugging Face
EXPOSE 7860

# 7. Lancement de l'application
CMD ["flet", "run", "app.py", "--web", "--port", "7860", "--host", "0.0.0.0"]

