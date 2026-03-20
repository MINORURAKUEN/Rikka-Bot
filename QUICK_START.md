# ⚡ Inicio Rápido - Bot de Videos para Telegram

## 🎯 En 5 Minutos

### 1️⃣ Instalar Termux
- Descarga Termux desde F-Droid o Google Play
- Abre Termux

### 2️⃣ Ejecutar Instalación Automática
```bash
# Copia y pega estos comandos uno por uno:

# Actualizar paquetes
pkg update -y && pkg upgrade -y

# Instalar dependencias básicas
pkg install python ffmpeg -y

# Crear directorio
mkdir -p ~/telegram-video-bot && cd ~/telegram-video-bot

# Copiar archivos del bot aquí (telegram_video_bot.py, requirements.txt)

# Instalar dependencias de Python
pip install python-telegram-bot==20.7
```

### 3️⃣ Crear Bot en Telegram
1. Abre Telegram
2. Busca: **@BotFather**
3. Envía: `/newbot`
4. Nombre: `Mi Bot de Videos`
5. Username: `mivideobot` ← debe terminar en 'bot'
6. Copia el **TOKEN** que te da (ejemplo: `123456789:ABC-DEF1234...`)

### 4️⃣ Configurar Token
```bash
# Pega tu token aquí (reemplaza el ejemplo):
echo "123456789:ABC-DEF1234ghIJKL-zyx57W2v1u123ew11" > ~/.telegram_bot_token
```

### 5️⃣ Ejecutar Bot
```bash
cd ~/telegram-video-bot
python telegram_video_bot.py
```

Verás:
```
🤖 Bot iniciado correctamente
Presiona Ctrl+C para detener
```

### 6️⃣ Usar el Bot
1. Abre Telegram
2. Busca tu bot por el username (`@mivideobot`)
3. Presiona **START**
4. Envía un video
5. ¡Listo! 🎉

---

## 🎬 Ejemplos de Uso

### Comprimir un Video
```
Usuario: /compress
Bot: 📹 Envíame el video
Usuario: [envía video.mp4]
Bot: Selecciona calidad:
     🔴 Baja | 🟡 Media | 🟢 Alta | ⭐ Ultra
Usuario: [click en 🟡 Media]
Bot: ⚙️ Comprimiendo...
Bot: ✅ [video comprimido]
     📊 Original: 150MB
     📊 Comprimido: 45MB
     📉 Reducción: 70%
```

### Añadir Portada
```
Usuario: /thumbnail
Bot: 🖼️ Envíame el video
Usuario: [envía video.mp4]
Bot: Ahora envía la imagen
Usuario: [envía portada.jpg]
Bot: 🖼️ Añadiendo portada...
Bot: ✅ [video con portada]
```

### Quemar Subtítulos
```
Usuario: /subtitles
Bot: 📝 Envíame el video
Usuario: [envía video.mp4]
Bot: Ahora envía los subtítulos
Usuario: [envía subtitulos.srt]
Bot: 📝 Quemando subtítulos...
Bot: ✅ [video con subtítulos]
```

### Extraer Audio
```
Usuario: /extract_audio
Bot: 🎵 Envíame el video
Usuario: [envía video.mp4]
Bot: 🎵 Extrayendo audio...
Bot: ✅ [audio.mp3]
```

---

## 🔥 Comandos Más Usados

| Comando | Descripción | Ejemplo |
|---------|-------------|---------|
| `/start` | Iniciar bot | `/start` |
| `/help` | Ver ayuda | `/help` |
| `/compress` | Comprimir video | `/compress` → enviar video |
| `/thumbnail` | Añadir portada | `/thumbnail` → video → imagen |
| `/subtitles` | Quemar subs | `/subtitles` → video → .srt |
| `/extract_audio` | Extraer MP3 | `/extract_audio` → video |

---

## 💾 Niveles de Compresión

