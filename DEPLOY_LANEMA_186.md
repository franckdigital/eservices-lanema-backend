# Déploiement e-Services Lanema — VPS 186.241.16.135 (srv1900496, Ubuntu 24.04)

| Élément | Valeur |
|---|---|
| Backend  | `/var/www/lanema/backend` (repo `github.com/franckdigital/eservices-lanema-backend`) |
| Frontend | `/var/www/lanema/frontend` |
| venv | `/var/www/lanema/backend/venv` |
| Projet Django | `ediligence` — **Django 5.2 LTS** (épinglé : MySQL 8.0 ne supporte pas Django 6.x) |
| App Celery | `ediligence` |
| Fichier env | `/var/www/lanema/backend/.env` (chargé par `settings.py` ET par systemd) |
| Services systemd | `lanema` · `lanema-celery` · `lanema-celerybeat` |
| Gunicorn | `127.0.0.1:9011` |
| Broker | Redis `redis://localhost:6379/0` |
| DB | MySQL 8.0 (Ubuntu) — base `lanema`, user `root`, mdp `Numerix@2026`, plugin `caching_sha2_password` |
| phpMyAdmin | `https://pma.lanema-ci.com` (déjà installé) |
| PHP-FPM | `php8.3-fpm` |
| Domaine API | `https://api.lanema-ci.com` |
| Domaine Front | `https://e-services.lanema-ci.com` |

> DNS (A record → 186.241.16.135) requis : `api.lanema-ci.com`,
> `e-services.lanema-ci.com` (`pma.lanema-ci.com` déjà fait).

---

## Étape 1 — Paquets système

```bash
ssh root@186.241.16.135
apt update && apt upgrade -y
apt install -y \
  python3 python3-venv python3-dev python3-pip \
  build-essential cmake pkg-config \
  git curl ufw \
  redis-server \
  tesseract-ocr poppler-utils \
  libjpeg-dev zlib1g-dev libpng-dev libgl1 libglib2.0-0
```
(MySQL, PHP, Nginx, phpMyAdmin déjà installés.)

---

## Étape 2 — Redis

```bash
systemctl enable --now redis-server
redis-cli ping                     # -> PONG
```

---

## Étape 3 — MySQL : mot de passe root + base

```bash
sudo mysql        # (ou: mysql -u root -p  si root a déjà un mot de passe)
```
```sql
ALTER USER 'root'@'localhost' IDENTIFIED WITH caching_sha2_password BY 'Numerix@2026';
CREATE DATABASE IF NOT EXISTS lanema CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
FLUSH PRIVILEGES;
EXIT;
```
Vérif (TCP, comme Django) :
```bash
mysql -u root -p'Numerix@2026' -h 127.0.0.1 -e "SELECT VERSION(), CURRENT_USER();"
```
Import d'un dump éventuel : `mysql -u root -p lanema < /root/backup_lanema.sql`

---

## Étape 4 — Code

```bash
mkdir -p /var/www/lanema
cd /var/www/lanema
git clone https://github.com/franckdigital/eservices-lanema-backend.git backend
cd /var/www/lanema/backend
```

---

## Étape 5 — Virtualenv + dépendances

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip wheel
pip install -r requirements.txt          # requirements.txt épingle Django>=5.2,<6.0
pip install gunicorn

python -m django --version               # doit afficher 5.2.x
```

---

## Étape 6 — Fichier `.env`

```bash
cat > /var/www/lanema/backend/.env <<'EOF'
DJANGO_SETTINGS_MODULE=ediligence.settings
DB_NAME=lanema
DB_USER=root
DB_PASSWORD=Numerix@2026
DB_HOST=127.0.0.1
DB_PORT=3306
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
EOF
chmod 600 /var/www/lanema/backend/.env
```
> `settings.py` charge `.env.local` puis `.env` (via `is_file()`), donc
> `manage.py` fonctionne sans `source .env`. Les services systemd lisent aussi
> `.env` via `EnvironmentFile`.

---

## Étape 7 — Migrations / static / superuser / dossiers

```bash
cd /var/www/lanema/backend && source venv/bin/activate

python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser

