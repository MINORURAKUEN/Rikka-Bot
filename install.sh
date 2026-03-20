#!/data/data/com.termux/files/usr/bin/bash

# Script de instalación automática para el Bot de Videos de Telegram en Termux
# Autor: Tu Nombre
# Fecha: 2026

echo "════════════════════════════════════════════════"
echo "   🎬 Instalador del Bot de Videos de Telegram"
echo "════════════════════════════════════════════════"
echo ""

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para imprimir mensajes
print_message() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Verificar si estamos en Termux
if [ ! -d "/data/data/com.termux" ]; then
    print_error "Este script debe ejecutarse en Termux"
    exit 1
fi

print_success "Ejecutando en Termux"
echo ""

# Paso 1: Actualizar paquetes
print_message "Actualizando paquetes de Termux..."
pkg update -y && pkg upgrade -y
if [ $? -eq 0 ]; then
    print_success "Paquetes actualizados"
else
    print_error "Error actualizando paquetes"
    exit 1
fi
echo ""

# Paso 2: Instalar Python
print_message "Instalando Python..."
pkg install python -y
if [ $? -eq 0 ]; then
    print_success "Python instalado: $(python --version)"
else
    print_error "Error instalando Python"
    exit 1
fi
echo ""

# Paso 3: Instalar FFmpeg
print_message "Instalando FFmpeg (esto puede tardar unos minutos)..."
pkg install ffmpeg -y
if [ $? -eq 0 ]; then
    print_success "FFmpeg instalado: $(ffmpeg -version | head -n 1)"
else
    print_error "Error instalando FFmpeg"
    exit 1
fi
echo ""

# Paso 4: Instalar dependencias adicionales
print_message "Instalando dependencias adicionales..."
pkg install libjpeg-turbo libpng -y
print_success "Dependencias adicionales instaladas"
echo ""

# Paso 5: Crear directorio del proyecto
print_message "Creando directorio del proyecto..."
PROJECT_DIR="$HOME/telegram-video-bot"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"
print_success "Directorio creado: $PROJECT_DIR"
echo ""

# Paso 6: Verificar si los archivos del bot están presentes
if [ ! -f "telegram_video_bot.py" ]; then
    print_warning "No se encontró telegram_video_bot.py en el directorio actual"
    print_message "Por favor, copia los archivos del bot a: $PROJECT_DIR"
    print_message "Archivos necesarios:"
    echo "  - telegram_video_bot.py"
    echo "  - requirements.txt"
    echo ""
    print_message "Puedes continuar la instalación después de copiar los archivos"
    exit 0
fi

# Paso 7: Instalar dependencias de Python
print_message "Instalando dependencias de Python..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    if [ $? -eq 0 ]; then
        print_success "Dependencias de Python instaladas"
    else
        print_error "Error instalando dependencias de Python"
        exit 1
    fi
else
    print_warning "No se encontró requirements.txt"
    print_message "Instalando manualmente..."
    pip install python-telegram-bot==20.7
fi
echo ""

# Paso 8: Configurar token
print_message "Configuración del token del bot de Telegram"
echo ""
echo "════════════════════════════════════════════════"
echo "   📱 Cómo obtener tu token de BotFather"
echo "════════════════════════════════════════════════"
echo ""
echo "1. Abre Telegram y busca: @BotFather"
echo "2. Envía el comando: /newbot"
echo "3. Sigue las instrucciones:"
echo "   - Nombre del bot: Mi Bot de Videos"
echo "   - Username: mivideobot (debe terminar en 'bot')"
echo "4. BotFather te dará un TOKEN como:"
echo "   123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
echo ""
echo "════════════════════════════════════════════════"
echo ""

read -p "¿Ya tienes tu token? (s/n): " has_token

if [ "$has_token" = "s" ] || [ "$has_token" = "S" ]; then
    echo ""
    read -p "Pega tu token aquí: " BOT_TOKEN
    
    if [ -z "$BOT_TOKEN" ]; then
        print_error "Token vacío"
        print_message "Puedes configurarlo más tarde con:"
        echo "  echo 'TU_TOKEN' > ~/.telegram_bot_token"
    else
        echo "$BOT_TOKEN" > ~/.telegram_bot_token
        print_success "Token guardado en ~/.telegram_bot_token"
    fi
else
    print_warning "Configura tu token más tarde con:"
    echo "  echo 'TU_TOKEN' > ~/.telegram_bot_token"
fi
echo ""

# Paso 9: Configurar permisos de almacenamiento
print_message "Configurando permisos de almacenamiento..."
termux-setup-storage
print_success "Permisos configurados (puede que se solicite confirmación)"
echo ""

# Paso 10: Instalar tmux (opcional)
print_message "¿Deseas instalar tmux para ejecutar el bot en segundo plano?"
read -p "(Recomendado) (s/n): " install_tmux

if [ "$install_tmux" = "s" ] || [ "$install_tmux" = "S" ]; then
    pkg install tmux -y
    print_success "tmux instalado"
    echo ""
    print_message "Para usar tmux:"
    echo "  tmux new -s videobot    # Crear sesión"
    echo "  Ctrl+B, luego D         # Separar de sesión"
    echo "  tmux attach -t videobot # Volver a la sesión"
fi
echo ""

# Paso 11: Crear script de inicio rápido
print_message "Creando script de inicio rápido..."
cat > "$PROJECT_DIR/start.sh" << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd ~/telegram-video-bot
python telegram_video_bot.py
EOF

chmod +x "$PROJECT_DIR/start.sh"
print_success "Script creado: $PROJECT_DIR/start.sh"
echo ""

# Paso 12: Resumen final
echo "════════════════════════════════════════════════"
echo "   ✅ INSTALACIÓN COMPLETADA"
echo "════════════════════════════════════════════════"
echo ""
print_success "Todo instalado correctamente!"
echo ""
print_message "Para iniciar el bot:"
echo "  cd ~/telegram-video-bot"
echo "  python telegram_video_bot.py"
echo ""
print_message "O usa el script de inicio rápido:"
echo "  ~/telegram-video-bot/start.sh"
echo ""

if [ "$install_tmux" = "s" ] || [ "$install_tmux" = "S" ]; then
    print_message "Para ejecutar en segundo plano:"
    echo "  tmux new -s videobot"
    echo "  ~/telegram-video-bot/start.sh"
    echo ""
fi

print_warning "IMPORTANTE:"
echo "  - Asegúrate de haber configurado tu token en:"
echo "    ~/.telegram_bot_token"
echo ""
echo "  - Verifica la instalación:"
echo "    python --version"
echo "    ffmpeg -version"
echo ""

print_message "Comandos útiles del bot:"
echo "  /start       - Iniciar el bot"
echo "  /compress    - Comprimir video"
echo "  /thumbnail   - Añadir portada"
echo "  /subtitles   - Quemar subtítulos"
echo "  /extract_audio - Extraer audio"
echo ""

print_message "¿Deseas iniciar el bot ahora? (s/n): "
read -p "" start_now

if [ "$start_now" = "s" ] || [ "$start_now" = "S" ]; then
    if [ -f "$HOME/.telegram_bot_token" ]; then
        echo ""
        print_success "Iniciando el bot..."
        echo ""
        python "$PROJECT_DIR/telegram_video_bot.py"
    else
        print_error "Token no configurado. Configúralo primero:"
        echo "  echo 'TU_TOKEN' > ~/.telegram_bot_token"
    fi
else
    print_message "¡Perfecto! Ejecuta el bot cuando estés listo."
fi

echo ""
echo "════════════════════════════════════════════════"
echo "   📚 Documentación en README.md"
echo "════════════════════════════════════════════════"
