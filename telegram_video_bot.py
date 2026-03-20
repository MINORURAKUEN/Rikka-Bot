#!/usr/bin/env python3
"""
Bot de Telegram para procesamiento de videos y descargas
Funcionalidades:
- Comprimir videos con diferentes niveles de calidad
- Añadir portadas/thumbnails personalizadas
- Quemar subtítulos en el video
- Descargar archivos de MEGA y MediaFire
- Optimizado para ejecutarse en Termux
"""

import os
import re
import logging
import asyncio
import subprocess
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# Configuración de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Directorios de trabajo
WORK_DIR = Path.home() / 'telegram_bot_files'
WORK_DIR.mkdir(exist_ok=True)

DOWNLOAD_DIR = Path.home() / 'telegram_downloads'
DOWNLOAD_DIR.mkdir(exist_ok=True)

# Estados del usuario
user_states = {}

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
        """
        Comprime un video con FFmpeg
        quality: 'low', 'medium', 'high', 'ultra'
        """
        quality_settings = {
            'low': {'crf': '28', 'preset': 'veryfast', 'bitrate': '500k'},
            'medium': {'crf': '23', 'preset': 'medium', 'bitrate': '1000k'},
            'high': {'crf': '20', 'preset': 'slow', 'bitrate': '2000k'},
            'ultra': {'crf': '18', 'preset': 'slower', 'bitrate': '3000k'}
        }
        
        settings = quality_settings.get(quality, quality_settings['medium'])
        
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
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            for line in process.stderr:
                if progress_callback:
                    progress_callback(line)
            
            process.wait()
            return process.returncode == 0
        except Exception as e:
            logger.error(f"Error comprimiendo video: {e}")
            return False
    
    @staticmethod
    def add_thumbnail(video_path, thumbnail_path, output_path):
        """Añade una portada/thumbnail al video"""
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
        
        try:
            result = subprocess.run(cmd, capture_output=True)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error añadiendo thumbnail: {e}")
            return False
    
    @staticmethod
    def burn_subtitles(video_path, subtitle_path, output_path):
        """Quema subtítulos en el video"""
        # Escapar la ruta del archivo de subtítulos para FFmpeg
        subtitle_path_escaped = subtitle_path.replace('\\', '\\\\').replace(':', '\\:')
        
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vf', f"subtitles='{subtitle_path_escaped}'",
            '-c:a', 'copy',
            '-y',
            output_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error quemando subtítulos: {e}")
            return False
    
    @staticmethod
    def extract_audio(video_path, output_path):
        """Extrae el audio de un video"""
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vn',
            '-acodec', 'libmp3lame',
            '-b:a', '192k',
            '-y',
            output_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error extrayendo audio: {e}")
            return False


