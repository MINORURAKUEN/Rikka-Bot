#!/usr/bin/env python3
"""
Bot de Telegram para procesamiento de videos y descargas (Versión con Pyrogram)
Soporta archivos grandes sin límite de 20MB
"""

import os
import re
import logging
import asyncio
import subprocess
from pathlib import Path
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# Configuración de logging mejorada
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),  # Para ver en terminal
        logging.FileHandler('bot.log')  # También guardar en archivo
    ]
)
logger = logging.getLogger(__name__)

# Configurar logging de Pyrogram para ver más detalles
logging.getLogger("pyrogram").setLevel(logging.WARNING)  # Menos verbose de Pyrogram

# Directorios de trabajo
WORK_DIR = Path.home() / 'telegram_bot_files'
WORK_DIR.mkdir(exist_ok=True)

DOWNLOAD_DIR = Path.home() / 'telegram_downloads'
DOWNLOAD_DIR.mkdir(exist_ok=True)

# Estados del usuario
user_states = {}

# Configuración de la API
API_ID = 30368923
API_HASH = "c77e78f4666683cb542fe4a2f7fd9045"

# Leer token del bot
token_file = Path.home() / '.telegram_bot_token'
if token_file.exists():
    BOT_TOKEN = token_file.read_text().strip()
else:
    BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not BOT_TOKEN:
    print("❌ Error: No se encontró el token del bot")
    print("Crea un archivo ~/.telegram_bot_token con tu token")
    exit(1)

