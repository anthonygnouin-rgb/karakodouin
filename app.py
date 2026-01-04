import streamlit as st
import whisper
import tempfile
import os
import numpy as np
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont

# --- FONCTION DE SECOURS POUR ÉCRIRE LE TEXTE (Sans ImageMagick) ---
def creer_image_texte(texte, fontsize, color, size):
    # Création d'une image transparente avec Pillow
    img = Image.new('RGBA', size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Tentative de charger une police par défaut, sinon police simple
    try:
        font = ImageFont.truetype("arial.ttf", fontsize)
    except IOError:
        font = ImageFont.load_default()
    
    # Calcul pour centrer le texte (méthode approximative compatible)
    # On dessine le texte au centre de l'image
    # Note: Sur mobile/serveur linux, le centrage parfait est complexe sans police externe
    # On positionne le texte un peu en bas
    text_position = (50, size[1] - fontsize - 50) 
    
    draw.text(text_position, texte, font=font, fill=color)
    
    # Conversion en format compréhensible par MoviePy
    return np.array(img)

# --- APPLICATION PRINCIPALE ---
st.title("🎤 KARAKODOUIN - Version Finale")

# 1. Chargement du MP3
audio_file = st.file_uploader("1. Choisissez votre musique (MP3)", type=["mp3"])

# 2. Chargement du fond
image_file = st.file_uploader("2. Choisissez l'image de fond", type=["jpg", "png", "jpeg"])

if st.button("Lancer la création 🎬") and audio_file and image_file:
    st.info("👂 L'IA écoute la chanson (cela peut prendre 1 à 2 minutes)...")
    
    # Sauvegarde temporaire des fichiers
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_audio:
        tmp_audio.write(audio_file.read())
        audio_path = tmp_audio.name
        
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_image:
        tmp_image.write(image_file.read())
        image_path = tmp_image.name

    try:
        # A. Transcription avec Whisper
        model = whisper.load_model("base")
        result = model.transcribe(audio_path)
        segments = result["segments"]
        st.success("✅ Paroles trouvées !")

        # B. Création de la vidéo
        st.info("🎬 Montage de la vidéo (Technique 'Pillow' activée)...")
        
        # Préparation de l'audio
        audio_clip = AudioFileClip(audio_path)
        
        # Préparation du fond
        background_clip = ImageClip(image_path).set_duration(audio_clip.duration)
        
        # Si l'image est trop petite, on la redimensionne (ex: format HD)
        w, h = background_clip.size
        # On s'assure d'avoir une taille standard si besoin, sinon on garde l'original
        
        subtitles = []
        
        for segment in segments:
            start_time = segment["start"]
            end_time = segment["end"]
            text = segment["text"].strip()
            
            # Utilisation de la méthode manuelle (Pillow) au lieu de TextClip
            # On crée une image transparente avec le texte dessus
            txt_img_array = creer_image_texte(text, fontsize=50, color='white', size=background_clip.size)
            
            txt_clip = (ImageClip(txt_img_array)
                        .set_start(start_time)
                        .set_end(end_time)
                        .set_position('center')
                        .set_duration(end_time - start_time))
            
            subtitles.append(txt_clip)
        
        # Superposition finale
        final_video = CompositeVideoClip([background_clip] + subtitles)
        final_video = final_video.set_audio(audio_clip)
        
        # Exportation
        output_filename = "karaoke_final.mp4"
        final_video.write_videofile(output_filename, fps=24, codec="libx264", audio_codec="aac")
        
        st.balloons()
        st.success("✨ Vidéo terminée !")
        
        with open(output_filename, "rb") as file:
            st.download_button("⬇️ TÉLÉCHARGER MA VIDÉO", file, file_name="mon_karaoke.mp4")

    except Exception as e:
        st.error(f"Une erreur est survenue : {e}")
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
        
