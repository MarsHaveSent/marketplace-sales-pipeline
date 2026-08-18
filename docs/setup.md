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

## Postgres

Репозиторий клонирован на сервер в `~/marketplace-sales-pipeline`. Реальные пароли — в `infra/.env` (не в git, только на сервере), по образцу `infra/.env.example`.

```
cd ~/marketplace-sales-pipeline/infra
docker compose up -d
docker compose ps
```

Порт 5432 проброшен наружу (`0.0.0.0:5432`) и подтверждён доступным снаружи сервера — группа безопасности Selectel `default` его не блокирует, отдельно настраивать не пришлось.

## Airflow

Metadata DB — отдельная база `airflow` в том же контейнере Postgres (не второй контейнер). Init-скрипты Docker-образа Postgres срабатывают только на пустом volume, а наш уже был инициализирован под `sales` в Неделе 1, поэтому база `airflow` создана вручную один раз:

```
docker compose exec -T postgres psql -U sales_app -d sales -c "CREATE DATABASE airflow;"
```

Секреты (генерируются один раз при бутстрапе, в `infra/.env`, не в git):

- `AIRFLOW_FERNET_KEY` — шифрует пароли/connections в metadata DB; менять после старта нельзя
- `AIRFLOW_WEBSERVER_SECRET_KEY` — подпись сессий Flask
- `AIRFLOW_ADMIN_PASSWORD` — пароль веб-пользователя `admin`

Подъём:

```
docker compose build airflow-init
docker compose up airflow-init          # миграция metadata DB + создание пользователя admin, разовый прогон
docker compose up -d airflow-webserver airflow-scheduler
```

Веб-интерфейс слушает `127.0.0.1:8080` — сознательно не наружу (в отличие от Postgres и Metabase, доступ к Airflow UI не входит в сдаваемые по ТЗ доступы). Смотреть его можно через SSH-туннель:

```
ssh -i ~/.ssh/da_final_project -L 8080:localhost:8080 deploy@<IP>
```

и затем открыть `http://localhost:8080` в браузере на своей машине, пока сессия открыта. Логин — `admin`, пароль — значение `AIRFLOW_ADMIN_PASSWORD` из `infra/.env` на сервере.

DAG'и и `scripts/` примонтированы как volumes (`../dags`, `../scripts`) — правки подхватываются без пересборки образа; пересборка (`docker compose build`) нужна только при изменении `requirements-airflow.txt` или `Dockerfile`.

## Metabase

Своя БД `metabase` в том же контейнере Postgres, тем же способом, что и `airflow` (volume уже не пустой, init-скрипты не срабатывают):

```
docker compose exec -T postgres psql -U sales_app -d sales -c "CREATE DATABASE metabase;"
docker compose up -d metabase
```

Слушает `3000` наружу — порт открыт в UFW и Security Groups с самого бутстрапа. При первом заходе на `http://<IP>:3000` — мастер настройки: аккаунт админа, потом добавить вторую БД-источник — `sales` (БД `metabase`  Metabase хранит только свои дашборды/настройки).

## DataLens

Отдельный от `sales_app` read-only пользователь Postgres, только на чтение `ops.pipeline_runs` — DataLens снаружи Yandex Cloud, боевые креды туда отдавать незачем:

```
docker compose exec -T postgres psql -U sales_app -d sales \
  -c "CREATE USER datalens_ro WITH PASSWORD '<пароль из infra/.env>';" \
  -c "GRANT CONNECT ON DATABASE sales TO datalens_ro;" \
  -c "GRANT USAGE ON SCHEMA ops TO datalens_ro;" \
  -c "GRANT SELECT ON ops.pipeline_runs TO datalens_ro;"
```

Пароль — `DATALENS_RO_PASSWORD` в `infra/.env` на сервере (не в git). Подключение из DataLens — напрямую по внешнему IP сервера, порт `5432` (уже открыт, тот же порт, что и для прямого доступа к `sales`), база `sales`, пользователь `datalens_ro`.
