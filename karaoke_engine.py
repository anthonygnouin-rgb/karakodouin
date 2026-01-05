import moviepy.editor as mp
from moviepy.video.tools.subtitles import SubtitlesClip
import pysrt
import numpy as np
import textwrap

# --- FONCTION UTILITAIRE ---
def time_to_seconds(t):
    return t.hours * 3600 + t.minutes * 60 + t.seconds + t.milliseconds / 1000.0

# --- MOTEUR VIDÉO ---
def create_karaoke_video(audio_path, background_path, srt_path, output_filename="karaoke_final.mp4"):
    
    # 1. SETUP DE BASE
    audio = mp.AudioFileClip(audio_path)
    subs = pysrt.open(srt_path)
    w, h = 1920, 1080  # Full HD Paysage
    
    # Gestion du fond (Vidéo ou Image)
    if background_path.lower().endswith(('.mp4', '.mov', '.avi')):
        bg_clip = mp.VideoFileClip(background_path)
        bg_clip = mp.vfx.loop(bg_clip, duration=audio.duration)
        bg_clip = bg_clip.resize(newsize=(w, h))
    else:
        bg_clip = mp.ImageClip(background_path).set_duration(audio.duration)
        bg_clip = bg_clip.resize(newsize=(w, h))

    # 2. GÉNÉRATION DES CLIPS TEXTE
    clips_to_overlay = []
    
    # Style
    font_main = 'Impact'  # Police forte et lisible
    fontsize_main = 70
    fontsize_future = 45
    color_active = '#D4AF37' # Or Viking
    color_inactive = 'white'
    stroke_color = 'black'
    stroke_width = 3
    
    # On parcourt par bloc de 2 lignes
    for i in range(0, len(subs), 2):
        # -- RECUPERATION DES LIGNES --
        current_lines = [subs[i]]
        if i+1 < len(subs): current_lines.append(subs[i+1])
        
        future_lines = []
        if i+2 < len(subs): future_lines.append(subs[i+2])
        if i+3 < len(subs): future_lines.append(subs[i+3])
        
        # Temps du bloc (début de la 1ère ligne à fin de la dernière ligne du bloc)
        t_start_block = time_to_seconds(current_lines[0].start)
        t_end_block = time_to_seconds(current_lines[-1].end) if len(current_lines) > 1 else time_to_seconds(current_lines[0].end)
        
        # Marge de sécurité pour l'affichage (commence un peu avant, finit un peu après)
        display_start = max(0, t_start_block - 0.5)
        display_end = t_end_block + 0.5
        
        # -- TRAITEMENT DES LIGNES ACTUELLES (ANIMEES) --
        for idx, line in enumerate(current_lines):
            t_start = time_to_seconds(line.start)
            t_end = time_to_seconds(line.end)
            duration = t_end - t_start
            
            y_pos = h/2 - 80 + (idx * 100) # Centré verticalement
            
            # 1. Texte Blanc (Base)
            txt_white = (mp.TextClip(line.text, font=font_main, fontsize=fontsize_main, color=color_inactive, 
                                     stroke_color=stroke_color, stroke_width=stroke_width, size=(w-100, None), method='caption')
                         .set_position(('center', y_pos))
                         .set_start(display_start)
                         .set_end(display_end))
            clips_to_overlay.append(txt_white)

            # 2. Texte Or (Remplissage) avec Masque de progression (Wipe)
            # On crée le texte Or complet
            txt_gold = (mp.TextClip(line.text, font=font_main, fontsize=fontsize_main, color=color_active, 
                                    stroke_color=stroke_color, stroke_width=stroke_width, size=(w-100, None), method='caption')
                         .set_position(('center', y_pos))
                         .set_start(t_start)
                         .set_end(display_end)) # Reste or après avoir été chanté
            
            # Création de l'effet "Wipe" (Masque qui grandit de gauche à droite)
            # Note: Pour éviter le crash sur mobile/cloud gratuit, on utilise un "cropping" simple ou un masque
            # Ici : méthode clipComposite (plus robuste que les masques complexes qui plantent imagemagick parfois)
            
            # On ajoute le clip Or
          
