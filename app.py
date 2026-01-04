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
st.set_page_config(page_title="Karaoké V5 Pro", layout="centered")

# --- 1. POLICE ---
def download_font():
    url = "https://github.com/google/fonts/raw/main/ofl/anton/Anton-Regular.ttf"
    if not os.path.exists("karaoke_font.ttf"):
        try:
            r = requests.get(url)
            with open("karaoke_font.ttf", 'wb') as f: f.write(r.content)
        except: 
            pass 

# --- 2. ANTI-CRASH (Nettoyage) ---
def clean_text(text):
    try:
        # Garde uniquement les caractères latins (enlève ♪, ♫, emojis)
        return text.encode('latin-1', 'ignore').decode('latin-1').strip()
    except:
        return ""

# --- 3. DESSIN (Actuel + Suivant) ---
def create_karaoke_frame(current_text, next_text, w, h):
    img = Image.new('RGBA', (w, h), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # --- A. TEXTE PRINCIPAL (10% - JAUNE) ---
    font_size_main = int(h * 0.10)
    try:
        font_main = ImageFont.truetype("karaoke_font.ttf", font_size_main)
    except:
        font_main = ImageFont.load_default()

    # Découpage (Wrapping) pour que ça tienne
    lines_main = textwrap.wrap(current_text, width=20)
    
    # Calcul de la hauteur du bloc principal
    line_height_main = font_size_main * 1.2
    total_height_main = len(lines_main) * line_height_main
    
    # On place le texte principal un peu au-dessus du centre
    start_y_main = (h - total_height_main) / 2 - (h * 0.05)
    
    current_y = start_y_main
    for line in lines_main:
        bbox = draw.textbbox((0, 0), line, font=font_main)
        text_w = bbox[2] - bbox[0]
        pos_x = (w - text_w) / 2
        
        # Jaune avec contour Noir
        draw.text((pos_x, current_y), line, font=font_main, 
                  fill='#FFD700', stroke_width=5, stroke_fill='black')
        current_y += line_height_main

    # --- B. TEXTE SUIVANT (4% - BLANC) ---
    if next_text:
        font_size_next = int(h * 0.04)
        try:
            font_next = ImageFont.truetype("karaoke_font.ttf", font_size_next)
        except:
            font_next = ImageFont.load_default()
            
        # On prépare le texte suivant (on met "..." au début)
        next_text_display = f"... {next_text} ..."
        lines_next = textwrap.wrap(next_text_display, width=40)
        
        # On le place un peu plus bas
        start_y_next = current_y + (h * 0.05)
        
        for line in lines_next:
            bbox = draw.textbbox((0, 0), line, font=font_next)
            text_w = bbox[2] - bbox[0]
            pos_x = (w - text_w) / 2
            
            # Blanc (ou Gris clair) avec petit contour
            draw.text((pos_x, start_y_next), line, font=font_next, 
                      fill='#E0E0E0', stroke_width=2, stroke_fill='black')
            start_y_next += (font_size_next * 1.2)
        
    return np.array(img)

# --- INTERFACE ---
st.title("🎤 KARAKODOUIN V5 - Pro")
st.markdown("ℹ️ *Affiche les paroles (10%) et la phrase suivante.*")

download_font()

audio = st.file_uploader("1. Musique", type=["mp3"], key="mp3_v5")
bg = st.file_uploader("2. Fond", type=["jpg", "png", "mp4"], key="bg_v5")

if st.button("Lancer la Vidéo 🎬") and audio and bg:
    st.info("🚀 Analyse et prédiction des paroles...")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f1:
        f1.write(audio.read())
        audio_path = f1.name
        
    is_video = bg.name.lower().endswith(".mp4")
    ext = ".mp4" if is_video else ".png"
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as f2:
        f2.write(bg.read())
        bg_path = f2.name

    try:
        model = whisper.load_model("base")
        result = model.transcribe(audio_path)
        segments = result["segments"]
        
        st.info("🎨 Montage (Patience, c'est précis)...")
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
        total = len(segments)
        
        for i in range(total):
            # 1. Texte Actuel
            current_seg = segments[i]
            txt_now = clean_text(current_seg["text"])
            
            # 2. Texte Suivant (Prédiction)
            txt_next = ""
            if i + 1 < total: # S'il y a une phrase après
                txt_next = clean_text(segments[i+1]["text"])
            
            if txt_now:
                # On envoie les DEUX textes à la fonction de dessin
                img = create_karaoke_frame(txt_now, txt_next, bg_c.w, bg_c.h)
                
                clip = (ImageClip(img)
                        .set_start(current_seg["start"])
                        .set_end(current_seg["end"])
                        .set_position('center'))
                subs.append(clip)
            
            bar.progress((i + 1) / total)
            
        final = CompositeVideoClip([bg_c] + subs).set_audio(audio_c)
        
        out = "karaoke_pro.mp4"
        final.write_videofile(out, fps=24, codec="libx264", 
                              audio_codec="aac", preset="ultrafast")
        
        st.success("✅ Terminé !")
        with open(out, "rb") as f:
            st.download_button("Télécharger", f, file_name="karaoke_pro.mp4")
            
    except Exception as e:
        st.error(f"Erreur : {e}")
                
