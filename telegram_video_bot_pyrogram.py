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
import json
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
    def compress_video_resolution(input_path, output_path, scale=None, bitrate='2000k', crf='23', preset='medium', max_size_mb=None):
        """
        Comprime un video con resolución específica
        scale: '640:360' para 360p, '1280:720' para 720p, None para mantener original
        """
        logger.info(f"🎬 Iniciando compresión de video con resolución")
        logger.info(f"📁 Entrada: {input_path}")
        logger.info(f"📁 Salida: {output_path}")
        logger.info(f"📺 Resolución: {scale if scale else 'Original'}")
        logger.info(f"📊 Bitrate: {bitrate}, CRF: {crf}, Preset: {preset}")
        
        # Construir comando base
        cmd = ['ffmpeg', '-i', input_path]
        
        # Si hay escala, agregar filtro de video con mejor calidad
        if scale:
            # Para 360p usar algoritmo de escala Lanczos (mejor calidad) + optimizaciones
            if '360' in scale:
                cmd.extend([
                    '-vf', f'scale={scale}:force_original_aspect_ratio=decrease:flags=lanczos,pad={scale}:(ow-iw)/2:(oh-ih)/2',
                    '-c:v', 'libx264',
                    '-crf', crf,  # CRF 26 = buena calidad con bajo peso
                    '-preset', preset,
                    '-b:v', bitrate,
                    '-maxrate', bitrate,
                    '-bufsize', '900k',
                    '-profile:v', 'main',  # Perfil main para mejor calidad que baseline
                    '-level', '3.1',
                    '-pix_fmt', 'yuv420p'  # Compatibilidad universal
                ])
            else:
                cmd.extend([
                    '-vf', f'scale={scale}:force_original_aspect_ratio=decrease:flags=lanczos,pad={scale}:(ow-iw)/2:(oh-ih)/2',
                    '-c:v', 'libx264',
                    '-crf', crf,
                    '-preset', preset,
                    '-b:v', bitrate
                ])
        else:
            # Sin escala, solo recodificar
            cmd.extend([
                '-c:v', 'libx264',
                '-crf', crf,
                '-preset', preset,
                '-b:v', bitrate
            ])
        
        # Audio optimizado
        if '360' in str(scale):
            cmd.extend(['-c:a', 'aac', '-b:a', '96k', '-ar', '44100'])  # Audio comprimido pero con calidad
        else:
            cmd.extend(['-c:a', 'aac', '-b:a', '128k'])
        
        # Opciones generales
        cmd.extend(['-movflags', '+faststart', '-y', output_path])
        
        logger.info(f"🔧 Comando FFmpeg: {' '.join(cmd[:15])}...")
        
        try:
            logger.info("⏳ Procesando video...")
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            line_count = 0
            for line in process.stderr:
                # Mostrar progreso de FFmpeg de forma más limpia
                if 'time=' in line:
                    line_count += 1
                    # Mostrar solo cada 30 líneas (aprox. cada 5-10%)
                    if line_count % 30 == 0:
                        time_match = re.search(r'time=(\S+)', line)
                        if time_match:
                            logger.info(f"⚙️ Procesando: {time_match.group(1)}")
                elif 'error' in line.lower():
                    logger.error(f"❌ {line.strip()}")
            
            process.wait()
            
            if process.returncode != 0:
                logger.error(f"❌ Error en compresión: código {process.returncode}")
                return False
            
            # Mostrar tamaño final
            output_size_mb = Path(output_path).stat().st_size / (1024 * 1024)
            logger.info(f"📦 Tamaño final: {output_size_mb:.2f} MB")
            logger.info("✅ Video comprimido exitosamente")
            return True
            
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
    """Clase para descargar archivos de MEGA con progreso en tiempo real"""
    
    @staticmethod
    def is_mega_url(url):
        """Verifica si es una URL de MEGA"""
        mega_patterns = [r'mega\.nz', r'mega\.co\.nz']
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in mega_patterns)
    
    @staticmethod
    async def download(url, output_dir, progress_callback=None):
        """Descarga archivo de MEGA usando megatools con monitoreo mejorado"""
        try:
            logger.info("🔷 Iniciando descarga desde MEGA")
            
            # Verificar que megatools esté instalado
            check_cmd = ['megadl', '--version']
            result = subprocess.run(check_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error("❌ megatools no está instalado")
                return False, None, "❌ megatools no está instalado.\nInstala con: pkg install megatools"
            
            if progress_callback:
                await progress_callback("📥 Descargando de MEGA...")
            
            logger.info(f"📥 URL: {url}")
            
            # Comando de descarga con opciones mejoradas
            cmd = [
                'megadl',
                '--path', str(output_dir),
                '--print-names',
                '--no-progress',  # Desactivar barra de progreso de megadl
                url
            ]
            
            logger.info(f"🔧 Ejecutando: megadl --path {output_dir} [URL]")
            logger.info("⏳ Descargando desde MEGA...")
            
            # Ejecutar comando
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Monitorear salida en tiempo real
            filename = None
            for line in process.stdout:
                line = line.strip()
                if line:
                    logger.info(f"[MEGA] {line}")
                    
                    # Capturar nombre del archivo
                    if not filename and line and not line.startswith('ERROR'):
                        filename = line
            
            process.wait()
            
            if process.returncode == 0:
                # Buscar el archivo descargado
                files = list(output_dir.glob('*'))
                if files:
                    latest_file = max(files, key=lambda p: p.stat().st_mtime)
                    file_size = latest_file.stat().st_size / (1024 * 1024)
                    
                    logger.info(f"✅ Descarga MEGA completada")
                    logger.info(f"📁 Archivo: {latest_file.name}")
                    logger.info(f"📦 Tamaño: {file_size:.2f} MB")
                    
                    return True, latest_file, None
                else:
                    logger.error("❌ Archivo no encontrado después de la descarga")
                    return False, None, "❌ Archivo no encontrado"
            else:
                logger.error(f"❌ Error en megadl: código {process.returncode}")
                return False, None, "❌ Error descargando de MEGA"
            
        except Exception as e:
            logger.error(f"❌ Error en descarga MEGA: {e}", exc_info=True)
            return False, None, f"❌ Error: {str(e)}"


class MediaFireDownloader:
    """Clase para descargar archivos de MediaFire"""
    
    @staticmethod
    def is_mediafire_url(url):
        """Verifica si es una URL de MediaFire"""
        return bool(re.search(r'mediafire\.com', url, re.IGNORECASE))
    
    @staticmethod
    async def get_direct_link(url):
        """Obtiene el enlace directo de descarga de MediaFire (método mejorado)"""
        try:
            logger.info("🌐 Parseando página de MediaFire...")
            
            # Obtener página con User-Agent
            cmd = ['curl', '-s', '-L', '-A', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', url]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                logger.error("❌ Error obteniendo página de MediaFire")
                return None, None
            
            html = result.stdout
            
            # Patrón 1: Buscar botón de descarga (#downloadButton)
            download_button_match = re.search(r'<a[^>]*id="downloadButton"[^>]*href="([^"]+)"', html)
            if download_button_match:
                direct_url = download_button_match.group(1)
                logger.info(f"✅ Enlace encontrado (downloadButton): {direct_url[:80]}...")
            else:
                # Patrón 2: Buscar enlace de descarga directa
                direct_match = re.search(r'href="(https://download\d+\.mediafire\.com[^"]+)"', html)
                if direct_match:
                    direct_url = direct_match.group(1)
                    logger.info(f"✅ Enlace encontrado (regex): {direct_url[:80]}...")
                else:
                    logger.error("❌ No se encontró enlace de descarga")
                    return None, None
            
            # Obtener nombre del archivo
            filename = None
            
            # Patrón 1: promoDownloadName
            name_match1 = re.search(r'<div[^>]*class="[^"]*promoDownloadName[^"]*"[^>]*title="([^"]+)"', html)
            if name_match1:
                filename = name_match1.group(1)
            else:
                # Patrón 2: filename class
                name_match2 = re.search(r'<div[^>]*class="[^"]*filename[^"]*"[^>]*>([^<]+)', html)
                if name_match2:
                    filename = name_match2.group(1).strip()
                else:
                    # Extraer del URL
                    url_name_match = re.search(r'/file/[^/]+/([^/]+)/', url)
                    if url_name_match:
                        filename = url_name_match.group(1)
                    else:
                        filename = 'mediafire_download'
            
            # Limpiar nombre
            filename = re.sub(r'\s+', ' ', filename).strip()
            filename = re.sub(r'[^\w\s\-\.]', '_', filename)
            
            logger.info(f"📁 Nombre del archivo: {filename}")
            
            return direct_url, filename
            
        except Exception as e:
            logger.error(f"❌ Error parseando MediaFire: {e}")
            return None, None
    
    @staticmethod
    async def download(url, output_dir, progress_callback=None):
        """Descarga archivo de MediaFire con monitoreo mejorado"""
        try:
            if progress_callback:
                await progress_callback("🔍 Obteniendo enlace de descarga...")
            
            logger.info("🌐 Obteniendo enlace de MediaFire...")
            direct_url, filename = await MediaFireDownloader.get_direct_link(url)
            
            if not direct_url or not filename:
                return False, None, "❌ No se pudo obtener el enlace de descarga"
            
            output_path = output_dir / filename
            logger.info(f"📁 Descargando: {filename}")
            logger.info(f"📥 Desde: {direct_url[:80]}...")
            
            if progress_callback:
                await progress_callback(f"⬇️ Descargando: {filename}")
            
            # Usar wget con parámetros optimizados para velocidad
            wget_cmd = [
                'wget',
                '-O', str(output_path),
                '--progress=dot:giga',  # Menos verboso, más rápido
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                '--no-check-certificate',
                '--timeout=30',  # Timeout de 30 segundos
                '--tries=3',  # 3 intentos
                '--continue',  # Continuar descarga si se interrumpe
                direct_url
            ]
            
            curl_cmd = [
                'curl',
                '-L',
                '-C', '-',  # Continuar descarga
                '-A', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                '-o', str(output_path),
                '--speed-limit', '1000',  # Velocidad mínima 1KB/s
                '--speed-time', '30',  # Timeout si está por debajo de velocidad mínima
                direct_url
            ]
            
            aria2c_cmd = [
                'aria2c',
                '-x', '16',  # 16 conexiones simultáneas
                '-s', '16',  # 16 servidores
                '-k', '1M',  # Fragmentos de 1MB
                '--file-allocation=none',
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                '--allow-overwrite=true',
                '--auto-file-renaming=false',
                '-d', str(output_dir),
                '-o', filename,
                direct_url
            ]
            
            # Intentar con aria2c primero (más rápido), luego wget, luego curl
            cmd = None
            downloader = None
            
            try:
                subprocess.run(['aria2c', '--version'], check=True, capture_output=True)
                cmd = aria2c_cmd
                downloader = "aria2c"
                logger.info("🚀 Usando aria2c para descarga rápida (16 conexiones)")
            except:
                try:
                    subprocess.run(['wget', '--version'], check=True, capture_output=True)
                    cmd = wget_cmd
                    downloader = "wget"
                    logger.info("📥 Usando wget para descargar")
                except:
                    cmd = curl_cmd
                    downloader = "curl"
                    logger.info("📥 Usando curl para descargar")
            
            logger.info("⏳ Iniciando descarga de MediaFire...")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Monitorear progreso en tiempo real (filtrado mejorado)
            last_percent = [0]
            for line in process.stdout:
                line = line.strip()
                if line:
                    # Para aria2c - mostrar solo cada 5%
                    if downloader == "aria2c" and "SPD:" in line:
                        percent_match = re.search(r'\((\d+)%\)', line)
                        if percent_match:
                            percent = int(percent_match.group(1))
                            if percent - last_percent[0] >= 5:
                                logger.info(f"📥 Descargando: {percent}%")
                                last_percent[0] = percent
                    # Para wget/curl - mostrar solo cada 10%
                    elif any(kw in line.lower() for kw in ['%', 'mb', 'kb']):
                        percent_match = re.search(r'(\d+)%', line)
                        if percent_match:
                            percent = int(percent_match.group(1))
                            if percent - last_percent[0] >= 10:
                                logger.info(f"📥 Descargando: {percent}%")
                                last_percent[0] = percent
                        elif 'saving' in line.lower() or 'mb' in line.lower():
                            logger.info(f"[MEDIAFIRE] {line}")
            
            process.wait()
            
            if process.returncode == 0 and output_path.exists():
                file_size = output_path.stat().st_size / (1024 * 1024)
                logger.info(f"✅ Descarga MediaFire completada")
                logger.info(f"📦 Tamaño: {file_size:.2f} MB")
                return True, output_path, None
            else:
                logger.error(f"❌ Error en descarga, código: {process.returncode}")
                return False, None, "❌ Error descargando de MediaFire"
            
        except Exception as e:
            logger.error(f"❌ Error descargando de MediaFire: {e}", exc_info=True)
            return False, None, f"❌ Error: {str(e)}"
            
            process.wait()
            
            if process.returncode == 0 and output_path.exists():
                file_size = output_path.stat().st_size / (1024 * 1024)
                logger.info(f"✅ Descarga MediaFire completada")
                logger.info(f"📦 Tamaño: {file_size:.2f} MB")
                return True, output_path, None
            else:
                logger.error(f"❌ Error en descarga, código: {process.returncode}")
                return False, None, f"❌ Error descargando"
            
        except Exception as e:
            logger.error(f"❌ Error descargando de MediaFire: {e}")
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

🈺 <b>Buscar anime:</b>
Obtén información completa de cualquier anime

<b>Comandos de video:</b>
/compress - Comprimir un video
/thumbnail - Añadir portada a un video
/subtitles - Quemar subtítulos en un video
/extract_audio - Extraer audio de un video

<b>Comandos de descarga:</b>
/download - Descargar de MEGA o MediaFire

<b>Comandos de búsqueda:</b>
/anime - Buscar información de anime
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
- Elige el formato y resolución
- Los videos se envían como archivo descargable

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

<b>BÚSQUEDA:</b>

<b>6️⃣ Buscar Anime:</b>
- Envía /anime Nombre del anime
- Obtén información completa con imagen
- Ejemplo: /anime One Piece

<b>Ejemplos de enlaces:</b>
• mega.nz/file/abc123#xyz789
• mediafire.com/file/abc123/archivo.zip

<b>Formatos soportados:</b>
- Descargas: Videos se envían como video reproducible
- Compresión: Videos se envían como archivo descargable
- Subtítulos: SRT, ASS, VTT
- Imágenes: JPG, PNG
- Audio: MP3, M4A, WAV, OGG, FLAC

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


@app.on_message(filters.command("anime"))
async def anime_command(client, message: Message):
    """Comando /anime - Busca información de anime"""
    
    # Obtener el nombre del anime
    args = message.text.split(maxsplit=1)
    
    if len(args) < 2:
        await message.reply_text(
            "🈺 <b>Búsqueda de Anime</b>\n\n"
            "Por favor ingresa el nombre del anime:\n"
            "<code>/anime Nombre del anime</code>\n\n"
            "Ejemplo:\n"
            "<code>/anime One Piece</code>",
            parse_mode=enums.ParseMode.HTML
        )
        return
    
    anime_name = args[1]
    logger.info(f"🈺 Buscando anime: {anime_name}")
    
    status_msg = await message.reply_text("⏳ Buscando información del anime...")
    
    try:
        # Query GraphQL para AniList
        query = """
        query ($search: String) {
            Media (search: $search, type: ANIME) {
                id
                title { romaji english native }
                studios(isMain: true) { nodes { name } }
                seasonYear
                episodes
                genres
                duration
                format
                season
                status
                description
                bannerImage
                coverImage { extraLarge large medium }
            }
        }
        """
        
        # Hacer petición a la API de AniList
        cmd = [
            'curl', '-s', '-X', 'POST',
            'https://graphql.anilist.co',
            '-H', 'Content-Type: application/json',
            '-H', 'Accept: application/json',
            '-d', json.dumps({
                'query': query,
                'variables': {'search': anime_name}
            })
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        
        if result.returncode != 0:
            await status_msg.edit_text("❌ Error al buscar el anime. Intenta de nuevo.")
            return
        
        # Parsear respuesta JSON
        data = json.loads(result.stdout)
        
        if not data.get('data') or not data['data'].get('Media'):
            await status_msg.edit_text(f"❌ No se encontró el anime: {anime_name}")
            return
        
        anime = data['data']['Media']
        
        # Traducciones
        ESTADOS = {
            'FINISHED': 'Finalizado',
            'RELEASING': 'En emisión',
            'NOT_YET_RELEASED': 'Próximamente',
            'CANCELLED': 'Cancelado',
            'HIATUS': 'En pausa'
        }
        
        TEMPORADAS = {
            'WINTER': 'Invierno',
            'SPRING': 'Primavera',
            'SUMMER': 'Verano',
            'FALL': 'Otoño'
        }
        
        FORMATOS = {
            'TV': 'Serie de TV',
            'MOVIE': 'Película',
            'SPECIAL': 'Especial',
            'OVA': 'OVA',
            'ONA': 'ONA',
            'MUSIC': 'Musical',
            'TV_SHORT': 'Serie Corta'
        }
        
        # Construir información
        titulo = anime['title']['romaji'] or anime['title']['english'] or anime['title']['native']
        titulo_ingles = anime['title'].get('english', '')
        titulo_nativo = anime['title'].get('native', '')
        
        estudios = ', '.join([s['name'] for s in anime['studios']['nodes']]) if anime['studios']['nodes'] else 'Desconocido'
        generos = ', '.join(anime['genres']) if anime['genres'] else 'N/A'
        
        # Limpiar sinopsis HTML
        sinopsis = anime.get('description', 'No disponible')
        if sinopsis != 'No disponible':
            sinopsis = re.sub(r'<[^>]+>', '', sinopsis).strip()
            # Limitar sinopsis a 400 caracteres
            if len(sinopsis) > 400:
                sinopsis = sinopsis[:400] + '...'
        
        # Formatear sinopsis
        sinopsis_formateada = '\n'.join([f"> {linea}" for linea in sinopsis.split('\n') if linea.strip()])
        
        # Construir mensaje
        info = f"""✨ <b>INFORMACIÓN DEL ANIME</b> ✨

🈺 <b>Título:</b> {titulo}
{f'🔤 <b>Título inglés:</b> {titulo_ingles}' if titulo_ingles and titulo_ingles != titulo else ''}
{f'🈯 <b>Título nativo:</b> {titulo_nativo}' if titulo_nativo and titulo_nativo != titulo else ''}
🏦 <b>Estudio:</b> {estudios}
📆 <b>Año:</b> {anime.get('seasonYear', 'N/A')}
🗂 <b>Episodios:</b> {anime.get('episodes', 'En emisión')}
🏷 <b>Géneros:</b> {generos}
⏱ <b>Duración:</b> {anime.get('duration', 'N/A')} min
💽 <b>Formato:</b> {FORMATOS.get(anime.get('format'), anime.get('format', 'N/A'))}
🔅 <b>Temporada:</b> {TEMPORADAS.get(anime.get('season'), 'N/A')}
⏳ <b>Estado:</b> {ESTADOS.get(anime.get('status'), anime.get('status', 'N/A'))}

📜 <b>Sinopsis:</b>
{sinopsis_formateada}"""
        
        # Obtener imagen
        image_url = anime['coverImage'].get('extraLarge') or anime.get('bannerImage') or anime['coverImage'].get('large')
        
        if image_url:
            # Descargar imagen
            img_cmd = ['curl', '-s', '-L', image_url]
            img_result = subprocess.run(img_cmd, capture_output=True, timeout=30)
            
            if img_result.returncode == 0 and len(img_result.stdout) > 0:
                # Guardar imagen temporal
                temp_img = WORK_DIR / f"anime_{message.from_user.id}.jpg"
                temp_img.write_bytes(img_result.stdout)
                
                # Enviar con imagen
                await message.reply_photo(
                    photo=str(temp_img),
                    caption=info,
                    parse_mode=enums.ParseMode.HTML
                )
                
                # Eliminar status y temp
                await status_msg.delete()
                temp_img.unlink()
            else:
                await status_msg.edit_text(info, parse_mode=enums.ParseMode.HTML)
        else:
            await status_msg.edit_text(info, parse_mode=enums.ParseMode.HTML)
        
        logger.info(f"✅ Anime encontrado: {titulo}")
        
    except Exception as e:
        logger.error(f"❌ Error buscando anime: {e}", exc_info=True)
        await status_msg.edit_text(
            f"❌ <b>Error al buscar el anime</b>\n\n"
            f"Detalles: {str(e)[:100]}",
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
    
    logger.info(f"⬇️ Iniciando descarga del video desde Telegram...")
    
    # Función de progreso (más limpia)
    last_download_percent = [0]
    async def download_progress(current, total):
        percent = int((current / total) * 100)
        # Mostrar solo cada 10%
        if percent - last_download_percent[0] >= 10:
            mb_current = current / (1024**2)
            mb_total = total / (1024**2)
            logger.info(f"⬇️ Descarga: {percent}% ({mb_current:.1f}/{mb_total:.1f} MB)")
            last_download_percent[0] = percent
    
    try:
        # Pyrogram descarga archivos grandes sin problemas
        video_path = await message.download(
            file_name=str(WORK_DIR / f"{user_id}_video_{video.file_unique_id}.mp4"),
            progress=download_progress
        )
        
        logger.info(f"✅ Video descargado en: {video_path}")
        logger.info(f"📁 Tamaño en disco: {Path(video_path).stat().st_size / (1024**2):.2f} MB")
        
        user_states[user_id]['video_path'] = str(video_path)
        
        if action == 'compress':
            logger.info("🎛️ Mostrando opciones de compresión al usuario")
            # Guardar información del video para el siguiente paso
            user_states[user_id]['video_info'] = {
                'size_mb': Path(video_path).stat().st_size / (1024**2),
                'original_ext': Path(video_path).suffix
            }
            
            # Primero preguntar por el formato
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📄 MP4 (Archivo)", callback_data='format_mp4'),
                    InlineKeyboardButton("📄 MKV (Archivo)", callback_data='format_mkv')
                ],
                [
                    InlineKeyboardButton("📄 AVI (Archivo)", callback_data='format_avi'),
                    InlineKeyboardButton("📄 WEBM (Archivo)", callback_data='format_webm')
                ],
                [
                    InlineKeyboardButton("📄 MOV (Archivo)", callback_data='format_mov'),
                    InlineKeyboardButton("⚡ Mantener original", callback_data='format_original')
                ]
            ])
            
            await status_msg.edit_text(
                "✅ Video descargado\n\n"
                "📦 Tamaño: {:.2f} MB\n\n"
                "Selecciona el formato de salida:".format(
                    user_states[user_id]['video_info']['size_mb']
                ),
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
            
            logger.info(f"📤 Preparando envío de archivo ({file_ext})...")
            logger.info(f"📦 Tamaño a enviar: {file_size / (1024**2):.2f} MB")
            
            # Función de progreso para Pyrogram (más limpia)
            last_send_percent = [0]
            async def progress(current, total):
                percent = int((current / total) * 100)
                # Mostrar solo cada 10%
                if percent - last_send_percent[0] >= 10:
                    mb_current = current / (1024**2)
                    mb_total = total / (1024**2)
                    logger.info(f"📤 Enviando: {percent}% ({mb_current:.1f}/{mb_total:.1f} MB)")
                    last_send_percent[0] = percent
            
            try:
                if file_ext in ['.mp4', '.mkv', '.avi', '.mov', '.webm']:
                    logger.info("🎬 Enviando como video...")
                    await message.reply_video(
                        video=str(file_path),
                        caption=f"✅ Descargado de {service_name}",
                        supports_streaming=True,
                        progress=progress
                    )
                elif file_ext in ['.mp3', '.m4a', '.wav', '.ogg', '.flac']:
                    logger.info("🎵 Enviando como audio...")
                    await message.reply_audio(
                        audio=str(file_path),
                        caption=f"✅ Descargado de {service_name}",
                        progress=progress
                    )
                elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                    logger.info("🖼️ Enviando como imagen...")
                    await message.reply_photo(
                        photo=str(file_path),
                        caption=f"✅ Descargado de {service_name}",
                        progress=progress
                    )
                else:
                    logger.info(f"📄 Enviando como documento: {filename}")
                    await message.reply_document(
                        document=str(file_path),
                        caption=f"✅ Descargado de {service_name}\n📦 {filename}",
                        progress=progress
                    )
                
                logger.info("✅ Archivo enviado exitosamente al usuario")
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
    
    # Manejar selección de formato
    if callback_query.data.startswith('format_'):
        format_choice = callback_query.data.replace('format_', '')
        
        # Mapeo de formatos
        format_map = {
            'mp4': '.mp4',
            'mkv': '.mkv',
            'avi': '.avi',
            'webm': '.webm',
            'mov': '.mov',
            'original': state.get('video_info', {}).get('original_ext', '.mp4')
        }
        
        output_format = format_map.get(format_choice, '.mp4')
        state['output_format'] = output_format
        
        logger.info(f"📹 Formato seleccionado: {output_format}")
        
        # Ahora mostrar opciones de calidad
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📱 360p", callback_data='quality_360p'),
                InlineKeyboardButton("📺 480p", callback_data='quality_480p')
            ],
            [
                InlineKeyboardButton("🖥️ 720p HD", callback_data='quality_720p'),
                InlineKeyboardButton("🎬 1080p Full HD", callback_data='quality_1080p')
            ],
            [
                InlineKeyboardButton("⚡ Original", callback_data='quality_original')
            ]
        ])
        
        await callback_query.message.edit_text(
            f"✅ Formato seleccionado: {output_format.upper()}\n\n"
            f"Ahora selecciona la resolución:",
            reply_markup=keyboard
        )
        
        await callback_query.answer()
        return
    
    # Manejar selección de calidad
    if callback_query.data.startswith('quality_'):
        resolution_map = {
            'quality_360p': {'scale': '640:360', 'bitrate': '450k', 'crf': '26', 'preset': 'medium', 'label': '360p', 'max_size_mb': None},
            'quality_480p': {'scale': '854:480', 'bitrate': '1000k', 'crf': '23', 'preset': 'medium', 'label': '480p', 'max_size_mb': None},
            'quality_720p': {'scale': '1280:720', 'bitrate': '2500k', 'crf': '23', 'preset': 'medium', 'label': '720p HD', 'max_size_mb': None},
            'quality_1080p': {'scale': '1920:1080', 'bitrate': '5000k', 'crf': '20', 'preset': 'medium', 'label': '1080p Full HD', 'max_size_mb': None},
            'quality_original': {'scale': None, 'bitrate': '3000k', 'crf': '23', 'preset': 'medium', 'label': 'Original', 'max_size_mb': None}
        }
        
        resolution_config = resolution_map.get(callback_query.data)
        output_format = state.get('output_format', '.mp4')
        
        if not resolution_config:
            return
        
        scale = resolution_config['scale']
        bitrate = resolution_config['bitrate']
        crf = resolution_config['crf']
        preset = resolution_config['preset']
        label = resolution_config['label']
        max_size_mb = resolution_config['max_size_mb']
        
        logger.info(f"🎬 Iniciando compresión - Resolución: {label}, Formato: {output_format}")
        
        await callback_query.message.edit_text(
            f"⚙️ Comprimiendo video...\n"
            f"📹 Formato: {output_format.upper()}\n"
            f"📺 Resolución: {label}\n\n"
            f"Esto puede tardar varios minutos."
        )
        
        try:
            resolution_name = callback_query.data.replace('quality_', '')
            output_path = WORK_DIR / f"{user_id}_compressed_{resolution_name}{output_format}"
            
            logger.info(f"📂 Archivo de salida: {output_path}")
            
            # Usar función de compresión con resolución
            success = VideoProcessor.compress_video_resolution(
                video_path, str(output_path), scale, bitrate, crf, preset, max_size_mb
            )
            
            if success:
                # Obtener tamaños
                original_size = Path(video_path).stat().st_size / (1024 * 1024)
                compressed_size = output_path.stat().st_size / (1024 * 1024)
                reduction = ((original_size - compressed_size) / original_size) * 100
                
                logger.info(f"📊 Tamaño original: {original_size:.2f} MB")
                logger.info(f"📊 Tamaño comprimido: {compressed_size:.2f} MB")
                logger.info(f"📉 Reducción: {reduction:.1f}%")
                
                caption = (
                    f"✅ Video comprimido exitosamente\n\n"
                    f"📹 Formato: {output_format.upper()}\n"
                    f"📺 Resolución: {label}\n"
                    f"📊 Tamaño original: {original_size:.2f} MB\n"
                    f"📊 Tamaño comprimido: {compressed_size:.2f} MB\n"
                    f"📉 Reducción: {reduction:.1f}%"
                )
                
                logger.info(f"📤 Enviando video comprimido como documento...")
                
                # Función de progreso para subida (más limpia)
                last_upload_percent = [0]
                async def upload_progress(current, total):
                    percent = int((current / total) * 100)
                    # Mostrar solo cada 10%
                    if percent - last_upload_percent[0] >= 10:
                        mb_current = current / (1024**2)
                        mb_total = total / (1024**2)
                        logger.info(f"📤 Subida: {percent}% ({mb_current:.1f}/{mb_total:.1f} MB)")
                        last_upload_percent[0] = percent
                
                # Enviar como documento (archivo)
                await callback_query.message.reply_document(
                    document=str(output_path),
                    caption=caption,
                    progress=upload_progress
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
        return
    
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
