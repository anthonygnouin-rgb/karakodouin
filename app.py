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
st.set_page_config(page_title="Karaoké V4.1 (30%)", layout="centered")

# --- 1. TÉLÉCHARGEMENT POLICE "ANTON" ---
def download_font():
    url = "https://github.com/google/fonts/raw/main/ofl/anton/Anton-Regular.ttf"
    if not os.path.exists("karaoke_font.ttf"):
        try:
            r = requests.get(url)
            with open("karaoke_font.ttf", 'wb') as f: f.write(r.content)
        except: 
            pass 

# --- 2. NETTOYAGE ---
def clean_text(text):
    try:
        return text.encode('latin-1', 'ignore').decode('latin-1').strip()
    except:
        return ""

# --- 3. DESSIN DU TEXTE (Version 30% ÉCRAN) ---
def create_karaoke_frame(text, w, h):
    img = Image.new('RGBA', (w, h), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # --- MODIFICATION DEMANDÉE : 30% de la hauteur ---
    fontsize = int(h * 0.30) 
    
    try:
        font = ImageFont.truetype("karaoke_font.ttf", fontsize)
    except:
        font = ImageFont.load_default()

    # Comme le texte est énorme, on coupe court (tous les 8 caractères environ)
    # Sinon "Bonjour tout le monde" sort de l'écran
    lines = textwrap.wrap(text, width=10)
    
    # Calcul de la hauteur du bloc
    line_height = fontsize * 1.1
    total_text_height = len(lines) * line_height
    
    current_y = (h - total_text_height) / 2
    
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        current_x = (w - text_w) / 2
        
        # Texte Jaune + Contour Noir très épais (8px) pour supporter la taille
        draw.text((current_x, current_y), line, font=font, fill='#FFD700', stroke_width=8, stroke_fill='black')
        
        current_y += line_height
        
    return np.array(img)

# --- INTERFACE ---
st.title("🎤 KARAKODOUIN V4.1 - XXL")
st.markdown("ℹ️ *Mode Ultra-Gros (30% de l'écran).*")

download_font()

audio = st.file_uploader("1. Musique (MP3)", type=["mp3"], key="mp3_xxl")
bg = st.file_uploader("2. Fond (Image/Vidéo)", type=["jpg", "png", "mp4"], key="bg_xxl")

if st.button("Lancer la Vidéo 🎬") and audio and bg:
    st.info("🚀 Analyse en cours...")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as
