# ❓ Preguntas Frecuentes (FAQ)

## 🚀 Instalación y Configuración

### ¿Funciona en cualquier dispositivo Android?
Sí, siempre que puedas instalar Termux. Compatible con Android 7.0 o superior.

### ¿Necesito root?
No, el bot funciona sin necesidad de acceso root.

### ¿Cuánto espacio necesito?
Mínimo 500MB libres. Recomendado 2GB+ para procesar videos grandes.

### ¿Funciona sin conexión a internet?
Una vez instalado, el procesamiento de videos funciona offline. Solo necesitas internet para recibir/enviar archivos por Telegram.

### ¿Puedo usar mi propia cuenta de Telegram en lugar de crear un bot?
No, debes crear un bot a través de @BotFather. Tu cuenta personal no puede ser utilizada como bot.

## 💾 Procesamiento de Videos

### ¿Cuál es el tamaño máximo de video?
Telegram tiene un límite de 2GB para archivos. El bot respeta este límite.

### ¿Cuánto tarda en comprimir un video?
Depende de:
- Duración del video
- Resolución original
- Nivel de compresión seleccionado
- Potencia de tu dispositivo

Ejemplos aproximados en un dispositivo de gama media:
- Video de 1 minuto (HD): 30-60 segundos
- Video de 5 minutos (HD): 2-5 minutos
- Video de 30 minutos (HD): 15-30 minutos

### ¿Pierde mucha calidad al comprimir?
Depende del nivel seleccionado:
- **Baja**: Reducción notable, ideal para compartir rápido
- **Media**: Balance óptimo, pérdida mínima perceptible
- **Alta**: Excelente calidad, reducción moderada
- **Ultra**: Calidad casi idéntica, reducción mínima

### ¿Puedo comprimir videos 4K?
Sí, pero ten en cuenta:
- Tardará más tiempo
- Necesitas más espacio disponible
- Consumirá más batería

### ¿Se mantiene el audio al comprimir?
Sí, el audio se recodifica a 128kbps AAC (calidad estándar).

## 🖼️ Portadas y Thumbnails

### ¿Qué formato de imagen usar para la portada?
JPG o PNG. Recomendado: JPG de 1280x720 o 1920x1080.

### ¿Se puede añadir GIF como portada?
No, solo imágenes estáticas. El primer frame del GIF será usado.

### ¿La portada aumenta el tamaño del archivo?
Mínimamente (típicamente menos de 100KB).

## 📝 Subtítulos

### ¿Qué formatos de subtítulos soporta?
SRT, ASS, VTT (los más comunes).

### ¿Puedo cambiar el estilo de los subtítulos?
Actualmente usa el estilo por defecto de FFmpeg. Para personalizarlos, ver ADVANCED_CONFIG.md.

### ¿Los subtítulos quedan permanentes?
Sí, se "queman" en el video y no se pueden quitar después.

### ¿Afecta la calidad del video?
El video debe recodificarse, lo que puede causar una pequeña pérdida de calidad.

### ¿Puedo añadir múltiples pistas de subtítulos?
No actualmente, solo se puede quemar una pista.

## 🎵 Extracción de Audio

### ¿En qué formato se extrae el audio?
MP3 a 192kbps por defecto.

### ¿Puedo extraer en otros formatos?
Requiere modificación del código. Ver ADVANCED_CONFIG.md para extraer en otros formatos como AAC, FLAC, WAV, etc.

### ¿Se mantiene la calidad original del audio?
Se recodifica a MP3 192kbps, que es calidad alta para la mayoría de casos.

## 🔧 Problemas Técnicos

### "FFmpeg no está instalado"
Solución:
```bash
pkg install ffmpeg -y
```

### "No se encontró el token del bot"
Solución:
```bash
echo "TU_TOKEN_AQUÍ" > ~/.telegram_bot_token
```
Reemplaza TU_TOKEN_AQUÍ con tu token real de @BotFather.

### "Permission denied" al ejecutar el script
Solución:
```bash
chmod +x telegram_video_bot.py
# O ejecuta con python:
python telegram_video_bot.py
```

### El bot no responde a mis mensajes
Verifica:
1. El bot está ejecutándose (no cerrado)
2. El token es correcto
3. Iniciaste conversación con /start
4. Tu conexión a internet funciona

### "Out of memory" durante el procesamiento
Soluciones:
- Cierra otras aplicaciones
- Usa nivel de compresión "Baja"
- Procesa videos más cortos
- Reinicia Termux

### El video procesado no se envía
Posibles causas:
- Archivo muy grande (>2GB)
- Conexión inestable
- Token de bot inválido

Solución: Verifica el tamaño y tu conexión.

### Error: "Codec not found"
Solución: Reinstala FFmpeg:
```bash
pkg uninstall ffmpeg
pkg install ffmpeg -y
```

## ⚡ Rendimiento

### ¿Consume mucha batería?
El procesamiento de video es intensivo. Recomendaciones:
- Conecta el cargador para videos largos
- Reduce el brillo de la pantalla
- Cierra apps en segundo plano

