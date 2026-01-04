import streamlit as st
import tempfile
import os
import whisper
import moviepy.editor as mp
from moviepy.config import change_settings

# Configuration pour que MoviePy trouve ImageMagick sur le serveur
change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"})

st.title("🎤 KARAKODOUIN")
st.write("Le générateur de Karaoké par Intelligence Artificielle")

# --- CHARGEMENT DU CERVEAU (IA) ---
# On met l'IA en mémoire cache pour ne pas la recharger à chaque fois (ça gagne du temps)
@st.cache_resource
def charger_ia():
    return whisper.load_model("base")

model = charger_ia()

# --- INTERFACE ---
st.info("💡 Astuce : L'IA va écouter votre musique et écrire les paroles elle-même pour être parfaitement calée !")

col1, col2 = st.columns(2)
with col1:
    fichier_audio = st.file_uploader("1. Votre fichier MP3", type=["mp3"])
with col2:
    fichier_fond = st.file_uploader("2. Image ou Vidéo de fond", type=["jpg", "png", "mp4"])

format_video = st.radio(
    "3. Format de la vidéo :",
    ["Portrait (TikTok/Reels - 9:16)", "Paysage (YouTube - 16:9)"]
)

# --- LA FONCTION MAGIQUE ---
def creer_karaoke(audio_file, fond_file, format_v):
    # 1. Sauvegarde temporaire des fichiers sur le serveur
    tfile_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tfile_audio.write(audio_file.read())
    path_audio = tfile_audio.name

    tfile_fond = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4" if fond_file.name.endswith(".mp4") else ".jpg")
    tfile_fond.write(fond_file.read())
    path_fond = tfile_fond.name

    # 2. L'IA écoute (Transcription)
    status.text("👂 L'IA écoute la chanson pour caler le rythme...")
    resultat = model.transcribe(path_audio)
    segments = resultat["segments"] # Liste des phrases avec leur timing précis

    # 3. Préparation du montage vidéo
    status.text("🎬 Montage de la vidéo en cours...")
    
    # Chargement de l'audio
    audio_clip = mp.AudioFileClip(path_audio)
    duree = audio_clip.duration

    # Création du fond (Background)
    if path_fond.endswith(".mp4"):
        fond_clip = mp.VideoFileClip(path_fond)
        # On boucle la vidéo de fond si elle est trop courte
        fond_clip = fond_clip.loop(duration=duree)
        # On coupe le son de la vidéo de fond pour garder la musique
        fond_clip = fond_clip.without_audio()
    else:
        # C'est une image
        fond_clip = mp.ImageClip(path_fond).set_duration(duree)

    # Redimensionnement selon le format choisi
    if "Portrait" in format_v:
        w, h = 1080, 1920
        # On coupe le fond pour qu'il remplisse l'écran vertical
        fond_clip = fond_clip.resize(height=1920) 
        fond_clip = fond_clip.crop(x1=fond_clip.w/2 - 540, width=1080, height=1920)
    else:
        w, h = 1920, 1080
        fond_clip = fond_clip.resize(width=1920)

    # 4. Création des paroles (Texte par dessus)
    clips_textes = []
    
    for segment in segments:
        texte = segment["text"].strip()
        start = segment["start"]
        end = segment["end"]
        
        # Création du clip texte
        txt_clip = (mp.TextClip(texte, fontsize=70, color='white', font='Arial-Bold', stroke_color='black', stroke_width=2, size=(w-100, None), method='caption')
                    .set_position(('center', 'center'))
                    .set_start(start)
                    .set_end(end))
        clips_textes.append(txt_clip)

    # Assemblage final (Fond + Textes)
    video_finale = mp.CompositeVideoClip([fond_clip] + clips_textes)
    video_finale = video_finale.set_audio(audio_clip)

    # Exportation
    output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
    # Note : On utilise un preset rapide pour ne pas faire attendre trop longtemps
    video_finale.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24, preset="ultrafast")
    
    return output_path

# --- LE BOUTON D'ACTION ---
if st.button("Lancer la création (Cela peut prendre quelques minutes)"):
    if fichier_audio and fichier_fond:
        status = st.empty() # Zone pour afficher l'avancement
        with st.spinner('Les robots travaillent... 🤖'):
            try:
                chemin_video = creer_karaoke(fichier_audio, fichier_fond, format_video)
                
                st.success("✅ Vidéo terminée !")
                
                # Lecture de la vidéo générée pour le téléchargement
                with open(chemin_video, "rb") as file:
                    video_bytes = file.read()
                    
                st.download_button(
                    label="📥 Télécharger ma vidéo KARAKODOUIN",
                    data=video_bytes,
                    file_name="mon_karaoke.mp4",
                    mime="video/mp4"
                )
            except Exception as e:
                st.error(f"Une erreur est survenue : {e}")
    else:
        st.warning("Il manque le fichier MP3 ou le fond !")
        
