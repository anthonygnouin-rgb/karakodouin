import streamlit as st
import whisper
import tempfile
import os
import numpy as np
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont

# --- FONCTION DE SECOURS POUR ÉCRIRE LE TEXTE (Sans ImageMagick) ---
def creer_image_texte(texte, fontsize, color, size):
    # Création d'une image transparente
    img = Image.new('RGBA', size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Police par défaut
    try:
        # On essaie une police plus grande si possible
        font = ImageFont.truetype("arial.ttf", fontsize)
    except IOError:
        font = ImageFont.load_default()
    
    # Positionnement approximatif (bas de l'écran centré)
    # On calcule la position pour que le texte soit en bas
    text_position = (50, size[1] - 150) 
    
    draw.text(text_position, texte, font=font, fill=color)
    return np.array(img)

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Karakodouin V2", layout="centered")
st.title("🎤 KARAKODOUIN - Mode Vidéo")

# --- INTERFACE ---
st.write("### 1. La Musique")
audio_file = st.file_uploader("Chargez le MP3", type=["mp3"], key="audio_uploader")

st.write("### 2. Le Fond (Image OU Vidéo)")
background_file = st.file_uploader("Chargez une Image (JPG/PNG) ou une Vidéo (MP4)", type=["jpg", "png", "jpeg", "mp4"], key="bg_uploader")

# --- LOGIQUE ---
if st.button("Lancer la création 🎬") and audio_file and background_file:
    st.info("⏳ Analyse en cours... Ne touchez à rien.")
    
    # 1. Sauvegarde des fichiers temporaires
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_audio:
        tmp_audio.write(audio_file.read())
        audio_path = tmp_audio.name
    
    # On détecte si c'est une image ou une vidéo par l'extension du fichier uploadé
    bg_is_video = background_file.name.lower().endswith(".mp4")
    suffix_bg = ".mp4" if bg_is_video else ".png"
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix_bg) as tmp_bg:
        tmp_bg.write(background_file.read())
        bg_path = tmp_bg.name

    try:
        # 2. Transcription Whisper
        model = whisper.load_model("base")
        result = model.transcribe(audio_path)
        segments = result["segments"]
        st.success("✅ Paroles détectées !")

        # 3. Montage
        st.info("🎬 Montage vidéo en cours...")
        
        audio_clip = AudioFileClip(audio_path)
        
        if bg_is_video:
            # Si c'est une vidéo
            background_clip = VideoFileClip(bg_path)
            # On coupe ou on boucle la vidéo pour qu'elle fasse la même durée que le son
            if background_clip.duration < audio_clip.duration:
                background_clip = background_clip.loop(duration=audio_clip.duration)
            else:
                background_clip = background_clip.subclip(0, audio_clip.duration)
            # On garde le son de la musique, pas de la vidéo de fond
            background_clip = background_clip.set_audio(None)
        else:
            # Si c'est une image
            background_clip = ImageClip(bg_path).set_duration(audio_clip.duration)

        # IMPORTANT : On force une taille standard (ex: format carré ou vertical mobile)
        # Sinon MoviePy plante si les tailles sont impaires
        background_clip = background_clip.resize(height=720) # Hauteur standard
        # On s'assure que la largeur est paire (bug fréquent x264)
        w, h = background_clip.size
        if w % 2 != 0:
            background_clip = background_clip.resize(width=w-1)

        subtitles = []
        
        # Création des sous-titres
        for segment in segments:
            start = segment["start"]
            end = segment["end"]
            text = segment["text"].strip()
            
            # Utilisation de notre fonction Pillow
            txt_img = creer_image_texte(text, 40, 'white', background_clip.size)
            
            txt_clip = (ImageClip(txt_img)
                        .set_start(start)
                        .set_end(end)
                        .set_position('center')
                        .set_duration(end - start))
            
            subtitles.append(txt_clip)
        
        # Assemblage final
        final_video = CompositeVideoClip([background_clip] + subtitles)
        final_video = final_video.set_audio(audio_clip)
        
        output_filename = "karaoke_final.mp4"
        # Preset ultrafast pour que ça ne plante pas sur mobile
        final_video.write_videofile(output_filename, fps=24, codec="libx264", audio_codec="aac", preset="ultrafast")
        
        st.balloons()
        st.success("✨ C'est prêt !")
        
        with open(output_filename, "rb") as file:
            st.download_button("⬇️ TÉLÉCHARGER VIDÉO", file, file_name="mon_karaoke.mp4")

    except Exception as e:
        st.error(f"Erreur technique : {e}")

    # Nettoyage
    if os.path.exists(audio_path): os.unlink(audio_path)
    if os.path.exists(bg_path): os.unlink(bg_path)
        
