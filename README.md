# 🎬 Bot de Telegram para Procesamiento de Videos en Termux

Bot completo para comprimir videos, añadir portadas, quemar subtítulos y extraer audio, optimizado para Termux en Android.

## 📋 Características

✅ **Compresión de Videos** - 4 niveles de calidad (baja, media, alta, ultra)
✅ **Añadir Portadas** - Agrega thumbnails personalizados a tus videos
✅ **Quemar Subtítulos** - Integra subtítulos permanentemente en el video
✅ **Extraer Audio** - Convierte videos a MP3
✅ **Interfaz Intuitiva** - Botones y comandos fáciles de usar
✅ **Optimizado para Termux** - Funciona perfectamente en Android

## 🚀 Instalación en Termux

### Paso 1: Actualizar Termux

```bash
pkg update && pkg upgrade -y
```

### Paso 2: Instalar dependencias

```bash
# Instalar Python
pkg install python -y

# Instalar FFmpeg (herramienta para procesar videos)
pkg install ffmpeg -y

# Instalar dependencias adicionales
pkg install libjpeg-turbo libpng -y
```

### Paso 3: Crear bot en Telegram

1. Abre Telegram y busca **@BotFather**
2. Envía `/newbot`
3. Sigue las instrucciones:
   - Nombre del bot: `Mi Bot de Videos`
   - Username: `mivideobot` (debe terminar en 'bot')