mkdir -p media static logs scan_entrant
mkdir -p /var/log/celery
```

---

## Étape 8 — Service Gunicorn

```bash
cat > /etc/systemd/system/lanema.service <<'EOF'
[Unit]
Description=e-Services Lanema — Gunicorn WSGI
After=network.target mysql.service

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/var/www/lanema/backend
Environment=PATH=/var/www/lanema/backend/venv/bin
Environment=PYTHONPATH=/var/www/lanema/backend
EnvironmentFile=/var/www/lanema/backend/.env
ExecStart=/var/www/lanema/backend/venv/bin/gunicorn \
    --workers 5 \
    --bind 127.0.0.1:9011 \
    --timeout 120 \
    --access-logfile /var/www/lanema/backend/logs/access.log \
    --error-logfile /var/www/lanema/backend/logs/error.log \
    ediligence.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now lanema.service
systemctl status lanema.service
curl -I http://127.0.0.1:9011/admin/        # 301/302 attendu
```

---

## Étape 9 — Celery (worker + beat)

```bash
cat > /etc/systemd/system/lanema-celery.service <<'EOF'
[Unit]
Description=Celery Worker — e-Services Lanema
After=network.target redis-server.service mysql.service

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/var/www/lanema/backend
Environment=PATH=/var/www/lanema/backend/venv/bin
EnvironmentFile=/var/www/lanema/backend/.env
ExecStart=/var/www/lanema/backend/venv/bin/celery -A ediligence worker \
    --loglevel=info --concurrency=4 \
    --logfile=/var/log/celery/lanema-worker.log
Restart=always
RestartSec=10s

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/lanema-celerybeat.service <<'EOF'
[Unit]
Description=Celery Beat — e-Services Lanema
After=network.target redis-server.service lanema-celery.service

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/var/www/lanema/backend
Environment=PATH=/var/www/lanema/backend/venv/bin
EnvironmentFile=/var/www/lanema/backend/.env
RuntimeDirectory=celery
ExecStart=/var/www/lanema/backend/venv/bin/celery -A ediligence beat \
    --loglevel=info \
    --pidfile=/run/celery/lanema-beat.pid \
    --schedule=/var/www/lanema/backend/celerybeat-schedule \
    --logfile=/var/log/celery/lanema-beat.log
