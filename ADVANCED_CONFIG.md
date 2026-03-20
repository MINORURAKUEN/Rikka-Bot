# ⚙️ Configuración Avanzada del Bot de Videos

## 📊 Presets de Calidad Personalizados

### Optimización para WhatsApp
Para videos que se compartirán en WhatsApp, usa estos parámetros:

```python
# En telegram_video_bot.py, línea 52
quality_settings = {
    'whatsapp': {'crf': '24', 'preset': 'medium', 'bitrate': '800k'},
}
```

Comando FFmpeg directo:
```bash
ffmpeg -i input.mp4 -c:v libx264 -crf 24 -preset medium -b:v 800k -c:a aac -b:a 128k output.mp4
```

### Optimización para Instagram
```python
'instagram': {'crf': '22', 'preset': 'medium', 'bitrate': '1500k'},
```

Comando FFmpeg directo:
```bash
ffmpeg -i input.mp4 -c:v libx264 -crf 22 -preset medium -b:v 1500k -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2" -c:a aac -b:a 192k output.mp4
```

### Optimización para YouTube
```python
'youtube': {'crf': '18', 'preset': 'slow', 'bitrate': '5000k'},
```

### Máxima Compresión (para compartir rápido)
```python
'tiny': {'crf': '32', 'preset': 'veryfast', 'bitrate': '300k'},
```

## 🎨 Personalización de Portadas

### Añadir portada con redimensionamiento automático
```bash
ffmpeg -i video.mp4 -i portada.jpg -map 0 -map 1 -c copy -disposition:v:1 attached_pic output.mp4
```

### Extraer portada de un video
```bash
ffmpeg -i video.mp4 -ss 00:00:05 -vframes 1 portada.jpg
```

## 📝 Trabajo Avanzado con Subtítulos

### Quemar subtítulos con estilos personalizados
```bash
# Subtítulos con fondo negro
ffmpeg -i video.mp4 -vf "subtitles=subs.srt:force_style='BackColour=&H80000000,BorderStyle=4'" output.mp4

# Subtítulos grandes y amarillos
ffmpeg -i video.mp4 -vf "subtitles=subs.srt:force_style='FontSize=24,PrimaryColour=&H00FFFF'" output.mp4
```

### Convertir formatos de subtítulos
```bash
# SRT a ASS
ffmpeg -i subtitulos.srt subtitulos.ass

# ASS a SRT
ffmpeg -i subtitulos.ass subtitulos.srt
```

## 🔊 Procesamiento de Audio

### Extraer audio con diferentes calidades
```bash
# Alta calidad (320kbps)
ffmpeg -i video.mp4 -vn -acodec libmp3lame -b:a 320k audio.mp3

# Media calidad (192kbps)
ffmpeg -i video.mp4 -vn -acodec libmp3lame -b:a 192k audio.mp3

# Baja calidad (128kbps)
ffmpeg -i video.mp4 -vn -acodec libmp3lame -b:a 128k audio.mp3
```

### Normalizar volumen del audio
```bash
ffmpeg -i input.mp4 -af "loudnorm" output.mp4
```

### Eliminar audio de un video
```bash
ffmpeg -i input.mp4 -c:v copy -an output.mp4
```

## 🎬 Funciones Adicionales que Puedes Agregar

### 1. Recortar Video (Trim)

Agrega esta función a la clase VideoProcessor:

```python
@staticmethod
def trim_video(input_path, output_path, start_time, end_time):
    """
    Recorta un video
    start_time: "00:00:10" (HH:MM:SS)
    end_time: "00:01:30"
    """
    cmd = [
        'ffmpeg',
        '-i', input_path,
        '-ss', start_time,
        '-to', end_time,
        '-c', 'copy',
        '-y',
        output_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error recortando video: {e}")
        return False
```

### 2. Cambiar Velocidad del Video

```python
@staticmethod
def change_speed(input_path, output_path, speed=1.0):
    """
    Cambia la velocidad del video
    speed: 0.5 (50% - lento), 1.0 (normal), 2.0 (200% - rápido)
    """
    cmd = [
        'ffmpeg',
        '-i', input_path,
        '-filter:v', f"setpts={1/speed}*PTS",
        '-filter:a', f"atempo={speed}",
        '-y',
        output_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error cambiando velocidad: {e}")
        return False
```

### 3. Rotar Video

```python
@staticmethod
def rotate_video(input_path, output_path, rotation=90):
    """
    Rota el video
    rotation: 90, 180, 270 grados
    """
    transpose_map = {
        90: '1',   # 90 grados horario
        180: '2,transpose=2',  # 180 grados
        270: '2'   # 90 grados antihorario
    }
    
    transpose = transpose_map.get(rotation, '1')
    
    cmd = [
        'ffmpeg',
        '-i', input_path,
        '-vf', f"transpose={transpose}",
        '-c:a', 'copy',
        '-y',
        output_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error rotando video: {e}")
        return False
```

### 4. Convertir Formato

```python
@staticmethod
def convert_format(input_path, output_path, output_format='mp4'):
    """
    Convierte el video a otro formato
    output_format: 'mp4', 'avi', 'mkv', 'webm', 'gif'
    """
    cmd = ['ffmpeg', '-i', input_path]
    
    if output_format == 'gif':
        cmd.extend([
            '-vf', 'fps=10,scale=480:-1:flags=lanczos',
            '-c:v', 'gif',
            '-y',
            output_path
        ])
    else:
        cmd.extend([
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-y',
            output_path
        ])
    
    try:
        result = subprocess.run(cmd, capture_output=True)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error convirtiendo formato: {e}")
        return False
```

### 5. Combinar Videos