### ¿Cómo acelerar el procesamiento?
- Usa preset "veryfast" (menor calidad)
- Reduce la resolución del video
- Usa dispositivos más potentes
- No ejecutes otras apps pesadas

### ¿Puedo procesar varios videos a la vez?
El bot procesa un video por usuario a la vez para evitar sobrecarga.

## 🔒 Seguridad y Privacidad

### ¿Mis videos son privados?
- Los archivos se procesan localmente en tu dispositivo
- Los videos pasan por servidores de Telegram
- No se almacenan en ningún servidor externo del bot
- Los archivos temporales se eliminan automáticamente

### ¿Puedo limitar quién usa el bot?
Sí, edita el código para añadir una lista de usuarios autorizados. Ver ADVANCED_CONFIG.md.

### ¿Alguien más puede acceder a mi bot?
Solo si compartes el username de tu bot. Puedes hacerlo privado limitando usuarios autorizados.

## 📊 Límites y Restricciones

### ¿Hay límite de videos por día?
No hay límite en el bot, pero Telegram puede limitar el uso intensivo.

### ¿Cuántos bots puedo crear?
BotFather permite 20 bots por cuenta de Telegram.

### ¿Puedo monetizar mi bot?
Sí, es tu bot. Puedes cobrar por el servicio si lo deseas.

## 🛠️ Personalización

### ¿Puedo cambiar los mensajes del bot?
Sí, edita las cadenas de texto en telegram_video_bot.py.

### ¿Puedo añadir más funciones?
Sí, el código es de código abierto. Ver ADVANCED_CONFIG.md para ejemplos.

### ¿Puedo cambiar el nombre del bot?
Sí, contacta a @BotFather y usa el comando /setname.

### ¿Puedo poner foto de perfil al bot?
Sí, contacta a @BotFather y usa el comando /setuserpic.

## 🌐 Integración

### ¿Puedo usarlo con grupos de Telegram?
Sí, añade el bot a un grupo. Puede procesar videos enviados en el grupo.

### ¿Funciona con canales?
Sí, si añades el bot como administrador del canal.

### ¿Puedo integrarlo con otras apps?
El bot solo funciona dentro de Telegram.

## 📱 Termux Específico

### ¿Se cierra al bloquear el teléfono?
Por defecto sí. Usa `termux-wake-lock` para evitarlo:
```bash
termux-wake-lock
```

### ¿Cómo ejecutar en segundo plano?
Usa tmux:
```bash
pkg install tmux
tmux new -s videobot
python telegram_video_bot.py
# Ctrl+B, luego D para separar
```

### ¿Se puede auto-iniciar al abrir Termux?
Sí, añade al ~/.bashrc:
```bash
echo 'cd ~/telegram-video-bot && python telegram_video_bot.py' >> ~/.bashrc
```

### ¿Funciona en Termux:API?
No es necesario, pero puedes integrarlo si deseas funciones adicionales del sistema.

## 💡 Tips y Trucos

### Atajos de comandos
En lugar de usar /compress, simplemente envía el video.

### Procesar lotes
Envía múltiples videos seguidos, se procesarán uno tras otro.

### Guardar presets favoritos
Edita el código para añadir tus configuraciones preferidas.

### Usar con scripts
Puedes crear scripts bash para procesar videos localmente:
```bash
#!/bin/bash
python -c "from telegram_video_bot import VideoProcessor; VideoProcessor.compress_video('input.mp4', 'output.mp4', 'medium')"
```

### Monitorear progreso
Mira los logs en tiempo real:
```bash
tail -f bot.log
```

## 🆘 Soporte

### ¿Dónde reportar bugs?
Verifica los logs primero:
```bash
cat bot.log
```

### ¿Cómo actualizar el bot?
1. Detén el bot (Ctrl+C)
2. Reemplaza telegram_video_bot.py
3. Reinstala dependencias si es necesario
4. Reinicia el bot

### ¿Hay versión con interfaz gráfica?
No, es solo línea de comandos (CLI).

## 📈 Mejoras Futuras

### Funciones en desarrollo
- Conversión de formatos
- Recorte de videos
- Filtros y efectos
- Marca de agua automática
- Procesamiento por lotes mejorado

### ¿Cómo contribuir?
Modifica el código, prueba tus cambios y compártelos.

## 🎓 Aprendizaje

### ¿Necesito saber programar?
No para uso básico. Para personalizaciones avanzadas, conocimientos de Python ayudan.

### ¿Dónde aprender más sobre FFmpeg?
- Documentación oficial: ffmpeg.org
- Ejemplos: ffmpeg.org/examples.html
- Wiki: trac.ffmpeg.org/wiki

### ¿Recursos para aprender Python?
- python.org/beginners
- docs.python.org/tutorial
- Telegram Bot API: core.telegram.org/bots

---

**¿No encuentras tu pregunta? Crea un issue o modifica el código! 🚀**