Restart=always
RestartSec=10s

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now lanema-celery.service lanema-celerybeat.service
systemctl status lanema-celery lanema-celerybeat
tail -n 30 /var/log/celery/lanema-worker.log
```

Tâches planifiées (`ediligence/celery.py`) : présence (5 min), fermeture auto 17h,
geofencing (5 min), nettoyages 02h/03h, rapport 18h, `watch_scan_folder` (30 s),
sync email DFIR (5 min).

---

## Étape 10 — Nginx : config HTTP provisoire

```bash
cat > /etc/nginx/sites-available/lanema <<'EOF'
server {
    listen 80;
    server_name api.lanema-ci.com e-services.lanema-ci.com;

    root /var/www/lanema/frontend;
    index index.html;

    location ^~ /.well-known/acme-challenge/ { root /var/www/html; }

    location /static/ { alias /var/www/lanema/backend/static/; }
    location /media/  { alias /var/www/lanema/backend/media/; }

    location /api/   { proxy_pass http://127.0.0.1:9011; proxy_set_header Host $host; proxy_set_header X-Real-IP $remote_addr; proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; proxy_set_header X-Forwarded-Proto $scheme; }
    location /admin/ { proxy_pass http://127.0.0.1:9011; proxy_set_header Host $host; proxy_set_header X-Real-IP $remote_addr; proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; proxy_set_header X-Forwarded-Proto $scheme; }

    location / { try_files $uri $uri/ /index.html; }
}
EOF

ln -sf /etc/nginx/sites-available/lanema /etc/nginx/sites-enabled/lanema
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
```

---

## Étape 11 — Pare-feu

```bash
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw enable
ufw status
```

---

## Étape 12 — Certbot (HTTPS)

```bash
apt install -y certbot python3-certbot-nginx

certbot --nginx \
  -d api.lanema-ci.com \
  -d e-services.lanema-ci.com \
  --non-interactive --agree-tos -m franckalain.ai@gmail.com --redirect

ls /etc/letsencrypt/live/          # noter le nom du dossier (ex: api.lanema-ci.com)
```

---

## Étape 13 — Nginx : config finale

```bash
cat > /etc/nginx/sites-available/lanema <<'EOF'
# ===== HTTP -> HTTPS =====
server {
    listen 80;
    server_name api.lanema-ci.com e-services.lanema-ci.com;
    location ^~ /.well-known/acme-challenge/ { root /var/www/html; }
    location / { return 301 https://$host$request_uri; }
}

# ===== FRONTEND : e-services.lanema-ci.com =====
server {
    listen 443 ssl http2;
    server_name e-services.lanema-ci.com;

    ssl_certificate     /etc/letsencrypt/live/api.lanema-ci.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.lanema-ci.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    root /var/www/lanema/frontend;
    index index.html;

    location /media/ {
        alias /var/www/lanema/backend/media/;
        expires 7d;
        include /etc/nginx/mime.types;
        add_header X-Content-Type-Options nosniff;
    }
    location / { try_files $uri $uri/ /index.html; }
}

# ===== API : api.lanema-ci.com =====
server {
    listen 443 ssl http2;
    server_name api.lanema-ci.com;

    ssl_certificate     /etc/letsencrypt/live/api.lanema-ci.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.lanema-ci.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    client_max_body_size 50M;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    location /static/ {
        alias /var/www/lanema/backend/static/;
        expires 30d;
        access_log off;
    }
    location /media/ {
        alias /var/www/lanema/backend/media/;
        expires 7d;
        include /etc/nginx/mime.types;
        add_header X-Content-Type-Options nosniff;
    }
    location / {
        proxy_pass http://127.0.0.1:9011;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port 443;
        proxy_read_timeout 120s;
    }
}
EOF

nginx -t && systemctl reload nginx
```

> Adapter `api.lanema-ci.com` dans les chemins `ssl_certificate` au nom réel du
> dossier vu à l'étape 12.

---

## Étape 14 — Renouvellement SSL

```bash
systemctl status certbot.timer
certbot renew --dry-run
```

---

## Étape 15 — Frontend

```bash
cd /var/www/lanema
git clone <REPO_FRONTEND> frontend
cd frontend
npm ci
npm run build
# si le build sort dans dist/ :  rsync -a --delete dist/ /var/www/lanema/frontend/
```

---

## Étape 16 — Vérifications finales

```bash
systemctl status lanema lanema-celery lanema-celerybeat nginx mysql redis-server php8.3-fpm
curl -I https://api.lanema-ci.com/admin/
curl -I https://e-services.lanema-ci.com/
journalctl -u lanema -n 50 --no-pager
```

---

## Mises à jour ultérieures

```bash
cd /var/www/lanema/backend && source venv/bin/activate
git pull origin master
pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput
systemctl restart lanema lanema-celery lanema-celerybeat
```

Script `/var/www/lanema/backend/deploy.sh` :

```bash
#!/bin/bash
set -e
cd /var/www/lanema/backend
source venv/bin/activate
git pull origin master
pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput
systemctl restart lanema lanema-celery lanema-celerybeat
echo "Deploy OK"
```

---

## Aide-mémoire services

```bash
systemctl status  lanema lanema-celery lanema-celerybeat
systemctl restart lanema                 # API / Gunicorn
systemctl restart lanema-celery          # Worker Celery
systemctl restart lanema-celerybeat      # Scheduler Celery

journalctl -u lanema -f
tail -f /var/log/celery/lanema-worker.log
tail -f /var/log/celery/lanema-beat.log
tail -f /var/www/lanema/backend/logs/error.log
```

---

## Notes / pièges rencontrés

- **`.env` vs `.env.local`** : `settings.py` a été modifié pour charger `.env`
  (via `is_file()`, pour ne pas confondre avec le dossier venv `backend/.env/`).
- **root MySQL en `auth_socket`** → provoque `ERROR 1698` / `1045` en TCP.
  Corrigé par `ALTER USER ... IDENTIFIED WITH caching_sha2_password`.
- **Django 6.x exige MySQL ≥ 8.4** (`NotSupportedError`). MySQL 8.0 d'Ubuntu →
  Django épinglé à `>=5.2,<6.0` dans `requirements.txt` (5.2 LTS, support 2028).
- **Dépôt APT MySQL Oracle** : clé GPG expirée (`EXPKEYSIG`). Non utilisé —
  on reste sur le paquet MySQL 8.0 d'Ubuntu (patché jusqu'en 2029).
```