```python
@staticmethod
def merge_videos(video_paths, output_path):
    """
    Combina múltiples videos en uno
    video_paths: lista de rutas de videos
    """
    # Crear archivo de lista
    list_file = '/tmp/merge_list.txt'
    with open(list_file, 'w') as f:
        for video in video_paths:
            f.write(f"file '{video}'\n")
    
    cmd = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', list_file,
        '-c', 'copy',
        '-y',
        output_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True)
        os.remove(list_file)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error combinando videos: {e}")
        return False
```

### 6. Añadir Marca de Agua

```python
@staticmethod
def add_watermark(input_path, watermark_path, output_path, position='bottom-right'):
    """
    Añade una marca de agua al video
    position: 'top-left', 'top-right', 'bottom-left', 'bottom-right', 'center'
    """
    position_map = {
        'top-left': '10:10',
        'top-right': 'W-w-10:10',
        'bottom-left': '10:H-h-10',
        'bottom-right': 'W-w-10:H-h-10',
        'center': '(W-w)/2:(H-h)/2'
    }
    
    overlay_pos = position_map.get(position, 'W-w-10:H-h-10')
    
    cmd = [
        'ffmpeg',
        '-i', input_path,
        '-i', watermark_path,
        '-filter_complex', f"overlay={overlay_pos}",
        '-c:a', 'copy',
        '-y',
        output_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error añadiendo marca de agua: {e}")
        return False
```

## 🔍 Análisis de Video

### Obtener información detallada
```bash
ffprobe -v quiet -print_format json -show_format -show_streams video.mp4
```

### Verificar calidad del video
```bash
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate,bit_rate -of default=noprint_wrappers=1 video.mp4
```

## 🚀 Optimizaciones de Rendimiento en Termux

### 1. Usar hardware acelerado (si está disponible)
```python
# En la función compress_video, añade:
'-hwaccel', 'auto',
```

### 2. Limitar uso de CPU
```python
# Añade al inicio de main():
os.nice(10)  # Reduce la prioridad del proceso
```

### 3. Procesar en lotes
```python
# Procesar múltiples archivos de forma secuencial
# en lugar de simultánea para evitar sobrecarga
```

### 4. Limpiar archivos temporales regularmente
```bash
# Agrega un cron job o comando manual
rm -rf ~/telegram_bot_files/*
```

## 📊 Monitoreo y Logs

### Ver progreso de FFmpeg en tiempo real
```python
def show_progress(line):
    if 'time=' in line:
        # Extraer y mostrar el tiempo procesado
        import re
        match = re.search(r'time=(\d+:\d+:\d+)', line)
        if match:
            print(f"Procesando: {match.group(1)}")
```

### Guardar logs detallados
```python
# En la configuración de logging:
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
```

## 🔐 Seguridad y Privacidad

### Limitar usuarios autorizados
```python
# Añade al inicio del archivo, después de imports:
AUTHORIZED_USERS = [123456789, 987654321]  # IDs de Telegram

# En cada handler, añade:
if update.effective_user.id not in AUTHORIZED_USERS:
    await update.message.reply_text("❌ No autorizado")
    return
```

### Limitar tamaño de archivos
```python
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# En handle_video:
if video.file_size > MAX_FILE_SIZE:
    await update.message.reply_text("❌ Archivo muy grande (máx. 100MB)")
    return
```

### Auto-limpieza de archivos antiguos
```python
import time

def cleanup_old_files(directory, max_age_hours=24):
    """Elimina archivos más antiguos que max_age_hours"""
    now = time.time()
    for file in Path(directory).glob('*'):
        if file.is_file():
            age_hours = (now - file.stat().st_mtime) / 3600
            if age_hours > max_age_hours:
                file.unlink()
                logger.info(f"Archivo antiguo eliminado: {file}")
```

## 📱 Notificaciones y Mensajes

### Personalizar mensajes
```python
# Mensajes en español con emojis
MESSAGES = {
    'welcome': '¡Hola! 👋 Bienvenido al bot de videos',
    'processing': '⚙️ Procesando tu video...',
    'success': '✅ ¡Listo! Aquí está tu video',
    'error': '❌ Hubo un error procesando el video',
}
```

### Enviar notificaciones de progreso
```python
# Actualizar mensaje cada X segundos durante el procesamiento
async def update_progress(message, current, total):
    progress = (current / total) * 100
    await message.edit_text(f"⚙️ Procesando: {progress:.1f}%")
```

## 🎯 Casos de Uso Específicos

### Para Creadores de Contenido
```python
# Preset para redes sociales
'social_media': {
    'crf': '20',
    'preset': 'medium',
    'bitrate': '2000k',
    'scale': '1920:1080'  # Full HD
}
```

### Para Ahorro de Datos
```python
# Preset ultra-comprimido
'data_saver': {
    'crf': '30',
    'preset': 'veryfast',
    'bitrate': '400k',
    'scale': '640:360'  # 360p
}
```

### Para Archivado
```python
# Preset de alta calidad para preservación
'archive': {
    'crf': '15',
    'preset': 'veryslow',
    'bitrate': '8000k'
}
```

## 🐛 Debug y Solución de Problemas

### Ver comando FFmpeg exacto
```python
# En cualquier función de VideoProcessor, añade:
logger.info(f"Ejecutando: {' '.join(cmd)}")
```

### Verificar errores de FFmpeg
```python
# En lugar de capture_output=True:
result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode != 0:
    logger.error(f"Error FFmpeg: {result.stderr}")
```

### Modo verbose
```python
# Cambiar el nivel de logging a DEBUG:
logging.basicConfig(level=logging.DEBUG)
```

---

**¡Con estas configuraciones puedes personalizar el bot a tu medida! 🎬✨**
