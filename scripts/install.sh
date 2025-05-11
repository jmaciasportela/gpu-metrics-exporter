# -------------------------------------------------------------------------- #
# Copyright 2002-2025, OpenNebula Project, OpenNebula Systems                #
#                                                                            #
# Licensed under the Apache License, Version 2.0 (the "License"); you may    #
# not use this file except in compliance with the License. You may obtain    #
# a copy of the License at                                                   #
#                                                                            #
# http://www.apache.org/licenses/LICENSE-2.0                                 #
#                                                                            #
# Unless required by applicable law or agreed to in writing, software        #
# distributed under the License is distributed on an "AS IS" BASIS,          #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.   #
# See the License for the specific language governing permissions and        #
# limitations under the License.                                             #
#-----

#!/bin/bash

set -e
INSTALL_DIR="/opt/gpu-gateway-exporter"
VENV_DIR="$INSTALL_DIR/venv"

if [[ "$EUID" -ne 0 ]]; then
  echo "This is script should be executed as root." >&2
  exit 1
fi

echo "🔍 Comprobando Python y entorno virtual..."

# Detectar distribución
DISTRO=$(awk -F= '/^ID=/{print tolower($2)}' /etc/os-release | tr -d '"')

# Funciones utilitarias
function ask_to_install() {
  local package_name="$1"
  echo
  read -p "¿Deseas instalar '$package_name'? [Y/n]: " choice
  case "$choice" in
    [Yy]* | "") return 0 ;;
    *) echo "⛔ No se instalará '$package_name'"; return 1 ;;
  esac
}

function install_package() {
  local pkg="$1"
  echo "🔧 Instalando paquete: $pkg"

  case "$DISTRO" in
    ubuntu|debian)
      sudo apt update
      sudo apt install -y "$pkg"
      ;;
    almalinux|rhel|centos|rocky)
      sudo dnf install -y "$pkg"
      ;;
    *)
      echo "❌ Distribución '$DISTRO' no soportada automáticamente."
      exit 1
      ;;
  esac
}

# 1. Verificar python3
if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ Python 3 no está instalado."
  if ask_to_install "python3"; then
    install_package "python3"
  else
    exit 1
  fi
else
  echo "✅ Python 3 está instalado."
fi

# 2. Verificar venv + ensurepip
echo "🔍 Verificando disponibilidad de venv y ensurepip..."

CREATE_TEST_VENV=false
if ! python3 -m venv --help >/dev/null 2>&1; then
  CREATE_TEST_VENV=true
fi

# En sistemas Debian-like, venv necesita el paquete python3-venv
if $CREATE_TEST_VENV; then
  if [[ "$DISTRO" == "ubuntu" || "$DISTRO" == "debian" ]]; then
    echo "❌ El módulo 'venv' no está disponible. Falta el paquete 'python3-venv'."
    if ask_to_install "python3-venv"; then
      install_package "python3-venv"
    else
      exit 1
    fi
  elif [[ "$DISTRO" =~ almalinux|rhel|centos|rocky ]]; then
    echo "❌ Módulo 'venv' no disponible. Asegúrate de tener 'python3' completo instalado."
    if ask_to_install "python3"; then
      install_package "python3"
    else
      exit 1
    fi
  else
    echo "❌ Distribución desconocida. Instala 'venv' manualmente."
    exit 1
  fi
else
  echo "✅ Módulo 'venv' disponible."
fi

# 3. Validar que se puede crear un entorno virtual real (con ensurepip)
echo "🧪 Validando creación de entorno virtual..."
TEMP_ENV=".test_venv_check"
rm -rf "$TEMP_ENV"

if ! python3 -m venv "$TEMP_ENV"; then
  echo "❌ Error: El entorno virtual no se pudo crear. Asegúrate de tener 'ensurepip'."
  echo "🔁 En sistemas Debian, eso lo resuelve instalar 'python3-venv'."
  exit 1
else
  echo "✅ Entorno virtual creado correctamente."
  rm -rf "$TEMP_ENV"
fi

echo
echo "🎉 Todo listo: Python 3 y virtualenv están configurados correctamente."

echo "Copy files..."
mkdir -p "$INSTALL_DIR"
rsync -rtvua ../exporter/* "$INSTALL_DIR" >/dev/null 2>&1
rsync -rtvua ../.env "$INSTALL_DIR" >/dev/null 2>&1
rsync -rtvua ../scripts/run.sh "$INSTALL_DIR" >/dev/null 2>&1
rsync -rtvua ../systemd/gpu-gateway-exporter.service "$INSTALL_DIR" >/dev/null 2>&1

cd "$INSTALL_DIR"

echo "Create Python3 Virtual Env..."
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

echo "Install project dependencies..."
pip install --upgrade pip
pip install -r "$INSTALL_DIR/requirements.txt"

echo "Install systemd service..."
cp "gpu-gateway-exporter.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable gpu-gateway-exporter
systemctl start gpu-gateway-exporter

echo "Install completed."
