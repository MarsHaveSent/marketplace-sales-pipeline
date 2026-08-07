# Сервер: аренда и базовая настройка

## Провайдер

Selectel Cloud, Ubuntu 24.04 LTS, 4 vCPU / 8 GB RAM / 80 GB SSD.

При создании сервера в панели Selectel:

- сеть — сразу подключить публичный ("белый") IP, не floating, чтобы не донастраивать отдельным шагом
- SSH-ключ — свой публичный ключ, не пароль
- Security Groups (файрвол на уровне облака, отдельно от UFW внутри сервера) — разрешить входящие 22 (SSH), 5432 (Postgres), 3000 (Metabase)

## SSH-ключ

Сгенерирован локально: `ssh-keygen -t ed25519 -f ~/.ssh/da_final_project -C "da-final-project"`. Публичный `*.pub` идёт в панель провайдера при создании сервера, приватный остаётся только на локальной машине.

## Базовая настройка сервера

Выполняется один раз через `infra/bootstrap-server.sh`, от root, сразу после создания сервера:

```
ssh -i ~/.ssh/da_final_project root@<IP> 'bash -s' < infra/bootstrap-server.sh
```

Скрипт делает:

- `apt update && upgrade`
- создаёт пользователя `deploy` с sudo, копирует ему `authorized_keys` от root
- ставит и включает UFW (22/5432/3000)
- ставит Docker Engine + Compose plugin, добавляет `deploy` в группу `docker`
- отключает вход по SSH под root и по паролю (только ключ)

После первого прогона: проверить вход под `deploy` в отдельной сессии, и только потом закрывать root-сессию. Если апдейт затронул ядро — перезагрузить сервер (`test -f /var/run/reboot-required`) и после перезагрузки заново проверить `deploy`-доступ, `systemctl is-active docker`, `sudo ufw status`.

Дальнейшая работа с сервером — только под `deploy`, root по SSH недоступен.
