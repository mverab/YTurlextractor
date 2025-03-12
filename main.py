from googleapiclient.discovery import build
import csv
import os
import time
import json
import sys
import argparse
from datetime import datetime
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Obtener variables de entorno
API_KEY = os.getenv('YOUTUBE_API_KEY')
DEFAULT_CHANNEL_ID = os.getenv('DEFAULT_CHANNEL_ID')
DEFAULT_OUTPUT_DIR = os.getenv('DEFAULT_OUTPUT_DIR', 'transcripciones')
DEFAULT_VIDEO_LIMIT = int(os.getenv('DEFAULT_VIDEO_LIMIT', 0))

# Verificar que la clave API esté configurada
if not API_KEY:
    print("Error: No se ha configurado la clave API de YouTube.")
    print("Por favor, crea un archivo .env con la variable YOUTUBE_API_KEY.")
    sys.exit(1)

# Construir el objeto de servicio de YouTube
youtube = build('youtube', 'v3', developerKey=API_KEY)

def get_video_id_from_url(url):
    """Extrae el ID del video de una URL de YouTube."""
    if "youtube.com/watch?v=" in url:
        return url.split("watch?v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    else:
        return url  # Asumimos que ya es un ID

def get_channel_info(channel_id):
    """Obtiene información básica del canal."""
    try:
        channel_response = youtube.channels().list(
            part='snippet,statistics,contentDetails',
            id=channel_id
        ).execute()
        
        if not channel_response.get('items'):
            print(f"No se encontró el canal con ID: {channel_id}")
            return None
        
        channel_info = channel_response['items'][0]
        return {
            'id': channel_id,
            'title': channel_info['snippet']['title'],
            'description': channel_info['snippet'].get('description', ''),
            'published_at': channel_info['snippet']['publishedAt'],
            'video_count': channel_info['statistics'].get('videoCount', 0),
            'subscriber_count': channel_info['statistics'].get('subscriberCount', 0),
            'view_count': channel_info['statistics'].get('viewCount', 0),
            'uploads_playlist_id': channel_info['contentDetails']['relatedPlaylists']['uploads']
        }
    except Exception as e:
        print(f"Error al obtener información del canal: {e}")
        return None

def get_channel_videos(channel_id):
    """Obtiene todos los videos de un canal de YouTube."""
    print(f"Obteniendo videos para el canal ID: {channel_id}")
    
    # Obtener información del canal
    channel_info = get_channel_info(channel_id)
    if not channel_info:
        return []
    
    print(f"Nombre del canal: {channel_info['title']}")
    print(f"Total de videos en el canal: {channel_info['video_count']}")
    uploads_playlist_id = channel_info['uploads_playlist_id']

    videos = []
    next_page_token = None
    total_videos = 0

    # Recuperar videos de la lista de reproducción de subidas
    while True:
        try:
        playlist_response = youtube.playlistItems().list(
            playlistId=uploads_playlist_id,
                part='snippet,contentDetails',
                maxResults=50,  # Máximo permitido por solicitud
            pageToken=next_page_token
        ).execute()

        for item in playlist_response.get('items', []):
                video_id = item['contentDetails']['videoId']
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            video_title = item['snippet']['title']
            video_published_at = item['snippet']['publishedAt']
            videos.append({
                    'id': video_id,
                'url': video_url,
                'title': video_title,
                    'published_at': video_published_at,
                    'channel_title': channel_info['title'],
                    'channel_id': channel_id
            })
                total_videos += 1
        
            print(f"Obtenidos {total_videos} videos hasta ahora...")
        next_page_token = playlist_response.get('nextPageToken')
        if not next_page_token:
            break

            # Pequeña pausa para evitar límites de la API
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Error al obtener videos: {e}")
            break

    print(f"Total de videos encontrados: {len(videos)}")
    return videos

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
    
    except NoTranscriptFound:
        print(f"No se encontró transcripción para el video {video_id}")
        return {
            'success': False,
            'error': "No se encontró ninguna transcripción."
        }
    except TranscriptsDisabled:
        print(f"Las transcripciones están deshabilitadas para el video {video_id}")
        return {
            'success': False,
            'error': "Las transcripciones están deshabilitadas para este video."
        }
    except Exception as e:
        print(f"Error al obtener transcripciones: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def save_transcript_to_file(video_info, transcript_info, output_dir):
    """Guarda la transcripción en un archivo de texto."""
    if not transcript_info['success']:
        print(f"No se pudo guardar la transcripción: {transcript_info.get('error', 'Error desconocido')}")
        return False
    
    # Crear un nombre de archivo seguro basado en el título del video
    safe_title = "".join([c if c.isalnum() or c in [' ', '-', '_'] else '_' for c in video_info['title']])
    safe_title = safe_title[:100]  # Limitar la longitud del título
    
    output_file = os.path.join(output_dir, f"{video_info['id']}_{safe_title}.txt")
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Título: {video_info['title']}\n")
            f.write(f"URL: {video_info['url']}\n")
            f.write(f"Canal: {video_info['channel_title']}\n")
            f.write(f"ID del Canal: {video_info.get('channel_id', '')}\n")
            f.write(f"Fecha de publicación: {video_info['published_at']}\n")
            f.write(f"Idioma: {transcript_info['language']}\n")
            f.write(f"Generada automáticamente: {'Sí' if transcript_info['is_generated'] else 'No'}\n")
            f.write("\n--- TRANSCRIPCIÓN ---\n\n")
            f.write(transcript_info['transcript_text'])
        
        print(f"Transcripción guardada en: {output_file}")
        return True
    except Exception as e:
        print(f"Error al guardar la transcripción: {e}")
        return False

def save_videos_to_csv(videos, filename):
    """Guarda los videos y sus transcripciones en un archivo CSV."""
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['ID', 'URL', 'Título', 'Canal', 'ID del Canal', 'Fecha de Publicación', 'Idioma', 'Generada Automáticamente', 'Éxito', 'Error'])
        
        for video in videos:
            writer.writerow([
                video['id'],
                video['url'], 
                video['title'], 
                video['channel_title'],
                video.get('channel_id', ''),
                video['published_at'], 
                video.get('transcript_language', ''),
                video.get('transcript_is_generated', ''),
                video.get('transcript_success', False),
                video.get('transcript_error', '')
            ])

def save_channel_info_to_file(channel_info, output_dir):
    """Guarda la información del canal en un archivo JSON."""
    if not channel_info:
        return False
    
    channel_file = os.path.join(output_dir, f"canal_{channel_info['id']}_info.json")
    
    try:
        with open(channel_file, 'w', encoding='utf-8') as f:
            json.dump(channel_info, f, ensure_ascii=False, indent=2)
        
        print(f"Información del canal guardada en: {channel_file}")
        return True
    except Exception as e:
        print(f"Error al guardar la información del canal: {e}")
        return False

def save_progress(videos, processed_count, output_dir, channel_id):
    """Guarda el progreso actual para poder reanudar más tarde."""
    progress_file = os.path.join(output_dir, f"progreso_{channel_id}.json")
    
    # Solo guardar los videos que aún no se han procesado
    remaining_videos = videos[processed_count:]
    
    # Convertir a un formato serializable
    serializable_videos = []
    for video in remaining_videos:
        video_copy = video.copy()
        # Eliminar datos de transcripción que no son serializables
        if 'transcript_data' in video_copy:
            del video_copy['transcript_data']
        serializable_videos.append(video_copy)
    
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump({
            'channel_id': channel_id,
            'processed_count': processed_count,
            'remaining_videos': serializable_videos,
            'timestamp': datetime.now().isoformat()
        }, f, ensure_ascii=False, indent=2)
    
    print(f"Progreso guardado en {progress_file}. Puedes reanudar más tarde.")

def load_progress(output_dir, channel_id):
    """Carga el progreso guardado anteriormente."""
    progress_file = os.path.join(output_dir, f"progreso_{channel_id}.json")
    
    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
                if progress_data.get('channel_id') == channel_id:
                    return progress_data.get('processed_count', 0), progress_data.get('remaining_videos', [])
                else:
                    print(f"El archivo de progreso es para otro canal ({progress_data.get('channel_id')}). Ignorando.")
        except Exception as e:
            print(f"Error al cargar el progreso: {e}")
    
    return 0, []

def process_single_video(video_url, output_dir):
    """Procesa un solo video y guarda su transcripción."""
    video_id = get_video_id_from_url(video_url)
    
    # Obtener información del video
    try:
        video_response = youtube.videos().list(
            part='snippet',
            id=video_id
        ).execute()
        
        if not video_response.get('items'):
            print(f"No se encontró el video con ID: {video_id}")
            return False
        
        video_info = {
            'id': video_id,
            'url': video_url,
            'title': video_response['items'][0]['snippet']['title'],
            'channel_title': video_response['items'][0]['snippet']['channelTitle'],
            'channel_id': video_response['items'][0]['snippet']['channelId'],
            'published_at': video_response['items'][0]['snippet']['publishedAt']
        }
        
        # Obtener la transcripción
        transcript_info = get_transcript(video_id)
        
        if transcript_info['success']:
            # Crear directorio para las transcripciones si no existe
            text_output_dir = os.path.join(output_dir, "texto")
            os.makedirs(text_output_dir, exist_ok=True)
            
            # Guardar la transcripción
            save_transcript_to_file(video_info, transcript_info, text_output_dir)
            
            # Mostrar una vista previa
            print("\n--- VISTA PREVIA DE LA TRANSCRIPCIÓN ---")
            preview_lines = transcript_info['transcript_text'].split('\n')[:10]
            print('\n'.join(preview_lines))
            if len(preview_lines) < 10:
                print("(Transcripción completa)")
            else:
                print("...")
            
            return True
        else:
            print(f"No se pudo obtener la transcripción: {transcript_info.get('error', 'Error desconocido')}")
            return False
    
    except Exception as e:
        print(f"Error al procesar el video: {e}")
        return False

def process_channel(channel_id, output_dir, limit=None, force_refresh=False):
    """Procesa todos los videos de un canal."""
    # Crear directorios para los resultados
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    text_output_dir = os.path.join(output_dir, "texto")
    if not os.path.exists(text_output_dir):
        os.makedirs(text_output_dir)
    
    # Obtener información del canal y guardarla
    channel_info = get_channel_info(channel_id)
    if not channel_info:
        print(f"No se pudo obtener información del canal {channel_id}. Abortando.")
        return False
    
    save_channel_info_to_file(channel_info, output_dir)
    
    # Verificar si hay un progreso guardado
    processed_count, remaining_videos = load_progress(output_dir, channel_id)
    
    # Si hay videos restantes y no se fuerza el refresco, preguntar si se quiere reanudar
    if remaining_videos and not force_refresh:
        print(f"Se encontró un progreso guardado con {len(remaining_videos)} videos pendientes.")
        resume = input("¿Deseas reanudar el procesamiento anterior? (s/n): ").lower()
        
        if resume == 's':
            videos = remaining_videos
            print(f"Reanudando procesamiento desde el video {processed_count + 1}...")
        else:
            # Obtener todos los videos del canal
            videos = get_channel_videos(channel_id)
            processed_count = 0
    else:
        # Obtener todos los videos del canal
        videos = get_channel_videos(channel_id)
        processed_count = 0
    
    # Limitar el número de videos si se especifica
    if limit and limit > 0:
        videos = videos[:limit]
        print(f"Limitando el procesamiento a {limit} videos.")
    
    # Procesar cada video para obtener su transcripción
    total_videos = len(videos)
    videos_with_transcripts = 0
    
    try:
        for i, video in enumerate(videos):
            print(f"\nProcesando video {processed_count + i + 1}/{processed_count + total_videos}: {video['title']}")
            
            # Verificar si el archivo de texto ya existe
            safe_title = "".join([c if c.isalnum() or c in [' ', '-', '_'] else '_' for c in video['title']])
            safe_title = safe_title[:100]
            
            transcript_file = os.path.join(text_output_dir, f"{video['id']}_{safe_title}.txt")
            
            if os.path.exists(transcript_file) and not force_refresh:
                print(f"La transcripción ya existe para este video. Omitiendo...")
                video['transcript_success'] = True
                video['transcript_language'] = "already_processed"
                video['transcript_is_generated'] = "unknown"
                videos_with_transcripts += 1
                continue
            
            # Obtener la transcripción
            transcript_info = get_transcript(video['id'])
            
            # Guardar información de la transcripción en el objeto de video
            video['transcript_success'] = transcript_info['success']
            
            if transcript_info['success']:
                video['transcript_language'] = transcript_info['language']
                video['transcript_is_generated'] = transcript_info['is_generated']
                videos_with_transcripts += 1
                
                # Guardar la transcripción como archivo de texto
                save_transcript_to_file(video, transcript_info, text_output_dir)
            else:
                video['transcript_error'] = transcript_info.get('error', 'Error desconocido')
            
            # Guardar progreso cada 10 videos
            if (i + 1) % 10 == 0:
                save_progress(videos, processed_count + i + 1, output_dir, channel_id)
            
            # Pequeña pausa para evitar límites de la API
            time.sleep(0.2)
    
    except KeyboardInterrupt:
        print("\nProcesamiento interrumpido por el usuario.")
        save_progress(videos, processed_count + i, output_dir, channel_id)
        print("Progreso guardado. Puedes reanudar más tarde.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError durante el procesamiento: {e}")
        save_progress(videos, processed_count + i, output_dir, channel_id)
        print("Progreso guardado debido a un error. Puedes reanudar más tarde.")
        raise
    
    # Guardar resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = os.path.join(output_dir, f"videos_transcripciones_{channel_id}_{timestamp}.csv")
    save_videos_to_csv(videos, csv_filename)
    
    # Eliminar el archivo de progreso si se completó todo
    progress_file = os.path.join(output_dir, f"progreso_{channel_id}.json")
    if os.path.exists(progress_file):
        os.remove(progress_file)
    
    print(f"\n--- RESUMEN ---")
    print(f"Canal: {channel_info['title']} (ID: {channel_id})")
    print(f"Total de videos procesados: {processed_count + total_videos}")
    print(f"Videos con transcripciones: {videos_with_transcripts}")
    print(f"Videos sin transcripciones: {processed_count + total_videos - videos_with_transcripts}")
    print(f"Resultados guardados en CSV: {csv_filename}")
    print(f"Transcripciones de texto guardadas en: {text_output_dir}")
    
    return True

def parse_arguments():
    """Analiza los argumentos de la línea de comandos."""
    parser = argparse.ArgumentParser(description='Extractor de transcripciones de YouTube')
    
    # Argumentos generales
    parser.add_argument('--output', '-o', type=str, default=DEFAULT_OUTPUT_DIR,
                        help='Directorio de salida para las transcripciones')
    
    # Subparsers para diferentes modos
    subparsers = parser.add_subparsers(dest='mode', help='Modo de operación')
    
    # Modo de video único
    video_parser = subparsers.add_parser('video', help='Procesar un solo video')
    video_parser.add_argument('video_url', type=str, help='URL o ID del video de YouTube')
    
    # Modo de canal
    channel_parser = subparsers.add_parser('channel', help='Procesar todos los videos de un canal')
    channel_parser.add_argument('channel_id', type=str, nargs='?', default=DEFAULT_CHANNEL_ID,
                               help=f'ID del canal de YouTube (por defecto: {DEFAULT_CHANNEL_ID})')
    channel_parser.add_argument('--limit', '-l', type=int, default=DEFAULT_VIDEO_LIMIT,
                               help=f'Limitar el número de videos a procesar (0 = sin límite, por defecto: {DEFAULT_VIDEO_LIMIT})')
    channel_parser.add_argument('--force', '-f', action='store_true',
                               help='Forzar el reprocesamiento de videos ya procesados')
    
    args = parser.parse_args()
    
    # Si no se especifica un modo, usar el modo de canal con el ID por defecto
    if not args.mode:
        args.mode = 'channel'
        args.channel_id = DEFAULT_CHANNEL_ID
        args.limit = DEFAULT_VIDEO_LIMIT
        args.force = False
    
    return args

def main():
    """Función principal del script."""
    # Analizar argumentos
    args = parse_arguments()
    
    # Crear directorio de salida
    output_dir = args.output
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Procesar según el modo
    if args.mode == 'video':
        print(f"Procesando un solo video: {args.video_url}")
        process_single_video(args.video_url, output_dir)
    elif args.mode == 'channel':
        print(f"Procesando canal: {args.channel_id}")
        process_channel(args.channel_id, output_dir, args.limit, args.force)
    else:
        print(f"Modo no reconocido: {args.mode}")
        return False
    
    return True

if __name__ == "__main__":
    main()
