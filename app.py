import streamlit as st
import whisper
import tempfile
import os
import requests
import numpy as np
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont

# --- CONFIGURATION ---
st.set_page_config(page_title="Karaoké V3", layout="centered")

# --- FONCTIONS ---
def download_font():
    # On télécharge une police "Gras" pour que ce soit lisible
    url = "https://github.com/google/fonts/raw/main/apache/robotoslab/RobotoSlab-Bold.ttf"
    if not os.path.exists("font.ttf"):
        try:
            r = requests.get(url)
            with open("font.ttf", 'wb') as f: f.write(r.content)
        except: 
            pass # Cette ligne est maintenant bien alignée !

def create_karaoke_frame(text, w, h):
    # Création d'une image transparente
    img = Image.new('RGBA', (w, h), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Taille du texte : 6% de la hauteur de la vidéo (Gros)
    fontsize = int(h * 0.06)
    
    try:
        font = ImageFont.truetype("font.ttf", fontsize)
    except:
        font = ImageFont.load_default()

    # Calcul pour centrer parfaitement
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (w - text_w) / 2
    y = (h - text_h) / 2
    
    # Texte Jaune avec Contour Noir (Lisible sur tout)
    draw.text((x, y), text, font=font, fill='yellow', stroke_width=3, stroke_fill='black')
    return np.array(img)

# --- INTERFACE ---
st.title("🎤 KARAKODOUIN V3")
st.markdown("**1.** Attendez que la roue en haut à droite s'arrête.\n**2.** Si l'upload échoue, ne rafraichissez pas, réessayez juste le fichier.")

download_font()

# On utilise une clé unique pour forcer le nettoyage du cache d'upload
audio = st.file_uploader("Musique (MP3)", type=["mp3"], key="mp3_load")
bg = st.file_uploader("Fond (Image ou Vidéo)", type=["jpg", "png", "mp4"], key="bg_load")

if st.button("Lancer la Vidéo 🎬") and audio and bg:
    st.info("🚀 Analyse de l'audio en cours...")
    
    # Fichiers temporaires
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f1:
        f1.write(audio.read())
        audio_path = f1.name
        
    is_video = bg.name.lower().endswith(".mp4")
    ext = ".mp4" if is_video else ".png"
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as f2:
        f2.write(bg.read())
        bg_path = f2.name

    try:
        # Whisper
        model = whisper.load_model("base")
        result = model.transcribe(audio_path)
        segments = result["segments"]
        
        # Montage
        st.info("🎨 Création des visuels...")
        audio_c = AudioFileClip(audio_path)
        
        if is_video:
            bg_c = VideoFileClip(bg_path)
            # Boucle vidéo
            if bg_c.duration < audio_c.duration:
                bg_c = bg_c.loop(duration=audio_c.duration)
            else:
                bg_c = bg_c.subclip(0, audio_c.duration)
            bg_c = bg_c.set_audio(None)
        else:
            bg_c = ImageClip(bg_path).set_duration(audio_c.duration)

        # Redimensionnement standard (Evite les bugs de taille)
        bg_c = bg_c.resize(height=720)
        if bg_c.w % 2 != 0: bg_c = bg_c.resize(width=bg_c.w-1)
        
        subs = []
        for s in segments:
            img = create_karaoke_frame(s["text"].strip(), bg_c.w, bg_c.h)
            clip = (ImageClip(img)
                    .set_start(s["start"])
                    .set_end(s["end"])
                    .set_position('center'))
            subs.append(clip)
            
        final = CompositeVideoClip([bg_c] + subs).set_audio(audio_c)
        
        out = "karaoke_final.mp4"
        final.write_videofile(out, fps=24, codec="libx264", audio_codec="aac", preset="ultrafast")
        
        st.success("✅ Terminé !")
        with open(out, "rb") as f:
            st.download_button("Télécharger Vidéo", f, file_name="karaoke.mp4")
            
    except Exception as e:
        st.error(f"Erreur : {e}")