class MEGADownloader:
    """Clase para descargar archivos de MEGA"""
    
    @staticmethod
    def is_mega_url(url):
        """Verifica si es una URL de MEGA"""
        mega_patterns = [
            r'mega\.nz',
            r'mega\.co\.nz',
        ]
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in mega_patterns)
    
    @staticmethod
    async def download(url, output_dir, progress_callback=None):
        """
        Descarga archivo de MEGA usando megatools
        Retorna: (success, file_path, error_message)
        """
        try:
            # Verificar que megatools esté instalado
            check_cmd = ['megadl', '--version']
            result = subprocess.run(check_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return False, None, "❌ megatools no está instalado.\nInstala con: pkg install megatools"
            
            # Preparar comando de descarga
            cmd = [
                'megadl',
                '--path', str(output_dir),
                '--print-names',
                url
            ]
            
            logger.info(f"Ejecutando: {' '.join(cmd)}")
            
            # Ejecutar descarga
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Capturar salida
            stdout_lines = []
            for line in process.stdout:
                logger.info(f"MEGA output: {line.strip()}")
                stdout_lines.append(line.strip())
                if progress_callback:
                    await progress_callback(line.strip())
            
            process.wait()
            
            if process.returncode == 0:
                # Buscar el archivo descargado
                files = list(output_dir.glob('*'))
                if files:
                    # Obtener el archivo más reciente
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
            # Usar curl para obtener la página
            cmd = ['curl', '-s', '-L', url]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return None
            
            html = result.stdout
            
            # Buscar el enlace directo usando diferentes patrones
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
        """
        Descarga archivo de MediaFire
        Retorna: (success, file_path, error_message)
        """
        try:
            # Obtener enlace directo
            if progress_callback:
                await progress_callback("🔍 Obteniendo enlace de descarga...")
            
            direct_url = await MediaFireDownloader.get_direct_link(url)
            
            if not direct_url:
                return False, None, "❌ No se pudo obtener el enlace de descarga"
            
            # Extraer nombre del archivo de la URL
            filename_match = re.search(r'/([^/]+)$', direct_url)
            if filename_match:
                filename = filename_match.group(1)
                # Limpiar el nombre del archivo
                filename = re.sub(r'[^\w\s\-\.]', '_', filename)
            else:
                filename = 'mediafire_download'
            
            output_path = output_dir / filename
            
            if progress_callback:
                await progress_callback(f"⬇️ Descargando: {filename}")
            
            # Descargar con wget o curl
            # Primero intentar con wget
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
                subprocess.run(['which', 'wget'], check=True, capture_output=True)
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
        """
        Descarga de cualquier servicio soportado
        Retorna: (success, file_path, error_message, service)
        """
        service = UniversalDownloader.detect_service(url)
        
        if service == 'mega':
            success, file_path, error = await MEGADownloader.download(url, output_dir, progress_callback)
            return success, file_path, error, 'MEGA'
        
        elif service == 'mediafire':
            success, file_path, error = await MediaFireDownloader.download(url, output_dir, progress_callback)
            return success, file_path, error, 'MediaFire'
        
        else:
            return False, None, "❌ Servicio no soportado. Usa MEGA o MediaFire", None


# Comandos del bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    welcome_message = """
🎬 *Bot de Procesamiento de Videos y Descargas*

¡Bienvenido! Puedo ayudarte con:

📹 *Comprimir videos* - Reduce el tamaño manteniendo calidad
🖼️ *Añadir portadas* - Agrega thumbnails personalizados
📝 *Quemar subtítulos* - Integra subtítulos permanentemente
🎵 *Extraer audio* - Obtén solo el audio del video

📥 *Descargar archivos:*
🔷 MEGA (mega.nz)
🔶 MediaFire (mediafire.com)

*Comandos de video:*
/compress - Comprimir un video
/thumbnail - Añadir portada a un video
/subtitles - Quemar subtítulos en un video
/extract_audio - Extraer audio de un video

*Comandos de descarga:*
/download - Descargar de MEGA o MediaFire
/help - Mostrar ayuda detallada

📥 Envíame un enlace de MEGA/MediaFire o un video para comenzar 🎥
"""
    await update.message.reply_text(welcome_message, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /help"""
    help_text = """
📖 *Ayuda Detallada*

*PROCESAMIENTO DE VIDEOS:*

*1️⃣ Comprimir Video:*
- Envía /compress o envía un video directamente
- Elige el nivel de calidad (baja, media, alta, ultra)
- Espera a que se procese y descarga

*2️⃣ Añadir Portada:*
- Envía /thumbnail
- Envía el video
- Envía la imagen para la portada
- Recibe el video con portada

*3️⃣ Quemar Subtítulos:*
- Envía /subtitles
- Envía el video
- Envía el archivo de subtítulos (.srt, .ass)
- Recibe el video con subtítulos integrados

*4️⃣ Extraer Audio:*
- Envía /extract_audio
- Envía el video
- Recibe el archivo de audio en MP3

*DESCARGAS:*

*5️⃣ Descargar de MEGA/MediaFire:*
- Envía /download o pega directamente el enlace
- Servicios soportados:
  🔷 MEGA (mega.nz, mega.co.nz)
  🔶 MediaFire (mediafire.com)
- El bot descargará y te enviará el archivo

*Ejemplos de enlaces:*
• mega.nz/file/abc123#xyz789
• mediafire.com/file/abc123/archivo.zip

*Formatos soportados:*
- Video: MP4, MKV, AVI, MOV, WEBM
- Subtítulos: SRT, ASS, VTT
- Imágenes: JPG, PNG
- Descargas: Cualquier tipo de archivo

*Límites:*
- Tamaño máximo: 2GB (Telegram)
- Tiempo de procesamiento: Depende del tamaño

¿Necesitas ayuda? Contáctame con /start
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def compress_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /compress"""
    user_id = update.effective_user.id
    user_states[user_id] = {'action': 'compress', 'step': 'waiting_video'}
    
    await update.message.reply_text(
        "📹 *Modo Compresión Activado*\n\n"
        "Envíame el video que quieres comprimir.",
        parse_mode='Markdown'
    )


async def thumbnail_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /thumbnail"""
    user_id = update.effective_user.id
    user_states[user_id] = {'action': 'thumbnail', 'step': 'waiting_video'}
    
    await update.message.reply_text(
        "🖼️ *Modo Añadir Portada Activado*\n\n"
        "Envíame el video al que quieres añadir una portada.",
        parse_mode='Markdown'
    )


async def subtitles_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /subtitles"""
    user_id = update.effective_user.id
    user_states[user_id] = {'action': 'subtitles', 'step': 'waiting_video'}
    
    await update.message.reply_text(
        "📝 *Modo Quemar Subtítulos Activado*\n\n"
        "Envíame el video al que quieres añadir subtítulos.",
        parse_mode='Markdown'
    )


async def extract_audio_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /extract_audio"""
    user_id = update.effective_user.id
    user_states[user_id] = {'action': 'extract_audio', 'step': 'waiting_video'}
    
    await update.message.reply_text(
        "🎵 *Modo Extraer Audio Activado*\n\n"
        "Envíame el video del que quieres extraer el audio.",
        parse_mode='Markdown'
    )


async def download_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /download"""
    await update.message.reply_text(
        "📥 *Modo Descarga Activado*\n\n"
        "Envíame un enlace de:\n"
        "🔷 MEGA (mega.nz)\n"
        "🔶 MediaFire (mediafire.com)\n\n"
        "Ejemplo:\n"
        "`https://mega.nz/file/abc123#xyz789`",
        parse_mode='Markdown'
    )


async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja URLs de descarga"""
    url = update.message.text.strip()
    user_id = update.effective_user.id
    
    # Verificar si es una URL válida
    if not url.startswith(('http://', 'https://')):
        return
    
    # Detectar servicio
    service = UniversalDownloader.detect_service(url)
    
    if not service:
        # No es una URL de descarga, ignorar
        return
    
    # Crear directorio temporal para este usuario
    user_download_dir = DOWNLOAD_DIR / f"user_{user_id}"
    user_download_dir.mkdir(exist_ok=True)
    
    # Mensaje de inicio
    status_msg = await update.message.reply_text(
        f"🔍 Detectado: *{service.upper()}*\n"
        f"⏳ Preparando descarga...",
        parse_mode='Markdown'
    )
    
    # Callback para actualizar progreso
    last_update = [0]  # Usar lista para modificar en callback
    
    async def progress_callback(message):
        import time
        current_time = time.time()
        # Actualizar cada 3 segundos para no saturar
        if current_time - last_update[0] > 3:
            try:
                await status_msg.edit_text(
                    f"⬇️ Descargando de *{service.upper()}*\n\n{message}",
                    parse_mode='Markdown'
                )
                last_update[0] = current_time
            except:
                pass
    
    try:
        # Descargar archivo
        success, file_path, error, service_name = await UniversalDownloader.download(
            url, user_download_dir, progress_callback
        )
        
        if success and file_path:
            # Verificar tamaño del archivo
            file_size = file_path.stat().st_size
            max_size = 2 * 1024 * 1024 * 1024  # 2GB
            
            if file_size > max_size:
                await status_msg.edit_text(
                    f"❌ Archivo muy grande: {file_size / (1024**3):.2f} GB\n\n"
                    f"Telegram tiene un límite de 2GB",
                    parse_mode='Markdown'
                )
                file_path.unlink()
                return
            
            # Actualizar mensaje
            await status_msg.edit_text(
                f"✅ Descarga completada de *{service_name}*\n"
                f"📤 Enviando archivo...\n\n"
                f"📦 Tamaño: {file_size / (1024**2):.2f} MB",
                parse_mode='Markdown'
            )
            
            # Determinar tipo de archivo y enviar
            file_ext = file_path.suffix.lower()
            filename = file_path.name
            
            try:
                if file_ext in ['.mp4', '.mkv', '.avi', '.mov', '.webm']:
                    # Enviar como video
                    await update.message.reply_video(
                        video=file_path,
                        caption=f"✅ Descargado de {service_name}",
                        supports_streaming=True
                    )
                elif file_ext in ['.mp3', '.m4a', '.wav', '.ogg', '.flac']:
                    # Enviar como audio
                    await update.message.reply_audio(
                        audio=file_path,
                        caption=f"✅ Descargado de {service_name}"
                    )
                elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                    # Enviar como foto
                    await update.message.reply_photo(
                        photo=file_path,
                        caption=f"✅ Descargado de {service_name}"
                    )
                else:
                    # Enviar como documento
                    await update.message.reply_document(
                        document=file_path,
                        caption=f"✅ Descargado de {service_name}\n📦 {filename}"
                    )
                
                # Eliminar mensaje de estado
                await status_msg.delete()
                
            except Exception as e:
                logger.error(f"Error enviando archivo: {e}")
                await update.message.reply_text(
                    f"❌ Error enviando el archivo: {str(e)}\n\n"
                    f"El archivo fue descargado pero no se pudo enviar por Telegram."
                )
            
            # Limpiar archivo descargado
            try:
                file_path.unlink()
            except:
                pass
            
        else:
            await status_msg.edit_text(
                f"❌ Error en la descarga\n\n{error}",
                parse_mode='Markdown'
            )
    
    except Exception as e:
        logger.error(f"Error en handle_url: {e}")
        await status_msg.edit_text(
            f"❌ Error inesperado: {str(e)}",
            parse_mode='Markdown'
        )
    
    # Limpiar directorio temporal si está vacío
    try:
        if user_download_dir.exists() and not any(user_download_dir.iterdir()):
            user_download_dir.rmdir()
    except:
        pass


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja videos recibidos"""
    user_id = update.effective_user.id
    video = update.message.video or update.message.document
    
    if not video:
        return
    
    # Si no hay estado, activar compresión por defecto
    if user_id not in user_states:
        user_states[user_id] = {'action': 'compress', 'step': 'waiting_video'}
    
    state = user_states[user_id]
    action = state.get('action')
    
    # Descargar video
    status_msg = await update.message.reply_text("⬇️ Descargando video...")
    
    try:
        file = await context.bot.get_file(video.file_id)
        video_path = WORK_DIR / f"{user_id}_video_{video.file_id}.mp4"
        await file.download_to_drive(video_path)
        
        user_states[user_id]['video_path'] = str(video_path)
        
        if action == 'compress':
            # Mostrar opciones de calidad
            keyboard = [
                [
                    InlineKeyboardButton("🔴 Baja (+ compresión)", callback_data='compress_low'),
                    InlineKeyboardButton("🟡 Media", callback_data='compress_medium')
                ],
                [
                    InlineKeyboardButton("🟢 Alta", callback_data='compress_high'),
                    InlineKeyboardButton("⭐ Ultra (- compresión)", callback_data='compress_ultra')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await status_msg.edit_text(
                "✅ Video descargado\n\n"
                "Selecciona el nivel de compresión:",
                reply_markup=reply_markup
            )
            
        elif action == 'thumbnail':
            user_states[user_id]['step'] = 'waiting_image'
            await status_msg.edit_text(
                "✅ Video descargado\n\n"
                "Ahora envíame la imagen que quieres usar como portada."
            )
            
        elif action == 'subtitles':
            user_states[user_id]['step'] = 'waiting_subtitle'
            await status_msg.edit_text(
                "✅ Video descargado\n\n"
                "Ahora envíame el archivo de subtítulos (.srt, .ass, .vtt)"
            )
            
        elif action == 'extract_audio':
            await status_msg.edit_text("🎵 Extrayendo audio...")
            output_path = WORK_DIR / f"{user_id}_audio.mp3"
            
            if VideoProcessor.extract_audio(str(video_path), str(output_path)):
                await update.message.reply_audio(
                    audio=output_path,
                    caption="🎵 Audio extraído exitosamente"
                )
                output_path.unlink()
            else:
                await update.message.reply_text("❌ Error extrayendo el audio")
            
            video_path.unlink()
            del user_states[user_id]
            
    except Exception as e:
        logger.error(f"Error procesando video: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja imágenes recibidas (para thumbnails)"""
    user_id = update.effective_user.id
    
    if user_id not in user_states:
        await update.message.reply_text("Usa /thumbnail primero para añadir una portada.")
        return
    
    state = user_states[user_id]
    
    if state.get('action') != 'thumbnail' or state.get('step') != 'waiting_image':
        return
    
    status_msg = await update.message.reply_text("⬇️ Descargando imagen...")
    
    try:
        photo = update.message.photo[-1]  # Obtener la mayor resolución
        file = await context.bot.get_file(photo.file_id)
        image_path = WORK_DIR / f"{user_id}_thumb.jpg"
        await file.download_to_drive(image_path)
        
        await status_msg.edit_text("🖼️ Añadiendo portada al video...")
        
        video_path = state['video_path']
        output_path = WORK_DIR / f"{user_id}_with_thumb.mp4"
        
        if VideoProcessor.add_thumbnail(video_path, str(image_path), str(output_path)):
            await update.message.reply_video(
                video=output_path,
                caption="✅ Portada añadida exitosamente"
            )
            output_path.unlink()
        else:
            await update.message.reply_text("❌ Error añadiendo la portada")
        
        Path(video_path).unlink()
        image_path.unlink()
        del user_states[user_id]
        
    except Exception as e:
        logger.error(f"Error procesando imagen: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja documentos (para subtítulos y videos)"""
    user_id = update.effective_user.id
    document = update.message.document
    
    if not document:
        return
    
    # Verificar si es un video
    if document.mime_type and document.mime_type.startswith('video/'):
        await handle_video(update, context)
        return
    
    # Verificar si es un archivo de subtítulos
    if user_id in user_states and user_states[user_id].get('action') == 'subtitles':
        state = user_states[user_id]
        
        if state.get('step') != 'waiting_subtitle':
            return
        
        status_msg = await update.message.reply_text("⬇️ Descargando subtítulos...")
        
        try:
            file = await context.bot.get_file(document.file_id)
            subtitle_path = WORK_DIR / f"{user_id}_sub{Path(document.file_name).suffix}"
            await file.download_to_drive(subtitle_path)
            
            await status_msg.edit_text("📝 Quemando subtítulos en el video...")
            
            video_path = state['video_path']
            output_path = WORK_DIR / f"{user_id}_with_subs.mp4"
            
            if VideoProcessor.burn_subtitles(video_path, str(subtitle_path), str(output_path)):
                await update.message.reply_video(
                    video=output_path,
                    caption="✅ Subtítulos quemados exitosamente"
                )
                output_path.unlink()
            else:
                await update.message.reply_text("❌ Error quemando los subtítulos")
            
            Path(video_path).unlink()
            subtitle_path.unlink()
            del user_states[user_id]
            
        except Exception as e:
            logger.error(f"Error procesando subtítulos: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja los callbacks de los botones"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    if user_id not in user_states:
        await query.edit_message_text("❌ Sesión expirada. Envía un video nuevamente.")
        return
    
    state = user_states[user_id]
    video_path = state.get('video_path')
    
    if not video_path or not Path(video_path).exists():
        await query.edit_message_text("❌ Video no encontrado. Envía un video nuevamente.")
        return
    
    # Determinar calidad
    quality_map = {
        'compress_low': 'low',
        'compress_medium': 'medium',
        'compress_high': 'high',
        'compress_ultra': 'ultra'
    }
    
    quality = quality_map.get(query.data)
    
    if not quality:
        return
    
    await query.edit_message_text(f"⚙️ Comprimiendo video (calidad: {quality})...\n\nEsto puede tardar varios minutos.")
    
    try:
        output_path = WORK_DIR / f"{user_id}_compressed_{quality}.mp4"
        
        if VideoProcessor.compress_video(video_path, str(output_path), quality):
            # Obtener tamaños
            original_size = Path(video_path).stat().st_size / (1024 * 1024)  # MB
            compressed_size = output_path.stat().st_size / (1024 * 1024)  # MB
            reduction = ((original_size - compressed_size) / original_size) * 100
            
            caption = (
                f"✅ Video comprimido exitosamente\n\n"
                f"📊 Tamaño original: {original_size:.2f} MB\n"
                f"📊 Tamaño comprimido: {compressed_size:.2f} MB\n"
                f"📉 Reducción: {reduction:.1f}%"
            )
            
            await context.bot.send_video(
                chat_id=user_id,
                video=output_path,
                caption=caption
            )
            output_path.unlink()
        else:
            await context.bot.send_message(
                chat_id=user_id,
                text="❌ Error comprimiendo el video"
            )
        
        Path(video_path).unlink()
        del user_states[user_id]
        
    except Exception as e:
        logger.error(f"Error en compresión: {e}")
        await context.bot.send_message(
            chat_id=user_id,
            text=f"❌ Error: {str(e)}"
        )


def main():
    """Función principal"""
    # Leer token del archivo o variable de entorno
    token_file = Path.home() / '.telegram_bot_token'
    
    if token_file.exists():
        TOKEN = token_file.read_text().strip()
    else:
        TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not TOKEN:
        print("❌ Error: No se encontró el token del bot")
        print("Crea un archivo ~/.telegram_bot_token con tu token")
        print("O establece la variable de entorno TELEGRAM_BOT_TOKEN")
        return
    
    # Verificar FFmpeg
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except:
        print("❌ Error: FFmpeg no está instalado")
        print("Instala FFmpeg con: pkg install ffmpeg")
        return
    
    # Crear aplicación
    application = Application.builder().token(TOKEN).build()
    
    # Handlers de comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("compress", compress_command))
    application.add_handler(CommandHandler("thumbnail", thumbnail_command))
    application.add_handler(CommandHandler("subtitles", subtitles_command))
    application.add_handler(CommandHandler("extract_audio", extract_audio_command))
    application.add_handler(CommandHandler("download", download_command))
    
    # Handler de URLs (debe ir antes de otros handlers de texto)
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'https?://'), handle_url))
    
    # Handlers de contenido
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    # Handler de callbacks
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Iniciar bot
    print("🤖 Bot iniciado correctamente")
    print("Presiona Ctrl+C para detener")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
