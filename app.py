import streamlit as st
import whisper
import tempfile
import os
import requests
import numpy as np
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont

# --- CONFIGURATION ---
st.set_page_config(page_title="Karaoké V3.2", layout="centered")

# --- FONCTIONS ---
def download_font():
    # On télécharge une police "Gras" pour que ce soit lisible
    url = "https://github.com/google/fonts/raw/main/apache/robotoslab/RobotoSlab-Bold.ttf"
    if not os.path.exists("font.ttf"):
        try:
            r = requests.get(url)
            with open("font.ttf", 'wb') as f: f.write(r.content)
        except: 
            pass 

def clean_text(text):
    # C'est ICI que la magie opère.
    # On force le texte à rester dans les caractères standards (Latin-1).
    # Ça supprime les notes de musique ♪ ♫ et les emojis qui font planter le serveur.
    try:
        return text.encode('latin-1', 'ignore').decode('latin-1').strip()
    except:
        return "" # Si ça plante vraiment, on renvoie du vide pour ne pas crasher

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
st.title("🎤 KARAKODOUIN V3.2 (Anti-Crash)")
st.markdown("ℹ️ *Si l'upload échoue, réessayez sans rafraichir la page.*")

download_font()

# Clés uniques pour forcer le nettoyage
audio = st.file_uploader("1. Musique (MP3)", type=["mp3"], key="mp3_v3")
bg = st.file_uploader("2. Fond (Image/Vidéo)", type=["jpg", "png", "mp4"], key="bg_v3")

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
        st.info("🎨 Création des visuels (Nettoyage des symboles activé)...")
        audio_c = AudioFileClip(audio_path)
        
        if is_video:
            bg_c = VideoFileClip(bg_path)
            if bg_c.duration < audio_c.duration:
                bg_c = bg_c.loop(duration=audio_c.duration)
            else:
                bg_c = bg_c.subclip(0, audio_c.duration)
            bg_c = bg_c.set_audio(None)
        else:
            bg_c = ImageClip(bg_path).set_duration(audio_c.duration)

        # Redimensionnement standard 720p
        bg_c = bg_c.resize(height=720)
        if bg_c.w % 2 != 0: bg_c = bg_c.resize(width=bg_c.w-1)
        
        subs = []
        # Barre de progression
        my_bar = st.progress(0)
        total_seg = len(segments)

        for i, s in enumerate(segments):
            # ON NETTOIE LE TEXTE ICI AVANT DE DESSINER
            raw_text = s["text"]
            safe_text = clean_text(raw_text)
            
            # Si le texte n'est pas vide après nettoyage, on crée l'image
            if safe_text:
                img = create_karaoke_frame(safe_text, bg_c.w, bg_c.h)
                clip = (ImageClip(img)
                        .set_start(s["start"])
                        .set_end(s["end"])
                        .set_position('center'))
                subs.append(clip)
            
            # Mise à jour de la barre
            my_bar.progress((i + 1) / total_seg)
            
        final = CompositeVideoClip([bg_c] + subs).set_audio(audio_c)
        
        out = "karaoke_final.mp4"
        final.write_videofile(out, fps=24, codec="libx264", audio_codec="aac", preset="ultrafast")
        
        st.success("✅ Terminé !")
        with open(out, "rb") as f:
            st.download_button("Télécharger Vidéo", f, file_name="karaoke.mp4")
            
    except Exception as e:
        st.error(f"Erreur : {e}")
