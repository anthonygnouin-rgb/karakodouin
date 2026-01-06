import flet as ft
import os
import karaoke_engine  # C'est ici qu'on appelle ton nouveau fichier moteur

def main(page: ft.Page):
    # Configuration de la page (Mode sombre et mobile friendly)
    page.title = "Karaoké Pro IA"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = "auto"
    page.padding = 20
    
    # Pour le style mobile sur ton Z Fold / A35
    page.window_width = 400
    page.window_height = 800

    # --- Variables de stockage ---
    current_lyrics = [] 
    
    # --- Éléments de l'interface ---
    titre = ft.Text("🎤 Karaoké Studio", size=30, weight="bold", color=ft.colors.CYAN_400)
    
    # Zone de texte principale (La parole en cours)
    lyrics_display = ft.Text(
        value="Choisissez une musique...", 
        size=32, 
        weight="bold",
        text_align="center", 
        color=ft.colors.WHITE
    )
    
    # Zone de texte secondaire (La phrase suivante pour anticiper)
    next_lyrics_display = ft.Text(
        value="", 
        size=18, 
        text_align="center", 
        color=ft.colors.GREY_500
    )
    
    status_text = ft.Text("", text_align="center")

    # --- Moteur de Synchronisation (La boucle temps réel) ---
    def on_position_changed(e):
        if not current_lyrics:
            return
            
        # Position actuelle du lecteur en millisecondes
        position_ms = int(e.data)
        
        txt_now = ""
        txt_next = ""
        
        # On cherche la phrase qui correspond au timing
        for i, ligne in enumerate(current_lyrics):
            if ligne['start'] <= position_ms <= ligne['end']:
                txt_now = ligne['text']
                # On prépare la ligne d'après
                if i + 1 < len(current_lyrics):
                    txt_next = current_lyrics[i+1]['text']
                break
        
        # Mise à jour de l'écran uniquement si le texte change (optimisation)
        if lyrics_display.value != txt_now and txt_now != "":
            lyrics_display.value = txt_now
            next_lyrics_display.value = txt_next
            page.update()

    # --- Lecteur Audio (Invisible mais essentiel) ---
    player = ft.Audio(
        src="", 
        autoplay=False,
        on_position_changed=on_position_changed
    )
    page.overlay.append(player)

    # --- Gestion de l'importation de fichier ---
    def file_picked(e: ft.FilePickerResultEvent):
        if e.files:
            file_path = e.files[0].path
            
            # On affiche que ça charge
            status_text.value = "🤖 L'IA analyse votre chanson... (Patientez)"
            status_text.color = ft.colors.YELLOW
            upload_btn.disabled = True
            play_btn.disabled = True
            page.update()

            try:
                # C'EST ICI QUE LA MAGIE OPÈRE
                # On appelle la fonction process_song de ton fichier karaoke_engine.py
                audio_path, sync_data = karaoke_engine.process_song(file_path)
                
                # On sauvegarde les résultats
                global current_lyrics
                current_lyrics = sync_data
                
                # On charge le lecteur
                player.src = audio_path
                
                status_text.value = "✅ Analyse terminée ! Appuyez sur Lecture."
                status_text.color = ft.colors.GREEN
                play_btn.disabled = False
                
            except Exception as ex:
                status_text.value = f"Erreur : {str(ex)}"
                status_text.color = ft.colors.RED
            
            upload_btn.disabled = False
            page.update()

    # Le sélecteur de fichiers
    file_picker = ft.FilePicker(on_result=file_picked)
    page.overlay.append(file_picker)

    # --- Boutons ---
    upload_btn = ft.ElevatedButton(
        "Importer un MP3", 
        icon=ft.icons.UPLOAD_FILE, 
        on_click=lambda _: file_picker.pick_files(allow_multiple=False, allowed_extensions=["mp3", "wav"])
    )
    
    play_btn = ft.ElevatedButton(
        "Lecture ▶", 
        icon=ft.icons.PLAY_ARROW, 
        on_click=lambda _: player.play(), 
        disabled=True
    )
    
    # --- Assemblage de la page ---
    page.add(
        ft.Column(
            [
                titre,
                ft.Divider(height=20, color="transparent"),
                upload_btn,
                status_text,
                ft.Divider(),
                lyrics_display, # Le gros texte
                ft.Divider(height=10, color="transparent"),
                next_lyrics_display, # Le petit texte
                ft.Divider(),
                play_btn,
    
