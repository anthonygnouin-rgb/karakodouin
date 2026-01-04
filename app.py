import streamlit as st
import whisper
import tempfile
import os
import requests
import numpy as np
import textwrap
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont

# --- CONFIGURATION ---
st.set_page_config(page_title="Karaoké XXL", layout="centered")

# --- 1. FONCTIONS ---
def download_font():
    url = "https://github.com/google/fonts/raw/main/ofl/anton/Anton-Regular.ttf"
    if not os.path.exists("karaoke_font.ttf"):
        try:
            r = requests.get(url)
            with open("karaoke_font.ttf", 'wb') as f: f.write(r.content)
        except: 
            pass 

def clean_text(text):
    try:
        return text.encode('latin-1', 'ignore').decode('latin-1').strip()
    except:
        return ""

def create_karaoke_frame(text, w, h):
    img = Image.new('RGBA', (w, h), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # TAILLE XXL : 30% de la hauteur
    fontsize = int(h * 0.30) 
    
    try:
        font = ImageFont.truetype("karaoke_font.ttf", fontsize)
    except:
        font = ImageFont.load_default()

    # On coupe le texte court (10 caractères max par ligne)
    lines = textwrap.wrap(text, width=10)
    
    line_height = fontsize * 1.1
    total_height = len(lines) * line_height
    current_y = (h - total_height) / 2
    
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        current_x = (w - text_w) / 2
        
        # Dessin avec contour (code coupé pour faciliter la copie)
        draw.text((current_x, current_y), line, font=font, 
                  fill='#FFD700', stroke_width=8, stroke_fill='black')
        
        current_y += line_height
        
    return np.array(img)

# --- 2. INTERFACE ---
st.title("🎤 KARAKODOUIN XXL")
st.markdown("ℹ️ *Texte géant (30%) - Parfait pour lire de loin.*")

download_font()

# Uploaders
audio = st.file_uploader("1. Musique", type=["mp3"], key="mp3_xxl")
bg = st.file_uploader("2. Fond", type=["jpg", "png", "mp4"], key="bg_xxl")

if st.button("Lancer la Vidéo 🎬") and audio and bg:
    st.info("🚀 Analyse en cours...")
    
    # C'EST ICI QUE L'ERREUR ÉTAIT (J'ai mis f1 et f2)
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
        st.info("🎨 Création visuelle...")
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

        bg_c = bg_c.resize(height=720)
        if bg_c.w % 2 != 0: bg_c = bg_c.resize(width=bg_c.w-1)
        
        subs = []
        bar = st.progress(0)
        
        for i, s in enumerate(segments):
            safe_text = clean_text(s["text"])
            if safe_text:
                img = create_karaoke_frame(safe_text, bg_c.w, bg_c.h)
                clip = (ImageClip(img)
                        .set_start(s["start"])
                        .set_end(s["end"])
                        .set_position('center'))
                subs.append(clip)
            bar.progress((i + 1) / len(segments))
            
        final = CompositeVideoClip([bg_c] + subs).set_audio(audio_c)
        
        out = "karaoke_xxl.mp4"
        final.write_videofile(out, fps=24, codec="libx264", 
                              audio_codec="aac", preset="ultrafast")
        
        st.success("✅ Terminé !")
        with open(out, "rb") as f:
            st.download_button("Télécharger", f, file_name="karaoke_xxl.mp4")
            
    except Exception as e:
        st.error(f"Erreur : {e}")