| Nivel | CRF | Calidad | Tamaño | Velocidad | Uso Recomendado |
|-------|-----|---------|--------|-----------|-----------------|
| 🔴 Baja | 28 | Aceptable | Muy pequeño | Rápida | WhatsApp, compartir rápido |
| 🟡 Media | 23 | Buena | Pequeño | Media | Uso general, redes sociales |
| 🟢 Alta | 20 | Excelente | Moderado | Lenta | YouTube, archivos importantes |
| ⭐ Ultra | 18 | Premium | Grande | Muy lenta | Proyectos profesionales |

---

## 🛠️ Solución Rápida de Problemas

### ❌ Error: "FFmpeg no instalado"
```bash
pkg install ffmpeg -y
```

### ❌ Error: "Token no encontrado"
```bash
# Verifica el archivo:
cat ~/.telegram_bot_token

# Si está vacío, créalo de nuevo:
echo "TU_TOKEN" > ~/.telegram_bot_token
```

### ❌ Bot no responde
1. ¿Está ejecutándose? (debe decir "Bot iniciado")
2. ¿Presionaste START en Telegram?
3. ¿El token es correcto?

### ❌ "Out of memory"
- Cierra otras apps
- Usa compresión "Baja"
- Procesa videos más cortos

### ❌ Video muy lento
- Usa preset "Baja" o "Media"
- Carga tu teléfono
- Cierra apps en segundo plano

---

## 📋 Checklist de Instalación

- [ ] Termux instalado y actualizado
- [ ] Python instalado (`python --version`)
- [ ] FFmpeg instalado (`ffmpeg -version`)
- [ ] Bot creado en @BotFather
- [ ] Token guardado en `~/.telegram_bot_token`
- [ ] Archivos del bot en `~/telegram-video-bot/`
- [ ] Dependencias instaladas (`pip list | grep telegram`)
- [ ] Bot ejecutándose
- [ ] Probado con `/start` en Telegram

---

## 🚀 Siguiente Nivel

### Ejecutar en Segundo Plano
```bash
# Instalar tmux
pkg install tmux -y

# Crear sesión
tmux new -s videobot

# Ejecutar bot
python telegram_video_bot.py

# Separar: Ctrl+B, luego D
# Volver: tmux attach -t videobot
```

### Auto-inicio
```bash
# Crear script
cat > ~/start-bot.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd ~/telegram-video-bot
python telegram_video_bot.py
EOF

chmod +x ~/start-bot.sh

# Ejecutar al abrir Termux
echo '~/start-bot.sh' >> ~/.bashrc
```

### Personalizar
Ver `ADVANCED_CONFIG.md` para:
- Cambiar niveles de compresión
- Añadir nuevas funciones
- Personalizar mensajes
- Limitar usuarios
- Y mucho más...

---

## 📚 Recursos Adicionales

- **README.md** - Documentación completa
- **FAQ.md** - Preguntas frecuentes
- **ADVANCED_CONFIG.md** - Configuración avanzada

---

## 🎉 ¡Listo!

Tu bot está funcionando. Ahora puedes:

✅ Comprimir videos para ahorrar espacio
✅ Añadir portadas profesionales
✅ Quemar subtítulos permanentemente
✅ Extraer audio de cualquier video
✅ Todo desde Telegram en tu Android

**¡Disfruta tu nuevo bot! 🎬✨**

---

## 💡 Tips Rápidos

- Envía videos directamente sin comando = compresión automática
- Nivel "Media" es el mejor balance calidad/tamaño
- Para WhatsApp, usa nivel "Baja" o "Media"
- Portadas JPG de 1920x1080 funcionan mejor
- Subtítulos SRT son los más compatibles
- Audio se extrae a MP3 192kbps

## ⚠️ Recordatorios

- No compartas tu token
- Limpia archivos viejos regularmente
- Videos >2GB no funcionan (límite de Telegram)
- Procesar videos consume batería

---

**¿Problemas? Revisa FAQ.md**
**¿Personalizar? Revisa ADVANCED_CONFIG.md**
