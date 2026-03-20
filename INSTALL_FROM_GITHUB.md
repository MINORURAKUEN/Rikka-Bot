# 🚀 Instalación Rápida desde GitHub

## 📥 Instalación en Termux (Desde GitHub)

### Paso 1: Actualizar Termux
```bash
pkg update -y && pkg upgrade -y
```

### Paso 2: Instalar Git
```bash
pkg install git -y
```

### Paso 3: Instalar Dependencias
```bash
# Instalar Python
pkg install python -y

# Instalar FFmpeg (para procesamiento de videos)
pkg install ffmpeg -y

# Instalar herramientas de descarga
pkg install megatools wget curl -y

# Dependencias adicionales
pkg install libjpeg-turbo libpng -y
```

### Paso 4: Clonar el Repositorio
```bash
# Navegar al directorio home
cd ~

# Clonar el repositorio (reemplaza con tu URL de GitHub)
git clone https://github.com/TU_USUARIO/TU_REPOSITORIO.git telegram-video-bot

# Entrar al directorio
cd telegram-video-bot
```

### Paso 5: Instalar Dependencias de Python
```bash
pip install -r requirements.txt
```

### Paso 6: Configurar el Token del Bot

#### Obtener Token de BotFather:
1. Abre Telegram
2. Busca: **@BotFather**
3. Envía: `/newbot`
4. Sigue las instrucciones:
   - Nombre: `Mi Bot de Videos`
   - Username: `mivideobot` (debe terminar en 'bot')
5. Copia el **TOKEN** que te da

#### Guardar el Token:
```bash
echo "TU_TOKEN_AQUI" > ~/.telegram_bot_token
```

Reemplaza `TU_TOKEN_AQUI` con el token real que obtuviste de BotFather.

### Paso 7: Ejecutar el Bot
```bash
python telegram_video_bot.py
```

Si todo está bien, verás:
```
🤖 Bot iniciado correctamente
Presiona Ctrl+C para detener
```

---

## 🎯 Instalación con un Solo Comando

Copia y pega este comando completo en Termux:

```bash
pkg update -y && pkg upgrade -y && pkg install git python ffmpeg megatools wget curl libjpeg-turbo libpng -y && cd ~ && git clone https://github.com/TU_USUARIO/TU_REPOSITORIO.git telegram-video-bot && cd telegram-video-bot && pip install -r requirements.txt && echo "Instalación completada. Ahora configura tu token con: echo 'TU_TOKEN' > ~/.telegram_bot_token"
```

**Importante:** Reemplaza `TU_USUARIO/TU_REPOSITORIO` con tu URL de GitHub.

---

## 🔄 Actualizar el Bot

Si haces cambios en GitHub y quieres actualizar tu bot:

```bash
cd ~/telegram-video-bot
git pull
pip install -r requirements.txt
python telegram_video_bot.py
```

---

## ✅ Verificar Instalación

### Verificar que todo esté instalado:
```bash
# Python
python --version

# FFmpeg
ffmpeg -version

# Megatools
megadl --version

# wget
wget --version
```

### Verificar archivos del bot:
```bash
ls -la ~/telegram-video-bot
```

Deberías ver:
- `telegram_video_bot.py`
- `requirements.txt`
- `README.md`
- Y otros archivos del repositorio

---

## 🎮 Uso Rápido

### 1. Iniciar el Bot
```bash
cd ~/telegram-video-bot
python telegram_video_bot.py
```

### 2. En Telegram
1. Busca tu bot: `@mivideobot`
2. Presiona **START**
3. Usa los comandos:

**Procesamiento de Videos:**
- `/compress` - Comprimir video
- `/thumbnail` - Añadir portada
- `/subtitles` - Quemar subtítulos
- `/extract_audio` - Extraer audio

**Descargas:**
- Pega directamente enlaces de:
  - 🔷 MEGA (mega.nz)
  - 🔶 MediaFire (mediafire.com)

---

## 🔧 Ejecutar en Segundo Plano

### Con tmux:
```bash
# Instalar tmux
pkg install tmux -y

# Crear sesión
tmux new -s videobot

# Dentro de tmux, ejecutar:
cd ~/telegram-video-bot
python telegram_video_bot.py

# Separar de la sesión: Ctrl+B, luego D

# Volver a la sesión:
tmux attach -t videobot
```

### Auto-inicio:
```bash
# Crear script de inicio
cat > ~/start-bot.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd ~/telegram-video-bot
python telegram_video_bot.py
EOF

chmod +x ~/start-bot.sh

# Agregar al .bashrc (opcional)
echo '~/start-bot.sh &' >> ~/.bashrc
```

---

## 🆘 Solución de Problemas

### "No such file or directory"
```bash
# Verifica que estás en el directorio correcto
pwd
cd ~/telegram-video-bot
```

### "Permission denied"
```bash
chmod +x telegram_video_bot.py
```

### "Module not found"
```bash
pip install -r requirements.txt --upgrade
```

### "FFmpeg not found"
```bash
pkg install ffmpeg -y
```

### "megatools not found"
```bash
pkg install megatools -y
```

### Bot no responde
1. Verifica el token: `cat ~/.telegram_bot_token`
2. Verifica que el bot esté ejecutándose
3. Presiona START en Telegram
4. Revisa los logs en Termux

---

## 📦 Estructura del Repositorio

```
telegram-video-bot/
├── telegram_video_bot.py    # Bot principal
├── requirements.txt          # Dependencias Python
├── README.md                 # Documentación completa
├── QUICK_START.md           # Guía de inicio rápido
├── FAQ.md                   # Preguntas frecuentes
├── ADVANCED_CONFIG.md       # Configuración avanzada
└── install.sh               # Script de instalación
```

---

## 🌟 Características

✅ **Procesamiento de Videos:**
- Compresión con 4 niveles de calidad
- Añadir portadas personalizadas
- Quemar subtítulos
- Extraer audio a MP3

✅ **Descargas:**
- MEGA (mega.nz)
- MediaFire (mediafire.com)
- Detección automática del servicio
- Soporte para todos los formatos

✅ **Optimizado para Termux:**
- Instalación sencilla
- Bajo consumo de recursos
- Funciona en segundo plano

---

## 📚 Documentación

- **README.md** - Documentación completa
- **QUICK_START.md** - Inicio en 5 minutos
- **FAQ.md** - Preguntas frecuentes
- **ADVANCED_CONFIG.md** - Personalización avanzada

---

## 🤝 Contribuir

Si encuentras bugs o quieres agregar funcionalidades:

1. Haz fork del repositorio
2. Crea una rama: `git checkout -b mi-nueva-funcionalidad`
3. Haz commit: `git commit -m 'Agregar nueva funcionalidad'`
4. Push: `git push origin mi-nueva-funcionalidad`
5. Abre un Pull Request

---

## 📞 Soporte

- Revisa **FAQ.md** para problemas comunes
- Abre un **Issue** en GitHub
- Lee la documentación completa en **README.md**

---

## 🎉 ¡Listo!

Tu bot está funcionando desde GitHub. Ahora puedes:

✅ Comprimir videos
✅ Añadir portadas
✅ Quemar subtítulos
✅ Extraer audio
✅ Descargar de MEGA
✅ Descargar de MediaFire

**Todo desde tu Android con Termux 🚀**

---

## 💡 Tips

- Usa `git pull` para actualizar el bot
- Guarda tu token de forma segura
- Revisa los logs si hay problemas
- Usa tmux para ejecución en segundo plano
- Lee ADVANCED_CONFIG.md para más funciones

**¡Disfruta tu bot! 🎬📥**
