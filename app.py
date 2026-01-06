import flet as ft
import karaoke_engine # On appelle ton fichier moteur
import os

def main(page: ft.Page):
    page.title = "Karaoké IA Pro"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 400
    page.window_height = 800
    page.scroll = "auto"

    # --- Variables ---
    current_lyrics = [] 
    
    # --- Interface ---
    titre = ft.Text("Karaoké Generator", size=30, weight="bold", color="blue")
    
    # Le texte des paroles (qui changera)
    lyrics_display = ft.Text(
        value="♫ En attente ♫", 
        size=28, 
        weight="bold",
        text_align="center", 
        color=ft.colors.WHITE
    )
    
    # Sous-titre pour voir la suite (optionnel)
    next_line_display = ft.Text(value="", size=16, color=ft.colors.GREY_500, text_align="center")

    # --- Logique de Synchro ---
    def on_position_changed(e):
        # Cette fonction tourne en boucle pendant la lecture
        position_ms = int(e.data)
        
        found_line = False
        for i, ligne in enumerate(current_lyrics):
            # Si le temps actuel est dans le créneau de la ligne
            if ligne['start'] <= position_ms <= ligne['end']:
                if lyrics_display.value != ligne['text']:
                    lyrics_display.value = ligne['text']
                    # On essaie d'afficher la ligne suivante en petit
                    if i + 1 < len(current_lyrics):
                        next_line_display.value = current_lyrics[i+1]['text']
                    else:
                        next_line_display.value = ""
                    page.update()
                found_line = True
                break
        
        # Si on est entre deux phrases (silence)
        if not found_line and current_lyrics:
             # Optionnel : laisser la dernière phrase ou effacer
             pass

    # Lecteur Audio
    player = ft.Audio(
        src="", 
        autoplay=False,
        on_position_changed=on_position_changed
    )
    page.overlay.append(player)

    # --- Gestion Fichier ---
    def file_picked(e: ft.FilePickerResultEvent):
        if e.files:
            file_path = e.files[0].path
            loading_text.value = "⏳ L'IA écoute votre musique... (Patientez)"
            upload_btn.disabled = True
            page.update()

            try:
                # Appel au cerveau (moteur_karaoke.py)
                audio_path, sync_data = moteur_karaoké.process_song(file_path)
                
                global current_lyrics
                current_lyrics = sync_data
                
                player.src = audio_path
                loading_text.value = "✅ Analyse terminée !"
                play_btn.disabled = False
                upload_btn.disabled = False
                
            except Exception as ex:
                loading_text.value = f"Erreur : {ex}"
                upload_btn.disabled = False
            
            page.update()

    file_picker = ft.FilePicker(on_result=file_picked)
    page.overlay.append(file_picker)

    upload_btn = ft.ElevatedButton("Choisir un MP3", on_click=lambda _: file_picker.pick_files(), icon=ft.icons.UPLOAD)
    play_btn = ft.ElevatedButton("Lecture ▶", on_click=lambda _: player.play(), disabled=True)
    loading_text = ft.Text("", color="green")

    # --- Assemblage ---
    page.add(
        ft.Column([
            titre,
            ft.Divider(),
            upload_btn,
            loading_text,
            ft.Divider(),
            play_btn,
            ft.Container(height=50), # Espace
            lyrics_display,
            ft.Container(height=20),
            next_line_display
        ], alignment="center", horizontal_alignment="center")
    )

ft.app(target=main)
                
