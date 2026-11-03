#!/usr/bin/env bash
# Actualiza el sitio en la VM con lo último de la rama main. Lo corre setup_server.sh la
# primera vez y GitHub Actions en cada push a main.
set -euo pipefail

cd /srv/koza-ttp
git fetch --quiet origin main
git reset --hard origin/main

env/bin/pip install --quiet -r requirements.txt
env/bin/python manage.py migrate --noinput
env/bin/python manage.py collectstatic --noinput --verbosity 0
env/bin/python manage.py translate_site --compile-only

sudo systemctl restart koza-ttp
echo "Desplegado $(git rev-parse --short HEAD)"
