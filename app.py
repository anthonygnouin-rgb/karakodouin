import streamlit as st
import whisper
import tempfile
import os
import requests
import numpy as np
import textwrap
import pandas as pd
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont

# --- CONFIGURATION ---
st.set_page_config(page_title="Karaoké V6 - Édition", layout="centered")

# --- INITIALISATION SESSION STATE (Mémoire) ---
if 'segments_data' not in st.session_state:
    st.session_state['segments_data'] = []
if 'audio_path' not in st.session_state:
    st.session_state['audio_path'] = None
if 'bg_path' not in st.session_state:
    st.session_state['bg_path'] = None
if 'is_video_bg' not in st.session_state:
    st.session_state['is_video_bg'] = False

# --- FONCTIONS ---
def download_font():
    url = "https://github.com/google/fonts/raw/main/ofl/anton/Anton-Regular.ttf"
    if not os.path.exists("karaoke_font.ttf"):
        try:
            r = requests.get(url)
            with open("karaoke_font.ttf", 'wb') as f: f.write(r.content)
        except: pass 

def create_karaoke_frame(current_text, next_text, w, h):
    img = Image.new('RGBA', (w, h), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # 1. Texte Principal (10% hauteur)
    font_size = int(h * 0.10)
    try:
        font = ImageFont.truetype("karaoke_font.ttf", font_size)
    except:
        font = ImageFont.load_default()

    lines = textwrap.wrap(str(current_text), width=20)
    line_height = font_size * 1.2
    total_height = len(lines) * line_height
    start_y = (h - total_height) / 2 - (h * 0.05)
    
    curr_y = start_y
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        pos_x = (w - text_w) / 2
        draw.text((pos_x, curr_y), line, font=font, fill='#FFD700', stroke_width=5, stroke_fill='black')
        curr_y += line_height

    # 2. Texte Suivant (4% hauteur)
    if next_text and str(next_text).strip() != "":
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
st.title("🎤 KARAKODOUIN V6 - Mode Manuel")
download_font()

# ÉTAPE 1 : UPLOAD
st.write("### 1. Fichiers")
audio = st.file_uploader("Musique (MP3)", type=["mp3"], key="u_audio")
bg = st.file_uploader("Fond (Image/Vidéo)", type=["jpg", "png", "mp4"], key="u_bg")

# ÉTAPE 2 : ANALYSE DU RYTHME
if st.button("1. Analyser le rythme 🎵") and audio and bg:
    st.info("L'IA détecte le timing des phrases...")
    
    # Sauvegarde Fichiers
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f1:
        f1.write(audio.read())
        st.session_state['audio_path'] = f1.name
        
    is_video = bg.name.lower().endswith(".mp4")
    st.session_state['is_video_bg'] = is_video
    ext = ".mp4" if is_video else ".png"
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as f2:
        f2.write(bg.read())
        st.session_state['bg_path'] = f2.name

    # Whisper pour le timing
    model = whisper.load_model("base")
    result = model.transcribe(st.session_state['audio_path'])
    
    # On prépare les données pour le tableau
    data = []
    for s in result["segments"]:
        data.append({
            "Début (s)": round(s["start"], 2),
            "Fin (s)": round(s["end"], 2),
            "Paroles (Modifiable)": s["text"].strip()
        })
    st.session_state['segments_data'] = data
    st.experimental_rerun()

# ÉTAPE 3 : ÉDITION DES PAROLES
if len(st.session_state['segments_data']) > 0:
    st.write("---")
    st.write("### 2. Vos Paroles")
    st.info("Voici ce que l'IA a entendu. **Cliquez dans la colonne 'Paroles' pour corriger ou coller votre texte.**")
    
    # Création du tableau éditable
    df = pd.DataFrame(st.session_state['segments_data'])
    edited_df = st.data_editor(
        df, 
        num_rows="dynamic", 
        use_container_width=True,
        height=400,
        key="editor"
    )

    # ÉTAPE 4 : GÉNÉRATION
    st.write("---")
    if st.button("2. Créer la Vidéo Finale 🎬"):
        st.info("Assemblage de la vidéo avec VOS paroles...")
        
        try:
            audio_path = st.session_state['audio_path']
            bg_path = st.session_state['bg_path']
            
            # Préparation Clips
            audio_c = AudioFileClip(audio_path)
            if st.session_state['is_video_bg']:
                bg_c = VideoFileClip(bg_path)
                if bg_c.duration < audio_c.duration:
                    bg_c = bg_c.loop(duration=audio_c.duration)
                else:
                    bg_c = bg_c.subclip(0, audio_c.duration)
                bg_c = bg_c.set_audio(None)
            else:
                bg_c = ImageClip(bg_path).set_duration(audio_c.duration)

            # Redimensionnement 720p
            bg_c = bg_c.resize(height=720)
            if bg_c.w % 2 != 0: bg_c = bg_c.resize(width=bg_c.w-1)

            subs = []
            
            # On récupère les données du tableau modifié par l'utilisateur
            # Convertit le DataFrame en liste de dictionnaires
            final_segments = edited_df.to_dict('records')
            total = len(final_segments)
            bar = st.progress(0)
            
            for i in range(total):
                row = final_segments[i]
                txt_now = row["Paroles (Modifiable)"]
                start = row["Début (s)"]
                end = row["Fin (s)"]
                
                # Prédiction phrase suivante
                txt_next = ""
                if i + 1 < total:
                    txt_next = final_segments[i+1]["Paroles (Modifiable)"]
                
                if txt_now and str(txt_now).strip():
                    img = create_karaoke_frame(txt_now, txt_next, bg_c.w, bg_c.h)
                    clip = (ImageClip(img)
                            .set_start(start)
                            .set_end(end)
                            .set_position('center'))
                    subs.append(clip)
                
                bar.progress((i + 1) / total)

            final = CompositeVideoClip([bg_c] + subs).set_audio(audio_c)
            out = "karaoke_final_user.mp4"
            final.write_videofile(out, fps=24, codec="libx264", audio_codec="aac", preset="ultrafast")
            
            st.balloons()
            st.success("✅ Vidéo prête avec VOS paroles !")
            with open(out, "rb") as f:
                st.download_button("Télécharger", f, file_name="mon_karaoke.mp4")

        except Exception as e:
            st.error(f"Erreur : {e}")
            
