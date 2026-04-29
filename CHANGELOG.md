## [0.9.0-rc.3](https://github.com/disafronov/sloths-inventory/compare/v0.9.0-rc.2...v0.9.0-rc.3) (2026-04-29)

### Features

* add index to Operation model for improved query performance ([46f2685](https://github.com/disafronov/sloths-inventory/commit/46f2685ce7c3fb32e800cc0af20ebaa95d1ba07f))
* enforce append-only semantics for Operation model ([982591f](https://github.com/disafronov/sloths-inventory/commit/982591ff1d65bc97e697de28914691093c5c21c3))
* implement permission checks for latest Operation in admin ([3f8ab2b](https://github.com/disafronov/sloths-inventory/commit/3f8ab2b0185866ce12593946714f47b454dda93f))

### Bug Fixes

* enhance Dockerfile for internationalization support ([f813b86](https://github.com/disafronov/sloths-inventory/commit/f813b860ff5ab2bdf6cb26a4ed3bcff0a2cd39d1))
* enhance fieldset handling in BaseAdmin class ([c8b134e](https://github.com/disafronov/sloths-inventory/commit/c8b134eb7be7abba1f3a255a6859b052ea95d2df))
* enhance SECRET_KEY handling in settings ([ef8fc9b](https://github.com/disafronov/sloths-inventory/commit/ef8fc9b3ad9d66b29b6e3cda25897b9c3b559724))
* implement concurrency-safe updates in Operation model ([ee5adfb](https://github.com/disafronov/sloths-inventory/commit/ee5adfb0e4dfee59b1bb5591df6c09fc7a784376))
* improve concurrency handling in Operation model ([cc75fa0](https://github.com/disafronov/sloths-inventory/commit/cc75fa0db31da92e792a6054cf2b22ef3a9f789e))
* improve database connection error handling in health check ([f2006c0](https://github.com/disafronov/sloths-inventory/commit/f2006c051840f1f86542cf90dbd2d87891e980a6))
* improve handling of None values in CurrentOperationValue ([82cbdc0](https://github.com/disafronov/sloths-inventory/commit/82cbdc0d04aaf15edf933deb0c84465313ab7654))
* improve validation logic in Operation model ([f38ccc1](https://github.com/disafronov/sloths-inventory/commit/f38ccc1aa9c3bf62ef4b2a0b74520d7e6fcb4b4a))
* optimize queryset and caching in admin views ([34cc468](https://github.com/disafronov/sloths-inventory/commit/34cc468e1dc82bb20d3f9d82630286cf8f6478b0))
* optimize queryset retrieval in admin views ([f2fc8da](https://github.com/disafronov/sloths-inventory/commit/f2fc8da90e636ab29573c391fb07e580d3077f7f))
* refine current operation retrieval in Item model ([ce2eedd](https://github.com/disafronov/sloths-inventory/commit/ce2eedd4e591219c3777ffc78bf8d2d468c32e44))
* refine database error handling in health check ([f6ae3e7](https://github.com/disafronov/sloths-inventory/commit/f6ae3e7d51bb3ab95828857208db70775e3ef22f))
* remove USE_L10N setting from settings.py ([2c0e9cd](https://github.com/disafronov/sloths-inventory/commit/2c0e9cdcb719964e1258b068a3e315f2f6c93f6c))
* update database engine in settings.py ([6ef3bff](https://github.com/disafronov/sloths-inventory/commit/6ef3bff9c6ae1fc0382646b6fdc7105de30e8e9b))
* update DEBUG setting to use environment variable ([84887f9](https://github.com/disafronov/sloths-inventory/commit/84887f93600709aeb8a6f7b8e090f9146533890a))
* update Dockerfile for development environment configuration ([50ce5c0](https://github.com/disafronov/sloths-inventory/commit/50ce5c02e604e1b15914e74cf8a0f11670ed070f))
* update Dockerfile to set ownership for source files ([940d626](https://github.com/disafronov/sloths-inventory/commit/940d6266acb51b1515ac1bdfd9ba090d8b3604f8))
* update translation function in admin.py ([5459b32](https://github.com/disafronov/sloths-inventory/commit/5459b321e1d06ab1f21da8b2dfe78c870386b5dd))

## [0.9.0-rc.2](https://github.com/disafronov/sloths-inventory/compare/v0.9.0-rc.1...v0.9.0-rc.2) (2026-04-29)

### Bug Fixes

* update entrypoint commands in Docker Compose configuration ([c2849e1](https://github.com/disafronov/sloths-inventory/commit/c2849e11b17679081f0ce517f087a96dd8dbc8bb))

## [0.9.0-rc.1](https://github.com/disafronov/sloths-inventory/compare/v0.8.3...v0.9.0-rc.1) (2026-04-29)

### Features

* introduce common utilities and test configuration for Django project ([3436fde](https://github.com/disafronov/sloths-inventory/commit/3436fdec50f446dd720153e11bfcf8d3a9af6023))

### Bug Fixes

* Potential fix for pull request finding 'CodeQL / Information exposure through an exception' ([85b977d](https://github.com/disafronov/sloths-inventory/commit/85b977d187cf9041917cd467d443d59a3a10220c))

# Changelog

All notable changes to this project will be documented in this file.

## [0.8.0] - 2025-05-18

### 🚀 Features

- Добавление поддержки интернационализации и обновление шаблонов
- Добавление миграций для обновления полей моделей в приложениях catalogs, devices и inventory
- Удаление файлов локализации для английского и русского языков
- Добавление поддержки интернационализации для моделей и локализации
- Добавление миграции для обновления опций моделей в приложении catalogs
- Обновление файлов локализации для поддержки интернационализации
- Обновление моделей для поддержки интернационализации и добавление файлов локализации
- Добавление миграций для обновления опций моделей в приложениях devices и inventory
- Обновление админки для поддержки интернационализации
- Обновление поддержки интернационализации в приложениях catalogs, devices и inventory

### 🚜 Refactor

- Удаление проверки локального запроса из функций liveness и readiness

## [0.7.0] - 2025-05-18

### 🚀 Features

- Добавление функционала управления устройствами с CRUD операциями и соответствующими шаблонами
- Добавление фабрики DeviceFactory и тестов для CRUD операций устройств
- Добавление проверки состояния приложения с помощью liveness и readiness проб
- Добавление маршрутов для проверки состояния приложения через liveness и readiness
- Замена шаблонов устройств на общий шаблон и обновление локализации
- Обновление шаблонов для управления устройствами с использованием нового общего шаблона
- Добавление функционала аутентификации с кастомными представлениями входа и выхода
- Добавление начальных миграций для приложений catalogs, devices и inventory
- Добавление тестового раннера для pytest и инициализация тестового пакета
- Добавление нового шаблона base.html
- Добавление проверки доступа к пробам liveness и readiness
- Добавление приложения health с пробами liveness и readiness
- Добавление базового админ-класса и обновление админки устройств
- Добавление полей поиска в админ-классы
- Обновление админ-класса DeviceAdmin для улучшения поиска
- Обновление админ-классов для моделей Location, Responsible и Status
- Обновление админ-класса ResponsibleAdmin для улучшения отображения
- Обновление админ-класса OperationAdmin для улучшения отображения
- Обновление админ-класса ItemAdmin для улучшения отображения
- Обновление админ-классов для улучшения структуры полей
- Обновление метода get_fieldsets в админ-классе ItemAdmin для улучшения структуры отображения
- Добавление метода _format_empty_value в базовый админ-класс для обработки пустых значений
- Добавление миксина CurrentFieldMixin в админ-класс ItemAdmin для улучшения отображения текущих полей
- Добавление миксина DeviceFieldsMixin в админ-классы ItemAdmin и OperationAdmin для улучшения поиска и фильтрации
- Добавление базовой структуры приложения с главной страницей и шаблонами
- Обновление маршрутов приложения и удаление шаблона base.html
- Обновление шаблона base.html для улучшения структуры и стилей
- Добавление маршрутов для входа и выхода, обновление шаблонов для улучшения навигации
- Удаление представлений и маршрутов для управления устройствами
- Обновление шаблонов для улучшения структуры и стилей
- Обновление маршрутов и шаблонов для улучшения пользовательского интерфейса

### 🐛 Bug Fixes

- Исправление импорта модели Device из приложения catalogs вместо текущего приложения
- CSRF_TRUSTED_ORIGINS

### 🚜 Refactor

- Объединение импортов моделей из приложений catalogs и devices
- Удаление модели Device и упрощение админ-панели
- Удаление тестов для приложений catalogs, devices, inventory и общего теста
- Rm generated tests
- Rm migrations
- Обновление конфигурации pytest для игнорирования определенных файлов
- Удаление шаблонов base.html и login.html
- Обновление шаблонов и маршрутов для устройств
- Обновление шаблона base.html для улучшения локализации и структуры
- Удаление неиспользуемого кода из приложения common

### 📚 Documentation

- Update changelog for v0.7.0

### 🧪 Testing

- Добавление тестов для проверки состояния приложения через liveness и readiness

## [0.6.4] - 2025-05-18

### 🐛 Bug Fixes

- Исправление зависимости в workflow тестов, замена 'test' на 'tests'

### 🚜 Refactor

- Улучшение тестов и удаление устаревших функций в manage.py, добавление новых тестов для конфигурации приложений и настроек Django
- Перевод тестов конфигурации приложений и настроек Django на русский язык
- Добавление приложения 'common' в тесты конфигурации Django

### 📚 Documentation

- Update changelog for v0.6.4

## [0.6.3] - 2025-05-18

### 🐛 Bug Fixes

- Rename

### 📚 Documentation

- Update changelog for v0.6.3

## [0.6.2] - 2025-05-18

### 🐛 Bug Fixes

- Rename
- Rename
- Test

### 📚 Documentation

- Update changelog for v0.6.2

### ⚙️ Miscellaneous Tasks

- Обновление условий зависимости jobs в docker-publish.yml для поддержки динамического определения необходимости тестирования при pull_request событиях
- Добавление нового workflow для тестирования в tests.yml и упрощение логики в docker-publish.yml
- Исправление ссылки на ветку в docker-publish.yml для корректного запуска тестов при pull_request событиях
- Удаление лишнего шага "Sideload tests" в docker-publish.yml для упрощения логики workflow
- Добавление нового workflow для тестирования pull_request событий с использованием PostgreSQL
- Обновление ключа кэширования в pr-tests.yml для учета uv.lock и удаление лишних параметров установки
- Изменение триггера для workflow docker-publish и добавление шага для его вызова из pr-tests.yml
- Добавление триггера workflow_call в docker-publish.yml и упрощение вызова из pr-tests.yml

## [0.6.1] - 2025-05-18

### 🐛 Bug Fixes

- Move postgres

### 📚 Documentation

- Update changelog for v0.6.1

### ⚙️ Miscellaneous Tasks

- Добавить тестирование PR с использованием uv
- Улучшить тестирование PR с использованием PostgreSQL
- Улучшить шаги тестирования PR в GitHub Actions
- New workflow
- Revert workflow
- Fix uv
- Fix cache path
- Cache
- Python
- Test cache
- Test frozen
- Test
- Test
- Объединение тестов в один workflow и удаление старого файла tests.yml
- Обновление условий выполнения jobs в docker-publish.yml для поддержки pull_request и push событий
- Добавление параметров кэширования в docker-publish.yml для улучшения производительности
- Обновление параметров кэширования в docker-publish.yml для использования glob-выражения
- Добавление кэширования зависимостей uv в docker-publish.yml для повышения производительности
- Удаление лишнего пробела и пустой строки в docker-publish.yml для улучшения читаемости

## [0.6.0] - 2025-05-18

### 🚀 Features

- Оптимизация кода + тесты

### 📚 Documentation

- Update changelog for v0.6.0

## [0.5.0] - 2025-05-04

### 🚀 Features

- Восстановить отображение поля location в админке OperationAdmin

### 📚 Documentation

- Update changelog for v0.5.0

## [0.4.0] - 2025-05-04

### 🚀 Features

- Обновить админку ItemAdmin для добавления поля serial_number в список ссылок
- Обновить админку ItemAdmin для добавления новых полей текущего статуса и ответственного

### 🐛 Bug Fixes

- Улучшить отображение текущего статуса, местоположения и ответственного в админке ItemAdmin

### 📚 Documentation

- Update changelog for v0.4.0

## [0.3.0] - 2025-05-04

### 🚀 Features

- Добавить приложение Inventory в настройки проекта
- Добавить приложение Inventory с базовой конфигурацией
- Обновить админку для модели Device и добавить модель Item
- Обновить админку для моделей Category, Manufacturer, Model, Type и Device
- Обновить админку модели Item для улучшения поиска
- Обновить поле серийного номера в модели Item
- Добавить модель Operation и обновить админку для Item
- Обновить админку модели Item для отображения текущих данных
- Улучшить админку модели Operation для отображения ответственного
- Улучшить отображение ответственного в админке модели Operation
- Добавить модель Responsible и обновить админку для управления ответственными
- Добавить модель Status и обновить админку для управления статусами
- Добавить метод get_full_name в админку модели Responsible и обновить порядок сортировки в модели Operation
- Добавить модели Category, Manufacturer, Model и Type, а также админку для управления ими
- Обновить модели и админку для управления устройствами и ответственными
- Добавить приложение devices в настройки проекта
- Обновить админку и модели для управления устройствами и статусами
- Восстановить и обновить модель Operation и админку для управления эксплуатацией
- Добавить тесты для моделей Category, Manufacturer, Model и Type
- Добавить тесты для моделей Item и Operation
- Добавить тесты для моделей Device, Location, Responsible и Status
- Добавить миграцию для моделей Category, Manufacturer, Model и Type
- Добавить начальную миграцию для моделей Location, Status, Responsible и Device
- Добавить начальную миграцию для моделей Item и Operation
- Заменить поле description на notes в моделях Category, Manufacturer, Model и Type
- Обновить админку и модели для использования поля notes вместо description
- Обновить админку и тесты для использования поля notes вместо description
- Обновить админку для классов Device, Location, Status, Category, Manufacturer, Model и Type
- Добавить автозаполнение для поля device в админке ItemAdmin
- Добавить поле notes в модель Responsible
- Обновить админку для классов Device, Location, Manufacturer, Model, Type, Item и Operation
- Добавить поле notes в миграции моделей Catalog, Device и Inventory

### 🐛 Bug Fixes

- Унифицировать форматирование полей в админке и моделях
- Унифицировать форматирование в классе DevicesConfig
- Унифицировать форматирование в моделях и тестах
- Заменить ValidationError на IntegrityError в тестах моделей Category, Manufacturer, Model и Type
- Заменить ValidationError на IntegrityError в тестах модели Device
- Обновить тесты модели Item и Operation для корректной обработки исключений

### 💼 Other

- Compose.yml rebuild

### 🚜 Refactor

- Обновить админку и модели для улучшения структуры и читаемости

### 📚 Documentation

- Update changelog for v0.3.0

### ⚙️ Miscellaneous Tasks

- Удалить неиспользуемый файл views.py
- Удалить неиспользуемый файл тестов

## [0.2.0] - 2025-05-03

### 🚀 Features

- Добавить базовую структуру приложения catalogs
- Добавить приложение catalogs в настройки Django
- Обновить настройки Docker Compose для Postgres
- Добавить сервис makemigrations в настройки Docker Compose
- Обновить настройки Docker Compose для проверки состояния сервиса Postgres
- Упростить настройки Docker Compose для сервиса Django, удалив ненужные комментарии и конфигурации
- Добавить модель Vendor и зарегистрировать её в админке Django
- Добавить модель Model и зарегистрировать её в админке Django
- Добавить модель Device и зарегистрировать её в админке Django
- Улучшить админку Django, добавив настройки для моделей Vendor, Model и Device
- Обновить админку Django, добавив ссылки для отображения и исправив порядок полей в моделях
- Изменить порядок отображения и фильтрации полей в админке для моделей Vendor, Model и Device
- Добавить модель Category и обновить админку для отображения и фильтрации устройств по категориям
- Изменить поле serial_number на catalog_number в модели Device и обновить админку для отображения и поиска по новому полю
- Изменить поведение полей в модели Device с CASCADE на PROTECT для обеспечения целостности данных
- Переименовать модель Vendor в Manufacturer и обновить соответствующие ссылки в админке и моделях
- Добавить автозаполнение для полей категории, производителя и модели в админке устройства
- Добавить уникальное ограничение для модели Device по полям category, manufacturer и model
- Добавить модель Type и обновить модель Device для использования нового поля
- Обновить модель Device и админку для улучшения отображения и поиска
- Изменить формат отображения модели Device для улучшения читаемости
- Добавить человекочитаемое имя для приложения Catalogs
- Добавить тесты для моделей Category, Manufacturer, Model, Type и Device

### 📚 Documentation

- Update changelog for v0.2.0

### ⚙️ Miscellaneous Tasks

- Disable docker build on main branch
- Compose

## [0.1.1] - 2025-04-11

### 🐛 Bug Fixes

- CSRF parenthesis

### 📚 Documentation

- Update changelog for v0.1.1

## [0.1.0] - 2025-04-11

### 🚀 Features

- CSRF_TRUSTED_ORIGINS

### 📚 Documentation

- Update changelog for v0.1.0

## [0.0.0] - 2025-04-09

### 🚀 Features

- Django
- Dockerfile (editable mode)
- Dockerfile MVP
- Compose.yml
- Env ALLOWED_HOSTS
- Compose sql loader
- Workflows

### 🐛 Bug Fixes

- --noreload

### 🚜 Refactor

- Dockerfile
- Dockerfile
- Pin base image
- Django entrypoint
- Remove makemigrations
- Docker stuff
- -> src
- Ignores
- Add postgres
- Paths and user
- Push on pr
- Remove .npmrc

### 📚 Documentation

- README.md

### ⚙️ Miscellaneous Tasks

- Gitignore
- .gitignore
- Ignores

<!-- generated by git-cliff -->