# Crear cliente de Pyrogram
app = Client(
    "video_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)


class VideoProcessor:
    """Clase para procesar videos con FFmpeg"""
    
    @staticmethod
    def get_video_info(video_path):
        """Obtiene información del video"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            import json
            return json.loads(result.stdout)
        except Exception as e:
            logger.error(f"Error obteniendo info del video: {e}")
            return None
    
    @staticmethod
    def compress_video(input_path, output_path, quality='medium', progress_callback=None):
        """Comprime un video con FFmpeg"""
        quality_settings = {
            'low': {'crf': '28', 'preset': 'veryfast', 'bitrate': '500k'},
            'medium': {'crf': '23', 'preset': 'medium', 'bitrate': '1000k'},
            'high': {'crf': '20', 'preset': 'slow', 'bitrate': '2000k'},
            'ultra': {'crf': '18', 'preset': 'slower', 'bitrate': '3000k'}
        }
        
        settings = quality_settings.get(quality, quality_settings['medium'])
        
        logger.info(f"🎬 Iniciando compresión de video")
        logger.info(f"📁 Entrada: {input_path}")
        logger.info(f"📁 Salida: {output_path}")
        logger.info(f"⚙️ Calidad: {quality} (CRF: {settings['crf']}, Preset: {settings['preset']}, Bitrate: {settings['bitrate']})")
        
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-c:v', 'libx264',
            '-crf', settings['crf'],
            '-preset', settings['preset'],
            '-b:v', settings['bitrate'],
            '-c:a', 'aac',
            '-b:a', '128k',
            '-movflags', '+faststart',
            '-y',
            output_path
        ]
        
        logger.info(f"🔧 Comando FFmpeg: {' '.join(cmd)}")
        
        try:
            logger.info("⏳ Procesando video...")
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            for line in process.stderr:
                # Mostrar progreso de FFmpeg en la terminal
                if 'time=' in line:
                    logger.info(f"⚙️ {line.strip()}")
                if progress_callback:
                    progress_callback(line)
            
            process.wait()
            
            if process.returncode == 0:
                logger.info("✅ Video comprimido exitosamente")
            else:
                logger.error(f"❌ Error en compresión: código {process.returncode}")
            
            return process.returncode == 0
        except Exception as e:
            logger.error(f"❌ Error comprimiendo video: {e}")
            return False
    
    @staticmethod
    def add_thumbnail(video_path, thumbnail_path, output_path):
        """Añade una portada/thumbnail al video"""
        logger.info(f"🖼️ Iniciando añadido de portada")
        logger.info(f"📁 Video: {video_path}")
        logger.info(f"📁 Imagen: {thumbnail_path}")
        logger.info(f"📁 Salida: {output_path}")
        
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-i', thumbnail_path,
            '-map', '0',
            '-map', '1',
            '-c', 'copy',
            '-disposition:v:1', 'attached_pic',
            '-y',
            output_path
        ]
        
        logger.info(f"🔧 Comando FFmpeg: {' '.join(cmd)}")
        
        try:
            logger.info("⏳ Añadiendo portada al video...")
            result = subprocess.run(cmd, capture_output=True)
            
            if result.returncode == 0:
                logger.info("✅ Portada añadida exitosamente")
            else:
                logger.error(f"❌ Error añadiendo portada: código {result.returncode}")
                logger.error(f"FFmpeg stderr: {result.stderr.decode()[:500]}")
            
            return result.returncode == 0
        except Exception as e:
            logger.error(f"❌ Error añadiendo thumbnail: {e}")
            return False
    
    @staticmethod
    def burn_subtitles(video_path, subtitle_path, output_path):
        """Quema subtítulos en el video"""
        logger.info(f"📝 Iniciando quemado de subtítulos")
        logger.info(f"📁 Video: {video_path}")
        logger.info(f"📁 Subtítulos: {subtitle_path}")
        logger.info(f"📁 Salida: {output_path}")
        
        subtitle_path_escaped = subtitle_path.replace('\\', '\\\\').replace(':', '\\:')
        
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vf', f"subtitles='{subtitle_path_escaped}'",
            '-c:a', 'copy',
            '-y',
            output_path
        ]
        
        logger.info(f"🔧 Comando FFmpeg: {' '.join(cmd)}")
        
        try:
            logger.info("⏳ Procesando video con subtítulos...")
            result = subprocess.run(cmd, capture_output=True)
            
            if result.returncode == 0:
                logger.info("✅ Subtítulos quemados exitosamente")
            else:
                logger.error(f"❌ Error quemando subtítulos: código {result.returncode}")
                logger.error(f"FFmpeg stderr: {result.stderr.decode()[:500]}")
            
            return result.returncode == 0
        except Exception as e:
            logger.error(f"❌ Error quemando subtítulos: {e}")
            return False
    
    @staticmethod
    def extract_audio(video_path, output_path):
        """Extrae el audio de un video"""
        logger.info(f"🎵 Iniciando extracción de audio")
        logger.info(f"📁 Video: {video_path}")
        logger.info(f"📁 Audio salida: {output_path}")
        
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vn',
            '-acodec', 'libmp3lame',
            '-b:a', '192k',
            '-y',
            output_path
        ]
        
        logger.info(f"🔧 Comando FFmpeg: {' '.join(cmd)}")
        
        try:
            logger.info("⏳ Extrayendo audio...")
            result = subprocess.run(cmd, capture_output=True)
            
            if result.returncode == 0:
                audio_size = Path(output_path).stat().st_size / (1024 * 1024)
                logger.info(f"✅ Audio extraído exitosamente ({audio_size:.2f} MB)")
            else:
                logger.error(f"❌ Error extrayendo audio: código {result.returncode}")
                logger.error(f"FFmpeg stderr: {result.stderr.decode()[:500]}")
            
            return result.returncode == 0
        except Exception as e:
            logger.error(f"❌ Error extrayendo audio: {e}")
            return False


class MEGADownloader:
    """Clase para descargar archivos de MEGA"""
    
    @staticmethod
    def is_mega_url(url):
        """Verifica si es una URL de MEGA"""
        mega_patterns = [r'mega\.nz', r'mega\.co\.nz']
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in mega_patterns)
    
    @staticmethod
    async def download(url, output_dir, progress_callback=None):
        """Descarga archivo de MEGA usando megatools"""
        try:
            check_cmd = ['megadl', '--version']
            result = subprocess.run(check_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return False, None, "❌ megatools no está instalado.\nInstala con: pkg install megatools"
            
            cmd = [
                'megadl',
                '--path', str(output_dir),
                '--print-names',
                url
            ]
            
            logger.info(f"Ejecutando: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            stdout_lines = []
            for line in process.stdout:
                logger.info(f"MEGA output: {line.strip()}")
                stdout_lines.append(line.strip())
                if progress_callback:
                    await progress_callback(line.strip())
            
            process.wait()
            
            if process.returncode == 0:
                files = list(output_dir.glob('*'))
                if files:
                    latest_file = max(files, key=lambda p: p.stat().st_mtime)
                    return True, latest_file, None
                else:
                    return False, None, "❌ Archivo descargado no encontrado"
            else:
                stderr = process.stderr.read()
                logger.error(f"Error MEGA: {stderr}")
                return False, None, f"❌ Error: {stderr[:200]}"
            
        except Exception as e:
            logger.error(f"Error descargando de MEGA: {e}")
            return False, None, f"❌ Error: {str(e)}"


class MediaFireDownloader:
    """Clase para descargar archivos de MediaFire"""
    
    @staticmethod
    def is_mediafire_url(url):
        """Verifica si es una URL de MediaFire"""
        return bool(re.search(r'mediafire\.com', url, re.IGNORECASE))
    
    @staticmethod
    async def get_direct_link(url):
        """Obtiene el enlace directo de descarga de MediaFire"""
        try:
            cmd = ['curl', '-s', '-L', url]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return None
            
            html = result.stdout
            
            patterns = [
                r'href="(https://download\d+\.mediafire\.com/[^"]+)"',
                r'DownloadUrl = \'([^\']+)\'',
                r'kNO = "([^"]+)"',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, html)
                if match:
                    direct_url = match.group(1)
                    logger.info(f"Enlace directo encontrado: {direct_url}")
                    return direct_url
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo enlace directo: {e}")
            return None
    
    @staticmethod
    async def download(url, output_dir, progress_callback=None):
        """Descarga archivo de MediaFire"""
        try:
            if progress_callback:
                await progress_callback("🔍 Obteniendo enlace de descarga...")
            
            direct_url = await MediaFireDownloader.get_direct_link(url)
            
            if not direct_url:
                return False, None, "❌ No se pudo obtener el enlace de descarga"
            
            filename_match = re.search(r'/([^/]+)$', direct_url)
            if filename_match:
                filename = filename_match.group(1)
                filename = re.sub(r'[^\w\s\-\.]', '_', filename)
            else:
                filename = 'mediafire_download'
            
            output_path = output_dir / filename
            
            if progress_callback:
                await progress_callback(f"⬇️ Descargando: {filename}")
            
            wget_cmd = [
                'wget',
                '-O', str(output_path),
                '--progress=bar:force',
                '--no-check-certificate',
                direct_url
            ]
            
            curl_cmd = [
                'curl',
                '-L',
                '-o', str(output_path),
                '--progress-bar',
                direct_url
            ]
            
            # Intentar con wget primero
            cmd = wget_cmd
            try:
                subprocess.run(['wget', '--version'], check=True, capture_output=True)
            except:
                # Si wget no está disponible, usar curl
                cmd = curl_cmd
            
            logger.info(f"Ejecutando: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            process.wait()
            
            if process.returncode == 0 and output_path.exists():
                return True, output_path, None
            else:
                stderr = process.stderr.read() if process.stderr else "Error desconocido"
                return False, None, f"❌ Error descargando: {stderr[:200]}"
            
        except Exception as e:
            logger.error(f"Error descargando de MediaFire: {e}")
            return False, None, f"❌ Error: {str(e)}"


class UniversalDownloader:
    """Clase para detectar y descargar de múltiples servicios"""
    
    @staticmethod
    def detect_service(url):
        """Detecta el servicio de la URL"""
        if MEGADownloader.is_mega_url(url):
            return 'mega'
        elif MediaFireDownloader.is_mediafire_url(url):
            return 'mediafire'
        else:
            return None
    
    @staticmethod
    async def download(url, output_dir, progress_callback=None):
        """Descarga de cualquier servicio soportado"""
        service = UniversalDownloader.detect_service(url)
        
        if service == 'mega':
            success, file_path, error = await MEGADownloader.download(url, output_dir, progress_callback)
            return success, file_path, error, 'MEGA'
        
        elif service == 'mediafire':
            success, file_path, error = await MediaFireDownloader.download(url, output_dir, progress_callback)
            return success, file_path, error, 'MediaFire'
        
        else:
            return False, None, "❌ Servicio no soportado. Usa MEGA o MediaFire", None


# Comandos del bot con Pyrogram
@app.on_message(filters.command("start"))
async def start(client, message: Message):
    """Comando /start"""
    welcome_message = """🎬 <b>Bot de Procesamiento de Videos y Descargas</b>

¡Bienvenido! Puedo ayudarte con:

📹 <b>Comprimir videos</b> - Reduce el tamaño manteniendo calidad
🖼️ <b>Añadir portadas</b> - Agrega thumbnails personalizados
📝 <b>Quemar subtítulos</b> - Integra subtítulos permanentemente
🎵 <b>Extraer audio</b> - Obtén solo el audio del video

📥 <b>Descargar archivos:</b>
🔷 MEGA (mega.nz)
🔶 MediaFire (mediafire.com)

<b>Comandos de video:</b>
/compress - Comprimir un video
/thumbnail - Añadir portada a un video
/subtitles - Quemar subtítulos en un video
/extract_audio - Extraer audio de un video

<b>Comandos de descarga:</b>
/download - Descargar de MEGA o MediaFire
/help - Mostrar ayuda detallada

📥 Envíame un enlace de MEGA/MediaFire o un video para comenzar 🎥

✨ <b>Nuevo:</b> Ahora soporto archivos de cualquier tamaño!"""
    await message.reply_text(welcome_message, parse_mode=enums.ParseMode.HTML)


@app.on_message(filters.command("help"))
async def help_command(client, message: Message):
    """Comando /help"""
    help_text = """📖 <b>Ayuda Detallada</b>

<b>PROCESAMIENTO DE VIDEOS:</b>

<b>1️⃣ Comprimir Video:</b>
- Envía /compress o envía un video directamente
- Funciona con videos de cualquier tamaño ✨
- Elige el nivel de calidad (baja, media, alta, ultra)
- Espera a que se procese y descarga

<b>2️⃣ Añadir Portada:</b>
- Envía /thumbnail
- Envía el video
- Envía la imagen para la portada
- Recibe el video con portada

<b>3️⃣ Quemar Subtítulos:</b>
- Envía /subtitles
- Envía el video
- Envía el archivo de subtítulos (.srt, .ass)
- Recibe el video con subtítulos integrados

<b>4️⃣ Extraer Audio:</b>
- Envía /extract_audio
- Envía el video
- Recibe el archivo de audio en MP3

<b>DESCARGAS:</b>

<b>5️⃣ Descargar de MEGA/MediaFire:</b>
- Envía /download o pega directamente el enlace
- Servicios soportados:
  🔷 MEGA (mega.nz, mega.co.nz)
  🔶 MediaFire (mediafire.com)
- El bot descargará y te enviará el archivo

<b>Ejemplos de enlaces:</b>
• mega.nz/file/abc123#xyz789
• mediafire.com/file/abc123/archivo.zip

<b>Formatos soportados:</b>
- Video: MP4, MKV, AVI, MOV, WEBM
- Subtítulos: SRT, ASS, VTT
- Imágenes: JPG, PNG
- Descargas: Cualquier tipo de archivo

<b>Límites:</b>
- Videos: Sin límite de tamaño para descargar ✨
- Archivos procesados: Máx. 2GB para enviar (límite de Telegram)
- Tiempo de procesamiento: Depende del tamaño

<b>💡 Tip:</b> Ahora puedes enviar videos grandes directamente!

¿Necesitas ayuda? Contáctame con /start"""
    await message.reply_text(help_text, parse_mode=enums.ParseMode.HTML)


@app.on_message(filters.command("compress"))
async def compress_command(client, message: Message):
    """Comando /compress"""
    user_id = message.from_user.id
    user_states[user_id] = {'action': 'compress', 'step': 'waiting_video'}
    
    await message.reply_text(
        "📹 <b>Modo Compresión Activado</b>\n\n"
        "Envíame el video que quieres comprimir.\n"
        "✨ Sin límite de tamaño!",
        parse_mode=enums.ParseMode.HTML
    )


@app.on_message(filters.command("thumbnail"))
async def thumbnail_command(client, message: Message):
    """Comando /thumbnail"""
    user_id = message.from_user.id
    user_states[user_id] = {'action': 'thumbnail', 'step': 'waiting_video'}
    
    await message.reply_text(
        "🖼️ <b>Modo Añadir Portada Activado</b>\n\n"
        "Envíame el video al que quieres añadir una portada.",
        parse_mode=enums.ParseMode.HTML
    )


@app.on_message(filters.command("subtitles"))
async def subtitles_command(client, message: Message):
    """Comando /subtitles"""
    user_id = message.from_user.id
    user_states[user_id] = {'action': 'subtitles', 'step': 'waiting_video'}
    
    await message.reply_text(
        "📝 <b>Modo Quemar Subtítulos Activado</b>\n\n"
        "Envíame el video al que quieres añadir subtítulos.",
        parse_mode=enums.ParseMode.HTML
    )


@app.on_message(filters.command("extract_audio"))
async def extract_audio_command(client, message: Message):
    """Comando /extract_audio"""
    user_id = message.from_user.id
    user_states[user_id] = {'action': 'extract_audio', 'step': 'waiting_video'}
    
    await message.reply_text(
        "🎵 <b>Modo Extraer Audio Activado</b>\n\n"
        "Envíame el video del que quieres extraer el audio.",
        parse_mode=enums.ParseMode.HTML
    )


@app.on_message(filters.command("download"))
async def download_command(client, message: Message):
    """Comando /download"""
    await message.reply_text(
        "📥 <b>Modo Descarga Activado</b>\n\n"
        "Envíame un enlace de:\n"
        "🔷 MEGA (mega.nz)\n"
        "🔶 MediaFire (mediafire.com)\n\n"
        "Ejemplo:\n"
        "<code>https://mega.nz/file/abc123#xyz789</code>",
        parse_mode=enums.ParseMode.HTML
    )


@app.on_message(filters.video | filters.document)
async def handle_video(client, message: Message):
    """Maneja videos recibidos - SIN LÍMITE DE TAMAÑO con Pyrogram"""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    video = message.video or message.document
    
    if not video:
        return
    
    logger.info(f"📹 Nuevo video recibido de @{username} (ID: {user_id})")
    
    # Si no hay estado, activar compresión por defecto
    if user_id not in user_states:
        user_states[user_id] = {'action': 'compress', 'step': 'waiting_video'}
        logger.info(f"🔄 Modo por defecto: compresión activada")
    
    state = user_states[user_id]
    action = state.get('action')
    
    logger.info(f"⚙️ Acción solicitada: {action}")
    
    # Mostrar tamaño del archivo
    file_size_mb = video.file_size / (1024 * 1024) if video.file_size else 0
    logger.info(f"📦 Tamaño del archivo: {file_size_mb:.2f} MB")
    
    # Descargar video (Pyrogram maneja archivos grandes automáticamente)
    status_msg = await message.reply_text(
        f"⬇️ Descargando video...\n"
        f"📦 Tamaño: {file_size_mb:.1f} MB"
    )
    
    logger.info(f"⬇️ Iniciando descarga del video...")
    
    try:
        # Pyrogram descarga archivos grandes sin problemas
        video_path = await message.download(
            file_name=str(WORK_DIR / f"{user_id}_video_{video.file_unique_id}.mp4")
        )
        
        logger.info(f"✅ Video descargado en: {video_path}")
        logger.info(f"📁 Tamaño en disco: {Path(video_path).stat().st_size / (1024**2):.2f} MB")
        
        user_states[user_id]['video_path'] = str(video_path)
        
        if action == 'compress':
            logger.info("🎛️ Mostrando opciones de compresión al usuario")
            # Mostrar opciones de calidad
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔴 Baja (+ compresión)", callback_data='compress_low'),
                    InlineKeyboardButton("🟡 Media", callback_data='compress_medium')
                ],
                [
                    InlineKeyboardButton("🟢 Alta", callback_data='compress_high'),
                    InlineKeyboardButton("⭐ Ultra (- compresión)", callback_data='compress_ultra')
                ]
            ])
            
            await status_msg.edit_text(
                "✅ Video descargado\n\n"
                "Selecciona el nivel de compresión:",
                reply_markup=keyboard
            )
            
        elif action == 'thumbnail':
            logger.info("🖼️ Esperando imagen para thumbnail")
            user_states[user_id]['step'] = 'waiting_image'
            await status_msg.edit_text(
                "✅ Video descargado\n\n"
                "Ahora envíame la imagen que quieres usar como portada."
            )
            
        elif action == 'subtitles':
            logger.info("📝 Esperando archivo de subtítulos")
            user_states[user_id]['step'] = 'waiting_subtitle'
            await status_msg.edit_text(
                "✅ Video descargado\n\n"
                "Ahora envíame el archivo de subtítulos (.srt, .ass, .vtt)"
            )
            
        elif action == 'extract_audio':
            logger.info("🎵 Iniciando extracción de audio")
            await status_msg.edit_text("🎵 Extrayendo audio...")
            output_path = WORK_DIR / f"{user_id}_audio.mp3"
            
            if VideoProcessor.extract_audio(str(video_path), str(output_path)):
                logger.info(f"✅ Audio extraído: {output_path}")
                await message.reply_audio(
                    audio=str(output_path),
                    caption="🎵 Audio extraído exitosamente"
                )
                output_path.unlink()
                logger.info("🗑️ Archivo de audio temporal eliminado")
            else:
                logger.error("❌ Error extrayendo el audio")
                await message.reply_text("❌ Error extrayendo el audio")
            
            Path(video_path).unlink()
            logger.info("🗑️ Video temporal eliminado")
            del user_states[user_id]
            
    except Exception as e:
        logger.error(f"❌ Error procesando video: {e}", exc_info=True)
        await message.reply_text(f"❌ Error: {str(e)}")


@app.on_message(filters.photo)
async def handle_photo(client, message: Message):
    """Maneja imágenes recibidas (para thumbnails)"""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    logger.info(f"🖼️ Imagen recibida de @{username}")
    
    if user_id not in user_states:
        await message.reply_text("Usa /thumbnail primero para añadir una portada.")
        logger.warning(f"⚠️ Usuario {user_id} envió imagen sin estado activo")
        return
    
    state = user_states[user_id]
    
    if state.get('action') != 'thumbnail' or state.get('step') != 'waiting_image':
        logger.info(f"⏭️ Imagen ignorada (no está en modo thumbnail)")
        return
    
    logger.info(f"🖼️ Procesando imagen como thumbnail")
    
    status_msg = await message.reply_text("⬇️ Descargando imagen...")
    
    try:
        image_path = await message.download(
            file_name=str(WORK_DIR / f"{user_id}_thumb.jpg")
        )
        
        logger.info(f"✅ Imagen descargada: {image_path}")
        image_size = Path(image_path).stat().st_size / 1024
        logger.info(f"📦 Tamaño de imagen: {image_size:.2f} KB")
        
        await status_msg.edit_text("🖼️ Añadiendo portada al video...")
        
        video_path = state['video_path']
        output_path = WORK_DIR / f"{user_id}_with_thumb.mp4"
        
        logger.info(f"🎬 Video original: {video_path}")
        logger.info(f"📤 Video con portada: {output_path}")
        
        if VideoProcessor.add_thumbnail(video_path, str(image_path), str(output_path)):
            output_size = output_path.stat().st_size / (1024 * 1024)
            logger.info(f"✅ Video con portada generado ({output_size:.2f} MB)")
            logger.info(f"📤 Enviando video al usuario...")
            
            await message.reply_video(
                video=str(output_path),
                caption="✅ Portada añadida exitosamente"
            )
            
            logger.info(f"✅ Video enviado exitosamente")
            output_path.unlink()
            logger.info(f"🗑️ Archivo de salida eliminado")
        else:
            logger.error("❌ Fallo al añadir portada")
            await message.reply_text("❌ Error añadiendo la portada")
        
        Path(video_path).unlink()
        logger.info(f"🗑️ Video original eliminado")
        Path(image_path).unlink()
        logger.info(f"🗑️ Imagen eliminada")
        del user_states[user_id]
        logger.info(f"🧹 Estado del usuario limpiado")
        
    except Exception as e:
        logger.error(f"❌ Error procesando imagen: {e}", exc_info=True)
        await message.reply_text(f"❌ Error: {str(e)}")


@app.on_message(filters.document)
async def handle_document(client, message: Message):
    """Maneja documentos (para subtítulos)"""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    document = message.document
    
    if not document:
        return
    
    logger.info(f"📄 Documento recibido de @{username}: {document.file_name}")
    
    # Verificar si es un archivo de subtítulos
    if user_id in user_states and user_states[user_id].get('action') == 'subtitles':
        state = user_states[user_id]
        
        if state.get('step') != 'waiting_subtitle':
            return
        
        logger.info(f"📝 Procesando como archivo de subtítulos")
        
        status_msg = await message.reply_text("⬇️ Descargando subtítulos...")
        
        try:
            subtitle_ext = Path(document.file_name).suffix
            logger.info(f"📝 Extensión de subtítulos: {subtitle_ext}")
            
            subtitle_path = await message.download(
                file_name=str(WORK_DIR / f"{user_id}_sub{subtitle_ext}")
            )
            
            logger.info(f"✅ Subtítulos descargados: {subtitle_path}")
            
            await status_msg.edit_text("📝 Quemando subtítulos en el video...")
            
            video_path = state['video_path']
            output_path = WORK_DIR / f"{user_id}_with_subs.mp4"
            
            logger.info(f"🎬 Video original: {video_path}")
            logger.info(f"📤 Video con subtítulos: {output_path}")
            
            if VideoProcessor.burn_subtitles(video_path, str(subtitle_path), str(output_path)):
                output_size = output_path.stat().st_size / (1024 * 1024)
                logger.info(f"✅ Video con subtítulos generado ({output_size:.2f} MB)")
                logger.info(f"📤 Enviando video al usuario...")
                
                await message.reply_video(
                    video=str(output_path),
                    caption="✅ Subtítulos quemados exitosamente"
                )
                
                logger.info(f"✅ Video enviado exitosamente")
                output_path.unlink()
                logger.info(f"🗑️ Archivo de salida eliminado")
            else:
                logger.error("❌ Fallo al quemar subtítulos")
                await message.reply_text("❌ Error quemando los subtítulos")
            
            Path(video_path).unlink()
            logger.info(f"🗑️ Video original eliminado")
            Path(subtitle_path).unlink()
            logger.info(f"🗑️ Archivo de subtítulos eliminado")
            del user_states[user_id]
            logger.info(f"🧹 Estado del usuario limpiado")
            
        except Exception as e:
            logger.error(f"❌ Error procesando subtítulos: {e}", exc_info=True)
            await message.reply_text(f"❌ Error: {str(e)}")


@app.on_message(filters.text & filters.regex(r'https?://'))
async def handle_url(client, message: Message):
    """Maneja URLs de descarga"""
    url = message.text.strip()
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    logger.info(f"🔗 URL recibida de @{username}: {url}")
    
    # Detectar servicio
    service = UniversalDownloader.detect_service(url)
    
    if not service:
        logger.info(f"⏭️ URL ignorada (no es servicio soportado)")
        return
    
    logger.info(f"✅ Servicio detectado: {service.upper()}")
    
    # Crear directorio temporal para este usuario
    user_download_dir = DOWNLOAD_DIR / f"user_{user_id}"
    user_download_dir.mkdir(exist_ok=True)
    logger.info(f"📁 Directorio temporal: {user_download_dir}")
    
    # Mensaje de inicio
    status_msg = await message.reply_text(
        f"🔍 Detectado: <b>{service.upper()}</b>\n"
        f"⏳ Preparando descarga...",
        parse_mode=enums.ParseMode.HTML
    )
    
    # Callback para actualizar progreso
    last_update = [0]
    
    async def progress_callback(msg):
        import time
        current_time = time.time()
        if current_time - last_update[0] > 3:
            try:
                logger.info(f"📥 Progreso: {msg}")
                await status_msg.edit_text(
                    f"⬇️ Descargando de <b>{service.upper()}</b>\n\n{msg}",
                    parse_mode=enums.ParseMode.HTML
                )
                last_update[0] = current_time
            except:
                pass
    
    try:
        logger.info(f"🚀 Iniciando descarga desde {service.upper()}...")
        
        # Descargar archivo
        success, file_path, error, service_name = await UniversalDownloader.download(
            url, user_download_dir, progress_callback
        )
        
        if success and file_path:
            # Verificar tamaño del archivo
            file_size = file_path.stat().st_size
            max_size = 2 * 1024 * 1024 * 1024  # 2GB
            
            logger.info(f"✅ Archivo descargado: {file_path.name}")
            logger.info(f"📦 Tamaño: {file_size / (1024**2):.2f} MB")
            
            if file_size > max_size:
                logger.warning(f"⚠️ Archivo muy grande: {file_size / (1024**3):.2f} GB")
                await status_msg.edit_text(
                    f"❌ Archivo muy grande: {file_size / (1024**3):.2f} GB\n\n"
                    f"Telegram tiene un límite de 2GB"
                )
                file_path.unlink()
                return
            
            # Actualizar mensaje
            await status_msg.edit_text(
                f"✅ Descarga completada de <b>{service_name}</b>\n"
                f"📤 Enviando archivo...\n\n"
                f"📦 Tamaño: {file_size / (1024**2):.2f} MB",
                parse_mode=enums.ParseMode.HTML
            )
            
            # Determinar tipo de archivo y enviar
            file_ext = file_path.suffix.lower()
            filename = file_path.name
            
            logger.info(f"📤 Enviando archivo ({file_ext})...")
            
            try:
                if file_ext in ['.mp4', '.mkv', '.avi', '.mov', '.webm']:
                    logger.info("🎬 Enviando como video...")
                    await message.reply_video(
                        video=str(file_path),
                        caption=f"✅ Descargado de {service_name}",
                        supports_streaming=True
                    )
                elif file_ext in ['.mp3', '.m4a', '.wav', '.ogg', '.flac']:
                    logger.info("🎵 Enviando como audio...")
                    await message.reply_audio(
                        audio=str(file_path),
                        caption=f"✅ Descargado de {service_name}"
                    )
                elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                    logger.info("🖼️ Enviando como imagen...")
                    await message.reply_photo(
                        photo=str(file_path),
                        caption=f"✅ Descargado de {service_name}"
                    )
                else:
                    logger.info("📄 Enviando como documento...")
                    await message.reply_document(
                        document=str(file_path),
                        caption=f"✅ Descargado de {service_name}\n📦 {filename}"
                    )
                
                logger.info("✅ Archivo enviado exitosamente")
                await status_msg.delete()
                
            except Exception as e:
                logger.error(f"❌ Error enviando archivo: {e}", exc_info=True)
                await message.reply_text(
                    f"❌ Error enviando el archivo: {str(e)}\n\n"
                    f"El archivo fue descargado pero no se pudo enviar por Telegram."
                )
            
            # Limpiar archivo descargado
            try:
                file_path.unlink()
                logger.info("🗑️ Archivo temporal eliminado")
            except:
                pass
            
        else:
            logger.error(f"❌ Error en descarga: {error}")
            await status_msg.edit_text(f"❌ Error en la descarga\n\n{error}")
    
    except Exception as e:
        logger.error(f"❌ Error inesperado en handle_url: {e}", exc_info=True)
        await status_msg.edit_text(f"❌ Error inesperado: {str(e)}")
    
    # Limpiar directorio temporal si está vacío
    try:
        if user_download_dir.exists() and not any(user_download_dir.iterdir()):
            user_download_dir.rmdir()
            logger.info(f"🗑️ Directorio temporal eliminado")
    except:
        pass


@app.on_callback_query()
async def button_callback(client, callback_query: CallbackQuery):
    """Maneja los callbacks de los botones"""
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username or callback_query.from_user.first_name
    
    logger.info(f"🎛️ Callback recibido de @{username}: {callback_query.data}")
    
    if user_id not in user_states:
        await callback_query.answer("❌ Sesión expirada. Envía un video nuevamente.")
        logger.warning(f"⚠️ Usuario {user_id} sin estado activo")
        return
    
    state = user_states[user_id]
    video_path = state.get('video_path')
    
    if not video_path or not Path(video_path).exists():
        await callback_query.answer("❌ Video no encontrado.")
        logger.error(f"❌ Video no encontrado para usuario {user_id}")
        return
    
    # Determinar calidad
    quality_map = {
        'compress_low': 'low',
        'compress_medium': 'medium',
        'compress_high': 'high',
        'compress_ultra': 'ultra'
    }
    
    quality = quality_map.get(callback_query.data)
    
    if not quality:
        return
    
    logger.info(f"🎬 Iniciando compresión con calidad: {quality}")
    
    await callback_query.message.edit_text(
        f"⚙️ Comprimiendo video (calidad: {quality})...\n\nEsto puede tardar varios minutos."
    )
    
    try:
        output_path = WORK_DIR / f"{user_id}_compressed_{quality}.mp4"
        
        logger.info(f"📂 Archivo de salida: {output_path}")
        
        if VideoProcessor.compress_video(video_path, str(output_path), quality):
            # Obtener tamaños
            original_size = Path(video_path).stat().st_size / (1024 * 1024)
            compressed_size = output_path.stat().st_size / (1024 * 1024)
            reduction = ((original_size - compressed_size) / original_size) * 100
            
            logger.info(f"📊 Tamaño original: {original_size:.2f} MB")
            logger.info(f"📊 Tamaño comprimido: {compressed_size:.2f} MB")
            logger.info(f"📉 Reducción: {reduction:.1f}%")
            
            caption = (
                f"✅ Video comprimido exitosamente\n\n"
                f"📊 Tamaño original: {original_size:.2f} MB\n"
                f"📊 Tamaño comprimido: {compressed_size:.2f} MB\n"
                f"📉 Reducción: {reduction:.1f}%"
            )
            
            logger.info(f"📤 Enviando video comprimido al usuario...")
            
            await callback_query.message.reply_video(
                video=str(output_path),
                caption=caption
            )
            
            logger.info(f"✅ Video enviado exitosamente")
            
            output_path.unlink()
            logger.info(f"🗑️ Archivo de salida eliminado")
        else:
            logger.error("❌ Error en la compresión del video")
            await callback_query.message.reply_text("❌ Error comprimiendo el video")
        
        Path(video_path).unlink()
        logger.info(f"🗑️ Video original eliminado")
        del user_states[user_id]
        logger.info(f"🧹 Estado del usuario limpiado")
        
    except Exception as e:
        logger.error(f"❌ Error en compresión: {e}", exc_info=True)
        await callback_query.message.reply_text(f"❌ Error: {str(e)}")
    
    await callback_query.answer()


if __name__ == '__main__':
    print("=" * 60)
    print("🤖 BOT DE TELEGRAM - PROCESAMIENTO DE VIDEOS")
    print("=" * 60)
    print("✨ Versión: Pyrogram (Sin límite de tamaño)")
    print(f"📁 Directorio de trabajo: {WORK_DIR}")
    print(f"📥 Directorio de descargas: {DOWNLOAD_DIR}")
    print(f"📝 Log guardado en: bot.log")
    print("=" * 60)
    
    # Verificar FFmpeg
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        version_line = result.stdout.decode().split('\n')[0]
        print(f"✅ FFmpeg: {version_line}")
    except:
        print("❌ ADVERTENCIA: FFmpeg no está instalado")
        print("   Instala con: pkg install ffmpeg")
    
    # Verificar megatools
    try:
        subprocess.run(['megadl', '--version'], capture_output=True, check=True)
        print("✅ Megatools: Instalado")
    except:
        print("⚠️  Megatools no instalado (opcional para MEGA)")
        print("   Instala con: pkg install megatools")
    
    # Verificar wget/curl
    has_wget = False
    has_curl = False
    try:
        subprocess.run(['wget', '--version'], capture_output=True, check=True)
        has_wget = True
    except:
        pass
    
    try:
        subprocess.run(['curl', '--version'], capture_output=True, check=True)
        has_curl = True
    except:
        pass
    
    if has_wget or has_curl:
        print(f"✅ Descargador: {'wget' if has_wget else 'curl'}")
    else:
        print("⚠️  wget/curl no encontrado")
    
    print("=" * 60)
    print("🚀 Bot iniciado correctamente")
    print("📱 Comandos disponibles:")
    print("   /start - Iniciar bot")
    print("   /compress - Comprimir video")
    print("   /thumbnail - Añadir portada")
    print("   /subtitles - Quemar subtítulos")
    print("   /extract_audio - Extraer audio")
    print("   /download - Descargar de MEGA/MediaFire")
    print("=" * 60)
    print("⌨️  Presiona Ctrl+C para detener")
    print("=" * 60)
    print()
    
    logger.info("🤖 Bot iniciado correctamente")
    
    app.run()
