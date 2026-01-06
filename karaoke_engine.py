import whisper
import os

# On charge le modèle une seule fois pour gagner du temps
# "base" est un bon compromis rapidité/précision. Tu peux mettre "small" ou "medium" si tu as un PC puissant.
model = whisper.load_model("base")

def process_song(file_path):
    """
    Prend un fichier audio, lance l'IA et retourne :
    1. Le chemin du fichier
    2. La liste des segments synchronisés
    """
    print(f"Analyse de {file_path} en cours...")
    
    # L'IA transcrit et synchronise
    result = model.transcribe(file_path, fp16=False) # fp16=False pour éviter les erreurs CPU
    
    # On reformate les données pour notre application Flet
    # On veut une liste de dictionnaires : {'text': "Paroles", 'start': ms, 'end': ms}
    synchro_data = []
    
    for segment in result['segments']:
        synchro_data.append({
            "text": segment['text'].strip(),
            "start": int(segment['start'] * 1000), # Convertir secondes en millisecondes
            "end": int(segment['end'] * 1000)
        })
        
    return file_path, synchro_data
    
