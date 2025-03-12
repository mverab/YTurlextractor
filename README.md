# Extractor de Transcripciones de YouTube

Este script permite extraer las transcripciones de todos los videos de un canal de YouTube específico, incluyendo las transcripciones generadas automáticamente.

## Características

- Extrae todos los videos de un canal de YouTube
- Obtiene transcripciones manuales y generadas automáticamente
- Guarda las transcripciones en formato CSV para análisis
- Crea archivos de texto individuales para cada video con transcripción
- Manejo de errores robusto para asegurar que el proceso continúe incluso si algunos videos no tienen transcripciones
- Soporte para múltiples idiomas de transcripción
- Sistema de guardado de progreso para reanudar el procesamiento si se interrumpe
- Detección de transcripciones ya procesadas para evitar trabajo duplicado
- Manejo de interrupciones del usuario (Ctrl+C) guardando el progreso
- Validación mejorada de formatos de transcripción para evitar errores
- Capacidad para procesar un solo video proporcionando su URL como argumento
- Interfaz de línea de comandos con opciones avanzadas
- Guardado de información del canal en formato JSON
- Organización de archivos por canal para procesar múltiples canales
- **Nuevo**: Configuración mediante variables de entorno para mayor seguridad
- **Nuevo**: Archivo .env.example para facilitar la configuración

## Opciones de Uso

Este proyecto incluye dos scripts:

1. **main.py**: Script principal que puede procesar todos los videos de un canal o un solo video específico.
2. **simple_extractor.py**: Script simplificado para extraer la transcripción de un solo video, útil para pruebas rápidas.

## Configuración Inicial

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/tu-usuario/youtube-transcript-extractor.git
   cd youtube-transcript-extractor
   ```

2. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar variables de entorno**:
   - Copia el archivo `.env.example` a `.env`:
     ```bash
     cp .env.example .env
     ```
   - Edita el archivo `.env` con tu editor favorito y añade tu clave API de YouTube:
     ```
     YOUTUBE_API_KEY=tu_clave_api_aqui
     ```

## Variables de Entorno

El proyecto utiliza las siguientes variables de entorno que puedes configurar en el archivo `.env`:

| Variable | Descripción | Valor por defecto |
|----------|-------------|------------------|
| `YOUTUBE_API_KEY` | Clave API de YouTube (obligatoria) | - |
| `DEFAULT_CHANNEL_ID` | ID del canal por defecto | UCkzcPjx6bTuZRa5pzQXumug |
| `DEFAULT_OUTPUT_DIR` | Directorio de salida por defecto | transcripciones |
| `DEFAULT_VIDEO_LIMIT` | Límite de videos por defecto (0 = sin límite) | 0 |

## Manejo de Errores y Formatos de Transcripción

El script está diseñado para manejar diferentes situaciones que pueden ocurrir al extraer transcripciones:

1. **Videos sin transcripciones**: Algunos videos pueden no tener transcripciones disponibles. El script detecta estos casos y continúa con el siguiente video.

2. **Transcripciones en diferentes idiomas**: El script intenta obtener transcripciones en cualquier idioma disponible, sin limitarse a un idioma específico.

3. **Formatos de transcripción inconsistentes**: La API de YouTube puede devolver transcripciones en diferentes formatos. El script valida cada elemento de la transcripción antes de procesarlo para evitar errores.

4. **Interrupciones y errores**: Si el script se interrumpe (por error o manualmente con Ctrl+C), guarda automáticamente el progreso para que puedas reanudarlo más tarde sin perder el trabajo realizado.

## Requisitos

Para usar este script, necesitas:

1. Python 3.6 o superior
2. Las siguientes bibliotecas de Python:
   - `google-api-python-client`
   - `youtube-transcript-api`
   - `python-dotenv`

Puedes instalar las dependencias con:

```bash
pip install -r requirements.txt
```

## Configuración de la API de YouTube

1. Obtén una clave API de YouTube:
   - Ve a [Google Cloud Console](https://console.cloud.google.com/)
   - Crea un nuevo proyecto
   - Habilita la API de YouTube Data v3
   - Crea una clave API
   - Copia la clave API en el archivo `.env` (variable `YOUTUBE_API_KEY`)

2. Encuentra el ID del canal de YouTube:
   - Ve al canal de YouTube
   - El ID del canal suele estar en la URL (por ejemplo, `https://www.youtube.com/channel/UCkzcPjx6bTuZRa5pzQXumug`)
   - Puedes configurar el ID del canal por defecto en el archivo `.env` (variable `DEFAULT_CHANNEL_ID`) o proporcionarlo como argumento al ejecutar el script

## Uso

### Opciones de línea de comandos

El script principal (`main.py`) ahora soporta una interfaz de línea de comandos con varias opciones:

