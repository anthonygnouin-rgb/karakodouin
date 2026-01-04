import streamlit as st
import tempfile
import os
import requests
import numpy as np
import textwrap
import re
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont

# --- CONFIGURATION ---
st.set_page_config(page_title="Karaoké V13 - Import SRT", layout="centered")

# --- FONCTIONS ---
def download_font():
    url = "https://github.com/google/fonts/raw/main/ofl/anton/Anton-Regular.ttf"
    if not os.path.exists("karaoke_font.ttf"):
        try:
            r = requests.get(url)
            with open("karaoke_font.ttf", 'wb') as f: f.write(r.content)
        except: pass 

def srt_time_to_seconds(time_str):
    # Convertit "00:00:12,500" en 12.5
    try:
        hours, minutes, seconds = time_str.replace(',', '.').split(':')
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    except:
        return 0.0

def parse_srt(srt_content):
    segments = []
    # On découpe par blocs (double saut de ligne)
    blocks = srt_content.strip().split('\n\n')
    
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 3:
            # La ligne 2 contient les temps : 00:00:12,000 --> 00:00:15,000
            time_line = lines[1]
            if '-->' in time_line:
                start_str, end_str = time_line.split('-->')
                start = srt_time_to_seconds(start_str.strip())
                end = srt_time_to_seconds(end_str.strip())
                
                # Le reste, c'est du texte (parfois sur plusieurs lignes)
                text = " ".join(lines[2:])
                
                segments.append({
                    'start': start,
                    'end': end,
                    'text': text
                })
    return segments

def create_karaoke_frame(current_text, next_text, w, h):
    img = Image.new('RGBA', (w, h), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # POLICE (10% hauteur)
    font_size = int(h * 0.10)
    try:
        font = ImageFont.truetype("karaoke_font.ttf", font_size)
    except:
        font = ImageFont.load_default()

    # TEXTE ACTUEL (JAUNE)
    lines = textwrap.wrap(str(current_text), width=20)
    line_height = font_size * 1.2
    total_h = len(lines) * line_height
    curr_y = (h - total_h) / 2 - (h * 0.05)
    
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        pos_x = (w - text_w) / 2
        draw.text((pos_x, curr_y), line, font=font, fill='#FFD700', stroke_width=5, stroke_fill='black')
        curr_y += line_height

    # TEXTE SUIVANT (PETIT BLANC)
    if next_text:
        font_size_next = int(h * 0.04)
        try:
            font_next = ImageFont.truetype("karaoke_font.ttf", font_size_next)
        except:
            font_next = ImageFont.load_default()
        
        next_lines = textwrap.wrap(f"... {next_text} ...", width=40)
        next_y = curr_y + (h * 0.05)
        for line in next_lines:
            bbox = draw.textbbox((0, 0), line, font=font_next)
            text_w = bbox[2] - bbox[0]
            pos_x = (w - text_w) / 2
            draw.text((pos_x, next_y), line, font=font_next, fill='#E0E0E0', stroke_width=2, stroke_fill='black')
            next_y += (font_size_next * 1.2)
            
    return np.array(img)

# --- INTERFACE ---
st.title("🎤 KARAKODOUIN V13 - SRT")
st.write("Importez votre fichier .SRT pour une synchro parfaite.")
download_font()

# 1. FICHIERS MÉDIAS
col1, col2 = st.columns(2)
with col1:
    audio = st.file_uploader("1. Musique (MP3)", type=["mp3"])
with col2:
    bg = st.file_uploader("2. Fond (Img/Vidéo)", type=["jpg", "png", "mp4"])

# 2. FICHIER SRT
srt_file = st.file_uploader("3. Fichier Sous-titres (.srt)", type=["srt"])

# 3. BOUTON
if st.button("Lancer la Production 🎬") and audio and bg and srt_file:
    st.info("Lecture du fichier SRT...")
    
    # Fichiers Temp
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        f.write(audio.read())
        audio_path = f.name
        
    is_video = bg.name.lower().endswith(".mp4")
    ext = ".mp4" if is_video else ".png"
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as f:
        f.write(bg.read())
        bg_path = f.name
        
    try:
        # Lecture du contenu SRT
        srt_content = srt_file.read().decode("utf-8", errors="ignore")
        segments = parse_srt(srt_content)
        
        if not segments:
            st.error("Impossible de lire le fichier SRT. Vérifiez le format.")
        else:
            st.success(f"✅ {len(segments)} phrases détectées.")
            
            # Montage Vidéo
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
            
            bg_c = bg_c.resize(height=720)
            if bg_c.w % 2 != 0: bg_c = bg_c.resize(width=bg_c.w-1)
            
            subs = []
            bar = st.progress(0)
            total = len(segments)
            
            for i in range(total):
                seg = segments[i]
                
                # Prédiction suivante
                nxt = ""
                if i + 1 < total: nxt = segments[i+1]['text']
                
                img = create_karaoke_frame(seg['text'], nxt, bg_c.w, bg_c.h)
                clip = (ImageClip(img)
                        .set_start(seg['start'])
                        .set_end(seg['end'])
                        .set_position('center'))
                subs.append(clip)
                
                bar.progress((i + 1) / total)
                
            final = CompositeVideoClip([bg_c] + subs).set_audio(audio_c)
            out = "karaoke_srt.mp4"
            final.write_videofile(out, fps=24, codec="libx264", audio_codec="aac", preset="ultrafast")
            
            st.balloons()
            with open(out, "rb") as f:
                st.download_button("💾 TÉLÉCHARGER LE KARAOKÉ", f, file_name="karaoke_final.mp4")

    except Exception as e:
        st.error(f"Erreur : {e}")
