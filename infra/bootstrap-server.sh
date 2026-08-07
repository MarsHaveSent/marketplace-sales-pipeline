#!/usr/bin/env bash
# Первичная настройка чистого Ubuntu-сервера. Запускать один раз от root
# сразу после создания сервера (SSH-ключ root уже должен быть на сервере).
set -euo pipefail

DEPLOY_USER="deploy"

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get upgrade -y -o Dpkg::Options::='--force-confold'
apt-get install -y ufw

adduser --disabled-password --gecos "" "$DEPLOY_USER"
usermod -aG sudo "$DEPLOY_USER"
mkdir -p "/home/$DEPLOY_USER/.ssh"
cp /root/.ssh/authorized_keys "/home/$DEPLOY_USER/.ssh/authorized_keys"
chown -R "$DEPLOY_USER:$DEPLOY_USER" "/home/$DEPLOY_USER/.ssh"
chmod 700 "/home/$DEPLOY_USER/.ssh"
chmod 600 "/home/$DEPLOY_USER/.ssh/authorized_keys"

ufw allow 22/tcp
ufw allow 5432/tcp
ufw allow 3000/tcp
ufw --force enable

curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
sh /tmp/get-docker.sh
usermod -aG docker "$DEPLOY_USER"
systemctl enable --now docker

# Отключаем root по SSH и вход по паролю — только ключ.
# На Ubuntu 24.04 (cloud-init) PasswordAuthentication дополнительно
# переопределяется в sshd_config.d/50-cloud-init.conf, который
# подключается раньше основного файла и потому выигрывает — правим оба места.
sed -i 's/^PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/^PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config.d/50-cloud-init.conf 2>/dev/null || true
sshd -t
systemctl restart ssh

echo "Готово. Из ДРУГОЙ сессии проверить вход под $DEPLOY_USER, и только потом закрывать эту root-сессию."
echo "Если apt upgrade затронул ядро — понадобится reboot (проверить: test -f /var/run/reboot-required)."