```
usage: main.py [-h] [--output OUTPUT] {video,channel} ...

Extractor de transcripciones de YouTube

positional arguments:
  {video,channel}       Modo de operación
    video               Procesar un solo video
    channel             Procesar todos los videos de un canal

optional arguments:
  -h, --help            show this help message and exit
  --output OUTPUT, -o OUTPUT
                        Directorio de salida para las transcripciones
```

### Procesar todos los videos de un canal

```bash
python main.py channel [ID_DEL_CANAL] [--limit NUMERO] [--force]
```

Opciones:
- `ID_DEL_CANAL`: ID del canal de YouTube (opcional, si no se proporciona se usa el valor por defecto)
- `--limit NUMERO`, `-l NUMERO`: Limitar el número de videos a procesar (0 = sin límite)
- `--force`, `-f`: Forzar el reprocesamiento de videos ya procesados

Ejemplos:
```bash
# Procesar todos los videos del canal por defecto
python main.py channel

# Procesar todos los videos de un canal específico
python main.py channel UCkzcPjx6bTuZRa5pzQXumug

# Procesar solo los primeros 10 videos de un canal
python main.py channel UCkzcPjx6bTuZRa5pzQXumug --limit 10

# Forzar el reprocesamiento de todos los videos, incluso si ya tienen transcripciones
python main.py channel UCkzcPjx6bTuZRa5pzQXumug --force

# Guardar las transcripciones en un directorio específico
python main.py --output mi_directorio channel UCkzcPjx6bTuZRa5pzQXumug
```

### Procesar un solo video

```bash
python main.py video "URL_DEL_VIDEO"
```

o

```bash
python simple_extractor.py "URL_DEL_VIDEO"
```

**IMPORTANTE**: Cuando uses una URL como argumento, debes ponerla entre comillas para evitar que los caracteres especiales (como ? y =) sean interpretados por el shell:

Por ejemplo, para procesar el video con ID `dQw4w9WgXcQ`:

```bash
python main.py video "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

### Reanudación del procesamiento

Si el script se interrumpe por cualquier motivo (error, interrupción manual con Ctrl+C, etc.), guardará automáticamente el progreso. La próxima vez que lo ejecutes, detectará este progreso guardado y te preguntará si deseas reanudarlo.

## Estructura de los resultados

### Organización de archivos

El script crea la siguiente estructura de directorios:

```
transcripciones/                  # Directorio principal (configurable con --output)
├── canal_CHANNEL_ID_info.json    # Información del canal en formato JSON
├── progreso_CHANNEL_ID.json      # Archivo de progreso (temporal)
├── videos_transcripciones_CHANNEL_ID_TIMESTAMP.csv  # Resultados en CSV
└── texto/                        # Directorio con las transcripciones en texto
    ├── VIDEO_ID_TITULO.txt       # Transcripción del primer video
    ├── VIDEO_ID_TITULO.txt       # Transcripción del segundo video
    └── ...                       # Más transcripciones
```

### Archivo CSV

El archivo CSV contiene las siguientes columnas:
- ID: ID del video de YouTube
- URL: URL completa del video
- Título: Título del video
- Canal: Nombre del canal
- ID del Canal: ID del canal de YouTube
- Fecha de Publicación: Fecha y hora de publicación
- Idioma: Idioma de la transcripción obtenida
- Generada Automáticamente: Si la transcripción fue generada automáticamente
- Éxito: Si se pudo obtener la transcripción
- Error: Mensaje de error si no se pudo obtener la transcripción

### Archivos de texto

Cada archivo de texto contiene:
- Metadatos del video (título, URL, canal, ID del canal, fecha de publicación, idioma)
- Información sobre si la transcripción fue generada automáticamente
- La transcripción completa en formato de texto plano con marcas de tiempo

## Limitaciones

- El script respeta los límites de la API de YouTube (cuota diaria)
- Algunas transcripciones pueden no estar disponibles si el propietario del canal las ha deshabilitado
- La calidad de las transcripciones generadas automáticamente puede variar

## Solución de problemas

Si encuentras errores:

1. Verifica que tu clave API sea válida y tenga permisos para la API de YouTube Data v3
2. Asegúrate de que el ID del canal sea correcto
3. Comprueba tu conexión a Internet
4. Verifica que no hayas excedido la cuota diaria de la API de YouTube
5. Si el script se interrumpe, simplemente ejecútalo de nuevo y selecciona la opción de reanudar
6. Si encuentras errores específicos con ciertos videos, prueba a procesar ese video individualmente con `simple_extractor.py`
7. Si recibes un error como `zsh: no matches found: https://www.youtube.com/watch?v=VIDEO_ID`, asegúrate de poner la URL entre comillas

## Contribuir

Las contribuciones son bienvenidas. Por favor, sigue estos pasos:

1. Haz un fork del repositorio
2. Crea una rama para tu característica (`git checkout -b feature/nueva-caracteristica`)
3. Haz commit de tus cambios (`git commit -am 'Añadir nueva característica'`)
4. Haz push a la rama (`git push origin feature/nueva-caracteristica`)
5. Crea un nuevo Pull Request

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.