4. Guarda el **TOKEN** que te da BotFather (parecido a: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Paso 4: Configurar el bot

```bash
# Crear carpeta para el proyecto
mkdir ~/telegram-video-bot
cd ~/telegram-video-bot

# Copiar los archivos (telegram_video_bot.py y requirements.txt)
# Puedes usar termux-share para transferir archivos desde tu PC

# Instalar dependencias de Python
pip install -r requirements.txt
```

### Paso 5: Guardar el token

```bash
# Crear archivo con tu token (reemplaza YOUR_TOKEN con tu token real)
echo "123456789:ABCdefGHIjklMNOpqrsTUVwxyz" > ~/.telegram_bot_token
```

### Paso 6: Ejecutar el bot

```bash
python telegram_video_bot.py
```

Si todo funciona, verás:
```
🤖 Bot iniciado correctamente
Presiona Ctrl+C para detener
```

## 📱 Cómo Usar el Bot

### Comandos Disponibles

- `/start` - Iniciar el bot y ver bienvenida
- `/help` - Mostrar ayuda detallada
- `/compress` - Comprimir un video
- `/thumbnail` - Añadir portada a un video
- `/subtitles` - Quemar subtítulos en un video
- `/extract_audio` - Extraer audio de un video

### Ejemplos de Uso

#### 1️⃣ Comprimir un Video

1. Envía `/compress` al bot
2. Envía tu video
3. Selecciona el nivel de compresión:
   - 🔴 **Baja** - Máxima compresión, menor calidad
   - 🟡 **Media** - Balance entre tamaño y calidad
   - 🟢 **Alta** - Buena calidad, menos compresión
   - ⭐ **Ultra** - Máxima calidad, mínima compresión
4. Espera a que se procese
5. Descarga el video comprimido

#### 2️⃣ Añadir Portada

1. Envía `/thumbnail` al bot
2. Envía tu video
3. Envía la imagen que quieres como portada
4. Descarga el video con portada

#### 3️⃣ Quemar Subtítulos

1. Envía `/subtitles` al bot
2. Envía tu video
3. Envía el archivo de subtítulos (.srt, .ass, .vtt)
4. Descarga el video con subtítulos integrados

#### 4️⃣ Extraer Audio

1. Envía `/extract_audio` al bot
2. Envía tu video
3. Descarga el archivo MP3

### Atajos Rápidos

- **Comprimir directamente**: Solo envía un video sin comando, se activará la compresión automáticamente

## 🔧 Configuración Avanzada

### Ejecutar en segundo plano

Para que el bot siga funcionando después de cerrar Termux:

```bash
# Instalar tmux
pkg install tmux -y

# Crear sesión
tmux new -s videobot

# Ejecutar bot
python telegram_video_bot.py

# Separar de la sesión: Presiona Ctrl+B, luego D

# Volver a la sesión:
tmux attach -t videobot
```

### Auto-inicio al abrir Termux

```bash
# Crear script de inicio
echo '#!/data/data/com.termux/files/usr/bin/bash
cd ~/telegram-video-bot
python telegram_video_bot.py' > ~/start-bot.sh

chmod +x ~/start-bot.sh

# Agregar al .bashrc
echo '~/start-bot.sh' >> ~/.bashrc
```

### Cambiar directorio de trabajo

Por defecto, los archivos se guardan en `~/telegram_bot_files`. Para cambiarlo, edita la línea 35 en `telegram_video_bot.py`:

```python
WORK_DIR = Path.home() / 'mi_carpeta_personalizada'
```

## 🎛️ Personalización

### Ajustar niveles de compresión

Edita las líneas 52-57 en `telegram_video_bot.py`:

```python
quality_settings = {
    'low': {'crf': '28', 'preset': 'veryfast', 'bitrate': '500k'},
    'medium': {'crf': '23', 'preset': 'medium', 'bitrate': '1000k'},
    'high': {'crf': '20', 'preset': 'slow', 'bitrate': '2000k'},
    'ultra': {'crf': '18', 'preset': 'slower', 'bitrate': '3000k'}
}
```

**Parámetros:**
- `crf`: 0-51 (menor = mejor calidad, mayor tamaño)
- `preset`: veryfast, fast, medium, slow, slower (más lento = mejor compresión)
- `bitrate`: tasa de bits del video

### Cambiar calidad de audio

Línea 69:
```python
'-b:a', '128k',  # Cambia a '192k' o '256k' para mejor calidad
```

## 📊 Límites y Consideraciones

- **Tamaño máximo**: 2GB (límite de Telegram)
- **Formatos soportados**: MP4, MKV, AVI, MOV, WEBM
- **Subtítulos**: SRT, ASS, VTT
- **Tiempo de procesamiento**: Depende del tamaño del video y la potencia de tu dispositivo

## 🐛 Solución de Problemas

### "FFmpeg no está instalado"

```bash
pkg install ffmpeg -y
```

### "No se encontró el token del bot"

```bash
# Verifica que creaste el archivo correctamente
cat ~/.telegram_bot_token

# Si está vacío, vuelve a crearlo
echo "TU_TOKEN_AQUÍ" > ~/.telegram_bot_token
```

### "Error descargando video"

- Verifica tu conexión a internet
- Asegúrate de que el video no supere 2GB

### Bot no responde

```bash
# Detén el bot (Ctrl+C)
# Vuelve a ejecutar
python telegram_video_bot.py
```

### Problemas de permisos en Termux

```bash
# Permitir acceso al almacenamiento
termux-setup-storage
```

## 📈 Optimización de Rendimiento

### Para videos grandes

1. Usa el nivel de compresión **Baja** o **Media**
2. Cierra otras aplicaciones en tu dispositivo
3. Asegúrate de tener suficiente espacio de almacenamiento

### Para mejor calidad

1. Usa el nivel **Alta** o **Ultra**
2. Ten en cuenta que el procesamiento será más lento
3. El archivo resultante será más grande

## 🔒 Seguridad

- **Nunca compartas tu token** - Cualquiera con tu token puede controlar tu bot
- **Limpia archivos temporales** - Los archivos se borran automáticamente después de procesarse
- **No proceses videos confidenciales** - Los archivos pasan por los servidores de Telegram

## 📞 Soporte

Si tienes problemas:

1. Revisa los logs en Termux
2. Verifica que FFmpeg esté instalado: `ffmpeg -version`
3. Comprueba la versión de Python: `python --version` (debe ser 3.7+)
4. Revisa que las dependencias estén instaladas: `pip list`

## 🆕 Actualizaciones Futuras

Posibles mejoras:
- Conversión de formatos de video
- Recortar/editar videos
- Añadir marcas de agua
- Ajustar velocidad de reproducción
- Combinar múltiples videos

## 📝 Licencia

Este proyecto es de código abierto. Úsalo libremente y modifícalo según tus necesidades.

---

**¡Disfruta procesando tus videos! 🎥✨**
