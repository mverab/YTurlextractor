from youtube_transcript_api import YouTubeTranscriptApi
import sys
import os
from dotenv import load_dotenv
import argparse

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Obtener variables de entorno
DEFAULT_OUTPUT_DIR = os.getenv('DEFAULT_OUTPUT_DIR', 'transcripciones')

def get_video_id_from_url(url):
    """Extrae el ID del video de una URL de YouTube."""
    if "youtube.com/watch?v=" in url:
        return url.split("watch?v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    else:
        return url  # Asumimos que ya es un ID

def get_transcript(video_id_or_url):
    """Obtiene la transcripción de un video de YouTube en cualquier idioma disponible."""
    video_id = get_video_id_from_url(video_id_or_url)
    print(f"Obteniendo transcripción para el video ID: {video_id}")
    
    try:
        # Obtener la lista de transcripciones disponibles
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Intentar todas las transcripciones disponibles, empezando por las manuales
        for transcript in transcript_list:
            try:
                print(f"Intentando con transcripción en {transcript.language} (generada automáticamente: {transcript.is_generated})")
                transcript_data = transcript.fetch()
                
                # Convertir a texto plano
                transcript_text = ""
                for item in transcript_data:
                    # Acceder a los atributos correctamente
                    # Los objetos FetchedTranscriptSnippet tienen atributos text, start y duration
                    text = item.text if hasattr(item, 'text') else item['text'] if isinstance(item, dict) and 'text' in item else ""
                    start = item.start if hasattr(item, 'start') else item['start'] if isinstance(item, dict) and 'start' in item else 0
                    
                    # Formato: [HH:MM:SS] Texto
                    seconds = start
                    hours, remainder = divmod(seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    time_str = f"[{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}]"
                    transcript_text += f"{time_str} {text}\n"
                
                return {
                    'success': True,
                    'language': transcript.language,
                    'is_generated': transcript.is_generated,
                    'transcript_data': transcript_data,
                    'transcript_text': transcript_text
                }
            except Exception as e:
                print(f"Error al obtener transcripción en {transcript.language}: {e}")
                continue
        
        # Si llegamos aquí, no se encontró ninguna transcripción utilizable
        print("No se encontró ninguna transcripción para este video.")
        return {
            'success': False,
            'error': "No se encontró ninguna transcripción utilizable."
        }
    
    except Exception as e:
        print(f"Error al obtener transcripciones: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def save_transcript_to_file(transcript_info, output_file=None):
    """Guarda la transcripción en un archivo de texto."""
    if not transcript_info['success']:
        print(f"No se pudo guardar la transcripción: {transcript_info.get('error', 'Error desconocido')}")
        return False
    
    if output_file is None:
        output_file = f"transcripcion_{transcript_info.get('language', 'desconocido')}.txt"
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Idioma: {transcript_info['language']}\n")
            f.write(f"Generada automáticamente: {'Sí' if transcript_info['is_generated'] else 'No'}\n\n")
            f.write(transcript_info['transcript_text'])
        
        print(f"Transcripción guardada en: {output_file}")
        return True
    except Exception as e:
        print(f"Error al guardar la transcripción: {e}")
        return False

def main():
    # Configurar el parser de argumentos
    parser = argparse.ArgumentParser(description='Extractor simple de transcripciones de YouTube')
    parser.add_argument('video_url', type=str, nargs='?', help='URL o ID del video de YouTube')
    parser.add_argument('--output', '-o', type=str, default=DEFAULT_OUTPUT_DIR,
                        help=f'Directorio de salida para las transcripciones (por defecto: {DEFAULT_OUTPUT_DIR})')
    args = parser.parse_args()
    
    # Verificar si se proporcionó una URL
    if args.video_url:
        video_url = args.video_url
    else:
        video_url = input("Introduce la URL del video de YouTube: ")
    
    # Obtener la transcripción
    transcript_info = get_transcript(video_url)
    
    if transcript_info['success']:
        print("\n--- INFORMACIÓN DE LA TRANSCRIPCIÓN ---")
        print(f"Idioma: {transcript_info['language']}")
        print(f"Generada automáticamente: {'Sí' if transcript_info['is_generated'] else 'No'}")
        print(f"Número de segmentos: {len(transcript_info['transcript_data'])}")
        
        # Crear directorio para las transcripciones si no existe
        os.makedirs(args.output, exist_ok=True)
        
        # Guardar la transcripción
        video_id = get_video_id_from_url(video_url)
        output_file = f"{args.output}/transcripcion_{video_id}_{transcript_info['language']}.txt"
        save_transcript_to_file(transcript_info, output_file)
        
        # Mostrar una vista previa
        print("\n--- VISTA PREVIA DE LA TRANSCRIPCIÓN ---")
        preview_lines = transcript_info['transcript_text'].split('\n')[:10]
        print('\n'.join(preview_lines))
        if len(preview_lines) < 10:
            print("(Transcripción completa)")
        else:
            print("...")
    else:
        print(f"No se pudo obtener la transcripción: {transcript_info.get('error', 'Error desconocido')}")

if __name__ == "__main__":
    main() 