#!/usr/bin/env bash
# Prepara la VM recién creada: paquetes, swap, código, entorno virtual, gunicorn (systemd),
# nginx y certificado HTTPS. Se corre una vez, en la VM, como el usuario ubuntu:
#
#   scp -i ~/.ssh/koza_ttp_azure db.sqlite3 deploy/setup_server.sh ubuntu@<IP>:~
#   ssh -i ~/.ssh/koza_ttp_azure ubuntu@<IP> 'bash setup_server.sh'
set -euo pipefail

APP_DIR=/srv/koza-ttp
REPO=https://github.com/lespam/koza-ttp.git
BRANCH="${BRANCH:-main}"
DOMAIN="${DOMAIN:-koza-ttp.lesliedickinson.dev}"
EMAIL="${EMAIL:-lesliepbv@gmail.com}"

sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
  python3.10 python3.10-venv python3.10-dev build-essential git \
  graphviz graphviz-dev libgraphviz-dev nginx certbot python3-certbot-nginx

# 2 GB de swap: la VM B1s solo tiene 1 GB de RAM y la programación genética usa bastante
if [ ! -f /swapfile ]; then
  sudo fallocate -l 2G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
fi

sudo mkdir -p "${APP_DIR}"
sudo chown "${USER}:${USER}" "${APP_DIR}"
if [ ! -d "${APP_DIR}/.git" ]; then
  git clone --branch "${BRANCH}" "${REPO}" "${APP_DIR}"
fi
cd "${APP_DIR}"

python3.10 -m venv env
env/bin/pip install --upgrade pip wheel
env/bin/pip install -r requirements.txt

if [ ! -f .env ]; then
  IP="$(curl -s https://api.ipify.org)"
  cat > .env <<EOF
SECRET_KEY=$(env/bin/python -c 'import secrets; print(secrets.token_urlsafe(50))')
DEBUG=False
ALLOWED_HOSTS=${DOMAIN},www.${DOMAIN},${IP}
CSRF_TRUSTED_ORIGINS=https://${DOMAIN},https://www.${DOMAIN}
EOF
  chmod 600 .env
fi

# La base de datos no está en git: se sube aparte (ver arriba)
if [ -f ~/db.sqlite3 ] && [ ! -f db.sqlite3 ]; then
  mv ~/db.sqlite3 db.sqlite3
fi

sudo mkdir -p /var/log/gunicorn
sudo chown "${USER}:www-data" /var/log/gunicorn
sudo cp deploy/systemd/koza-ttp.service /etc/systemd/system/
sudo cp deploy/nginx/koza-ttp.conf /etc/nginx/sites-available/koza-ttp
sudo ln -sf /etc/nginx/sites-available/koza-ttp /etc/nginx/sites-enabled/koza-ttp
sudo rm -f /etc/nginx/sites-enabled/default
sudo systemctl daemon-reload
sudo systemctl enable koza-ttp

bash deploy/deploy.sh
sudo nginx -t && sudo systemctl reload nginx

# HTTPS: necesita que el DNS ya apunte a esta VM
if getent hosts "${DOMAIN}" | grep -q "$(curl -s https://api.ipify.org)"; then
  sudo certbot --nginx --non-interactive --agree-tos --redirect -m "${EMAIL}" \
    -d "${DOMAIN}" -d "www.${DOMAIN}"
else
  echo "El DNS de ${DOMAIN} todavía no apunta aquí; cuando lo haga, corre:"
  echo "  sudo certbot --nginx --redirect -m ${EMAIL} -d ${DOMAIN} -d www.${DOMAIN}"
fi
