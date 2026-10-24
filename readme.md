# SmartWorkout API

Серверная часть фитнес-приложения SmartWorkout. Пользователь выбирает упражнения из каталога, собирает из них программы тренировок, добавляет чужие программы в избранное, проводит тренировки по программам и смотрит историю результатов.

Сервер написан на Python без веб-фреймворков: HTTP-сервер и маршрутизатор построены на стандартной библиотеке, данные хранятся в MongoDB.

- [Запуск](#запуск)
- [Общие правила](#общие-правила)
- [Эндпоинты](#эндпоинты)
- [Подробное описание эндпоинтов](#подробное-описание-эндпоинтов)
- [Модели данных](#модели-данных)
- [Swagger](#swagger)

## Запуск

```bash
cp .env.example .env              # настройки MongoDB и секрет для токенов
pip install -r requirements.txt
make start                        # MongoDB в Docker и сервер на http://localhost:8000
make start-ui                     # то же и веб-интерфейс базы DbGate на http://localhost:3000
pytest                            # тесты, нужна запущенная MongoDB (make db-up)
```

## Общие правила

- **Адрес сервера:** `http://localhost:8000`. Тела запросов и ответов передаются в JSON (UTF-8).
- **Авторизация.** Все эндпоинты, кроме `/auth/*`, требуют заголовок `Authorization: Bearer <access_token>`. Токен доступа выдаёт `POST /auth/login`, он действует 15 минут. Refresh-токен действует 30 дней и хранится в cookie `refresh_token` (HttpOnly, путь `/auth`). По нему `POST /auth/refresh` выдаёт новые токены.
- **Роли.** `USER` — обычный пользователь, его получает каждый при регистрации. `ADMIN` — администратор, только он может менять каталог упражнений.
- **Идентификаторы** (`exercise_id`, `program_id`, `session_id`) — строки из 24 шестнадцатеричных символов, например `6adc3a249f3c1a7e524b1d5f`.
- **Даты** передаются в формате ISO 8601 в UTC: `2026-10-24T04:55:00.000+00:00`.
- **Списки** отдаются страницами. Параметр `limit` задаёт размер страницы от 1 до 100 (по умолчанию 20), параметр `cursor` — начало следующей страницы: в него передаётся значение `next` из предыдущего ответа. Ответ со страницей:

  ```text
  {
    "data": [ объекты страницы ],
    "next": курсор следующей страницы или null,
    "has_more": true, если есть ещё страницы
  }
  ```

- **Request ID.** В каждом ответе есть заголовок `X-Request-Id`, по нему запрос можно найти в логах сервера.

### Ошибки

Ошибка в данных запроса возвращается со статусом 400. Если неверны конкретные поля, они перечислены в `errors`:

```json
{
  "code": "BAD_REQUEST",
  "message": "Validation failed",
  "errors": [
    { "field": "password", "message": "password must be at least 6 characters long" }
  ]
}
```

Остальные ошибки содержат только машинный код и текст:

```json
{ "code": "NOT_FOUND", "message": "Program not found" }
```

| Статус | `code` | Когда возникает |
|---|---|---|
| 400 | `BAD_REQUEST` | Неверное тело запроса, параметры или формат идентификатора |
| 401 | `UNAUTHORIZED`, `INVALID_CREDENTIALS`, `TOKEN_INVALID`, `TOKEN_EXPIRED` | Нет токена или он недействителен; неверный email или пароль при входе |
| 403 | `FORBIDDEN` | Нет прав: нужна роль `ADMIN` или действие с чужой программой |
| 404 | `NOT_FOUND` | Объекта нет или он недоступен текущему пользователю |
| 405 | `METHOD_NOT_ALLOWED` | Метод не поддерживается для этого адреса |
| 409 | `CONFLICT`, `DUPLICATE_EMAIL` | Запрос противоречит текущему состоянию данных |
| 413 | `PAYLOAD_TOO_LARGE` | Тело запроса больше 1 МБ |
| 500 | `INTERNAL_ERROR` | Внутренняя ошибка сервера |

## Эндпоинты

Название действия ведёт к подробному описанию: параметрам, примеру запроса и ответа.

| Название действия | Локейшн (URL) | Тип запроса | Описание запроса и ответа |
|---|---|---|---|
| **Аутентификация** | | | |
| [Зарегистрироваться](#зарегистрироваться) | `/auth/register` | POST | Принимает `email` и `password`. Возвращает 201 и созданного пользователя. |
| [Войти](#войти) | `/auth/login` | POST | Принимает `email` и `password`. Возвращает 200, `access_token` и данные пользователя; refresh-токен записывает в cookie. |
| [Обновить токен](#обновить-токен) | `/auth/refresh` | POST | Принимает refresh-токен из cookie. Возвращает 200 и новый `access_token`, cookie обновляет. |
| [Выйти](#выйти) | `/auth/logout` | POST | Тело не нужно. Возвращает 204 и удаляет cookie с refresh-токеном. |
| **Профиль** | | | |
| [Получить профиль](#получить-профиль) | `/me` | GET | Параметров нет. Возвращает 200 и профиль текущего пользователя. |
| **Упражнения** | | | |
| [Получить список упражнений](#получить-список-упражнений) | `/exercises` | GET | Параметры запроса: `muscle_group`, `equipment`, `search`, `cursor`, `limit`. Возвращает 200 и страницу упражнений. |
| [Получить упражнение](#получить-упражнение) | `/exercises/{exercise_id}` | GET | Принимает id упражнения в пути. Возвращает 200 и упражнение. |
| [Создать упражнение](#создать-упражнение) | `/exercises` | POST | Только `ADMIN`. Принимает `name`, `muscle_groups`, `equipment` и необязательные `description`, `video_url`, `image_url`. Возвращает 201 и созданное упражнение. |
| [Изменить упражнение](#изменить-упражнение) | `/exercises/{exercise_id}` | PATCH | Только `ADMIN`. Принимает изменяемые поля упражнения. Возвращает 200 и обновлённое упражнение. |
| [Удалить упражнение](#удалить-упражнение) | `/exercises/{exercise_id}` | DELETE | Только `ADMIN`. Возвращает 204. Упражнение, которое входит в программу, не удаляется: 409. |
| **Программы тренировок** | | | |
| [Получить публичные программы](#получить-публичные-программы) | `/programs` | GET | Параметры запроса: `cursor`, `limit`. Возвращает 200 и страницу публичных программ всех пользователей. |
| [Получить свои программы](#получить-свои-программы) | `/me/programs` | GET | Параметры запроса: `cursor`, `limit`. Возвращает 200 и страницу программ текущего пользователя, публичных и приватных. |
| [Получить программу](#получить-программу) | `/programs/{program_id}` | GET | Принимает id программы в пути. Возвращает 200 и программу, если она публичная или своя. |
| [Создать программу](#создать-программу) | `/programs` | POST | Принимает `title`, `is_public`, `difficulty`, `exercises` и необязательное `description`. Возвращает 201 и созданную программу. |
| [Изменить программу](#изменить-программу) | `/programs/{program_id}` | PATCH | Только автор. Принимает изменяемые поля: `title`, `description`, `difficulty`, `exercises`. Возвращает 200 и обновлённую программу. |
| [Удалить программу](#удалить-программу) | `/programs/{program_id}` | DELETE | Только автор. Возвращает 204. Программа удаляется и из избранного других пользователей. |
| **Избранное** | | | |
| [Получить избранное](#получить-избранное) | `/me/favorites` | GET | Параметры запроса: `cursor`, `limit`. Возвращает 200 и страницу кратких карточек программ. |
| [Добавить программу в избранное](#добавить-программу-в-избранное) | `/me/favorites` | POST | Принимает `program_id` чужой публичной программы. Возвращает 201 и `{"status": "success"}`. |
| [Убрать программу из избранного](#убрать-программу-из-избранного) | `/me/favorites/{program_id}` | DELETE | Принимает id программы в пути. Возвращает 204. |
| **Тренировки** | | | |
| [Начать тренировку](#начать-тренировку) | `/me/sessions` | POST | Принимает `program_id`. Копирует упражнения программы в новую тренировку. Возвращает 201 и тренировку в статусе `in_progress`. |
| [Получить историю тренировок](#получить-историю-тренировок) | `/me/sessions` | GET | Параметры запроса: `cursor`, `limit`. Возвращает 200 и страницу кратких записей о тренировках, новые сначала. |
| [Получить тренировку](#получить-тренировку) | `/me/sessions/{session_id}` | GET | Принимает id тренировки в пути. Возвращает 200 и тренировку с результатами по упражнениям. |
| [Сохранить результат тренировки](#сохранить-результат-тренировки) | `/me/sessions/{session_id}` | PATCH | Принимает `exercises` с фактическими результатами и (или) `status: "finished"`. Возвращает 200 и тренировку. Завершённую тренировку изменить нельзя: 409. |
| [Удалить тренировку](#удалить-тренировку) | `/me/sessions/{session_id}` | DELETE | Принимает id тренировки в пути. Возвращает 204. |

## Подробное описание эндпоинтов

### Аутентификация

#### Зарегистрироваться

`POST /auth/register` · без токена

Создаёт пользователя с ролью `USER`. Вход не выполняет: после регистрации нужен `POST /auth/login`.

**Тело запроса**

| Поле | Тип | Обязательное | Описание |
|---|---|---|---|
| `email` | string | да | Email, сохраняется в нижнем регистре |
| `password` | string | да | Пароль от 6 до 32 символов |

```json
{
  "email": "anna@example.com",
  "password": "strongpass1"
}
```

**Ответ `201 Created`**

```json
{
  "id": "6adc36a09f3c1a7e524b1d58",
  "email": "anna@example.com",
  "created_at": "2026-10-24T04:40:00.512+00:00"
}
```

**Ошибки:** `400` — неверный email или длина пароля; `409 DUPLICATE_EMAIL` — email уже зарегистрирован.

#### Войти

`POST /auth/login` · без токена

Проверяет email и пароль. Выдаёт токен доступа на 15 минут и refresh-токен на 30 дней.

**Тело запроса**

| Поле | Тип | Обязательное | Описание |
|---|---|---|---|
| `email` | string | да | Email пользователя |
| `password` | string | да | Пароль |

```json
{
  "email": "anna@example.com",
  "password": "strongpass1"
}
```

**Ответ `200 OK`**

Заголовок `Set-Cookie: refresh_token=<refresh-токен>; HttpOnly; Max-Age=2592000; Path=/auth; SameSite=Strict`.

```json
{
  "access_token": "eyJzdWIiOiI2YWRjMzZhMDlmM2MxYTdlNTI0YjFkNTgiLCJlbWFpbCI6ImFubmFAZXhhbXBsZS5jb20iLCJyb2xlIjoiVVNFUiIsInR5cGUiOiJhY2Nlc3MiLCJleHAiOjE3OTI4MTc3NjB9.V4tTATEVDxsugjcJYLHYDsRUKH6DAORpBRdQ7vjm1dU",
  "user": {
    "id": "6adc36a09f3c1a7e524b1d58",
    "email": "anna@example.com"
  }
}
```

**Ошибки:** `400` — не передан email или пароль; `401 INVALID_CREDENTIALS` — неверный email или пароль.

#### Обновить токен

`POST /auth/refresh` · без токена доступа, нужна cookie `refresh_token`

Выдаёт новый токен доступа и записывает в cookie новый refresh-токен. Тело не нужно.

**Ответ `200 OK`**

Заголовок `Set-Cookie` с новым `refresh_token`, как при входе.

```json
{
  "access_token": "eyJzdWIiOiI2YWRjMzZhMDlmM2MxYTdlNTI0YjFkNTgiLCJlbWFpbCI6ImFubmFAZXhhbXBsZS5jb20iLCJyb2xlIjoiVVNFUiIsInR5cGUiOiJhY2Nlc3MiLCJleHAiOjE3OTI4MTg2NjB9.MyxdwElSF53VINK6pHDrwR2O4Zz0o3jINPB80meb8lE"
}
```

**Ошибки:** `401 UNAUTHORIZED` — нет cookie; `401 TOKEN_INVALID` или `401 TOKEN_EXPIRED` — refresh-токен недействителен или истёк.

#### Выйти

`POST /auth/logout` · без токена

Удаляет cookie с refresh-токеном. Токен доступа клиент удаляет у себя сам. Тело не нужно.

**Ответ `204 No Content`**

Тела нет. Заголовок `Set-Cookie: refresh_token=""; Max-Age=0; Path=/auth` удаляет cookie.

**Ошибки:** нет.

### Профиль

#### Получить профиль

`GET /me` · любой пользователь с токеном

Параметров нет.

**Ответ `200 OK`** — [профиль пользователя](#профиль-пользователя)

```json
{
  "id": "6adc36a09f3c1a7e524b1d58",
  "email": "anna@example.com",
  "role": "USER",
  "created_at": "2026-10-24T04:40:00.512+00:00"
}
```

**Ошибки:** `401`.

### Упражнения

#### Получить список упражнений

`GET /exercises` · любой пользователь с токеном

**Параметры запроса** (все необязательные)

| Параметр | Тип | Описание |
|---|---|---|
| `muscle_group` | string | Группы мышц через запятую, например `CHEST,ARMS` ([значения](#перечисления)) |
| `equipment` | string | Инвентарь через запятую, например `DUMBBELL,BODYWEIGHT` ([значения](#перечисления)) |
| `search` | string | Подстрока в названии или описании, без учёта регистра |
| `cursor` | string | Курсор следующей страницы из поля `next` |
| `limit` | integer | Размер страницы от 1 до 100, по умолчанию 20 |

Внутри одного фильтра подходит любое из перечисленных значений, а разные фильтры должны выполняться одновременно. Регистр значений не важен. Упражнения идут в порядке добавления в каталог.

Пример запроса: `GET /exercises?muscle_group=chest,arms&equipment=bodyweight&limit=1`

**Ответ `200 OK`** — страница [упражнений](#упражнение)

```json
{
  "data": [
    {
      "id": "6ad315e89f3c1a7e524b1d27",
      "name": "Push-up",
      "description": "Отжимания от пола, корпус держать прямым",
      "muscle_groups": ["CHEST", "ARMS"],
      "equipment": ["BODYWEIGHT"],
      "video_url": "https://video.example.com/push-up",
      "image_url": "https://cdn.example.com/exercises/push-up.png",
      "created_at": "2026-10-17T06:30:00.000+00:00"
    }
  ],
  "next": "6ad315e89f3c1a7e524b1d27",
  "has_more": true
}
```

**Ошибки:** `400` — недопустимое значение фильтра, `cursor` или `limit`; `401`.

#### Получить упражнение

`GET /exercises/{exercise_id}` · любой пользователь с токеном

**Параметр пути:** `exercise_id` — id упражнения.

**Ответ `200 OK`** — [упражнение](#упражнение)

```json
{
  "id": "6ad315e89f3c1a7e524b1d27",
  "name": "Push-up",
  "description": "Отжимания от пола, корпус держать прямым",
  "muscle_groups": ["CHEST", "ARMS"],
  "equipment": ["BODYWEIGHT"],
  "video_url": "https://video.example.com/push-up",
  "image_url": "https://cdn.example.com/exercises/push-up.png",
  "created_at": "2026-10-17T06:30:00.000+00:00"
}
```

**Ошибки:** `401`; `404` — упражнения нет.

#### Создать упражнение

`POST /exercises` · только `ADMIN`

**Тело запроса**

| Поле | Тип | Обязательное | Описание |
|---|---|---|---|
| `name` | string | да | Название, от 1 до 100 символов |
| `muscle_groups` | array of string | да | Группы мышц, хотя бы одна ([значения](#перечисления)) |
| `equipment` | array of string | да | Инвентарь, хотя бы один ([значения](#перечисления)) |
| `description` | string | нет | Описание, до 500 символов |
| `video_url` | string (URI) | нет | Ссылка на видео с техникой |
| `image_url` | string (URI) | нет | Ссылка на картинку |

Поля, которых нет в таблице, не принимаются.

```json
{
  "name": "Plank",
  "description": "Упор на предплечьях, тело в одну линию",
  "muscle_groups": ["CORE"],
  "equipment": ["BODYWEIGHT"],
  "video_url": "https://video.example.com/plank"
}
```

**Ответ `201 Created`** — созданное [упражнение](#упражнение)

```json
{
  "id": "6ad317149f3c1a7e524b1d35",
  "name": "Plank",
  "description": "Упор на предплечьях, тело в одну линию",
  "muscle_groups": ["CORE"],
  "equipment": ["BODYWEIGHT"],
  "video_url": "https://video.example.com/plank",
  "created_at": "2026-10-17T06:35:00.000+00:00"
}
```

**Ошибки:** `400` — ошибка в полях; `401`; `403` — роль не `ADMIN`.

#### Изменить упражнение

`PATCH /exercises/{exercise_id}` · только `ADMIN`

Меняет только переданные поля, остальные остаются прежними. Поля и ограничения те же, что при создании, но все необязательные; `null` не допускается.

**Параметр пути:** `exercise_id` — id упражнения.

```json
{
  "description": "Упор на предплечьях, держать 30–60 секунд"
}
```

**Ответ `200 OK`** — [упражнение](#упражнение) после изменения

```json
{
  "id": "6ad317149f3c1a7e524b1d35",
  "name": "Plank",
  "description": "Упор на предплечьях, держать 30–60 секунд",
  "muscle_groups": ["CORE"],
  "equipment": ["BODYWEIGHT"],
  "video_url": "https://video.example.com/plank",
  "created_at": "2026-10-17T06:35:00.000+00:00"
}
```

**Ошибки:** `400` — ошибка в полях или неверный формат id; `401`; `403` — роль не `ADMIN`; `404` — упражнения нет.

#### Удалить упражнение

`DELETE /exercises/{exercise_id}` · только `ADMIN`

**Параметр пути:** `exercise_id` — id упражнения.

**Ответ `204 No Content`** — тела нет.

**Ошибки:** `401`; `403` — роль не `ADMIN`; `404` — упражнения нет; `409 CONFLICT` — упражнение входит хотя бы в одну программу:

```json
{ "code": "CONFLICT", "message": "Exercise is used in one or more programs" }
```

### Программы тренировок

#### Получить публичные программы

`GET /programs` · любой пользователь с токеном

**Параметры запроса:** `cursor`, `limit` (см. [общие правила](#общие-правила)). Программы идут в порядке создания.

**Ответ `200 OK`** — страница [программ](#программа)

```json
{
  "data": [
    {
      "id": "6ad88e4c9f3c1a7e524b1d43",
      "title": "Full body для начинающих",
      "description": "Базовая программа на всё тело без инвентаря",
      "is_public": true,
      "difficulty": "Beginner",
      "author_id": "6ad723049f3c1a7e524b1d3c",
      "exercises": [
        {
          "exercise_id": "6ad315e89f3c1a7e524b1d27",
          "exercise_name": "Push-up",
          "order": 1,
          "sets": 3,
          "reps": 12,
          "rest_sec": 60
        }
      ],
      "created_at": "2026-10-21T10:05:00.000+00:00",
      "updated_at": "2026-10-21T10:05:00.000+00:00"
    }
  ],
  "next": null,
  "has_more": false
}
```

**Ошибки:** `400` — неверный `cursor` или `limit`; `401`.

#### Получить свои программы

`GET /me/programs` · любой пользователь с токеном

Возвращает программы, автор которых — текущий пользователь, и публичные, и приватные.

**Параметры запроса:** `cursor`, `limit`. Программы идут в порядке создания.

**Ответ `200 OK`** — страница [программ](#программа)

```json
{
  "data": [
    {
      "id": "6adc3a249f3c1a7e524b1d5f",
      "title": "Утро дома",
      "description": "Короткая тренировка перед работой",
      "is_public": false,
      "difficulty": "Beginner",
      "author_id": "6adc36a09f3c1a7e524b1d58",
      "exercises": [
        {
          "exercise_id": "6ad315e89f3c1a7e524b1d27",
          "exercise_name": "Push-up",
          "order": 1,
          "sets": 3,
          "reps": 12,
          "rest_sec": 60
        },
        {
          "exercise_id": "6ad316609f3c1a7e524b1d2e",
          "exercise_name": "Bodyweight squat",
          "order": 2,
          "sets": 3,
          "reps": 15,
          "rest_sec": 60
        }
      ],
      "created_at": "2026-10-24T04:55:00.000+00:00",
      "updated_at": "2026-10-24T04:55:00.000+00:00"
    }
  ],
  "next": null,
  "has_more": false
}
```

**Ошибки:** `400` — неверный `cursor` или `limit`; `401`.

#### Получить программу

`GET /programs/{program_id}` · любой пользователь с токеном

Программа доступна, если она публичная или текущий пользователь — её автор. Чужая приватная программа возвращает 404.

**Параметр пути:** `program_id` — id программы.

**Ответ `200 OK`** — [программа](#программа)

```json
{
  "id": "6adc3a249f3c1a7e524b1d5f",
  "title": "Утро дома",
  "description": "Короткая тренировка перед работой",
  "is_public": false,
  "difficulty": "Beginner",
  "author_id": "6adc36a09f3c1a7e524b1d58",
  "exercises": [
    {
      "exercise_id": "6ad315e89f3c1a7e524b1d27",
      "exercise_name": "Push-up",
      "order": 1,
      "sets": 3,
      "reps": 12,
      "rest_sec": 60
    },
    {
      "exercise_id": "6ad316609f3c1a7e524b1d2e",
      "exercise_name": "Bodyweight squat",
      "order": 2,
      "sets": 3,
      "reps": 15,
      "rest_sec": 60
    }
  ],
  "created_at": "2026-10-24T04:55:00.000+00:00",
  "updated_at": "2026-10-24T04:55:00.000+00:00"
}
```

**Ошибки:** `400` — неверный формат id; `401`; `404` — программы нет или она чужая приватная.

#### Создать программу

`POST /programs` · любой пользователь с токеном

Автором программы становится текущий пользователь.

**Тело запроса**

| Поле | Тип | Обязательное | Описание |
|---|---|---|---|
| `title` | string | да | Название, от 3 до 200 символов |
| `is_public` | boolean | да | Видна ли программа другим пользователям. Задаётся только при создании |
| `difficulty` | string | да | Сложность: `Beginner`, `Intermediate` или `Advanced` |
| `exercises` | array | да | Упражнения программы, хотя бы одно. Поля элемента — в таблице ниже |
| `description` | string | нет | Описание, до 2000 символов |

Элемент `exercises`:

| Поле | Тип | Обязательное | Описание |
|---|---|---|---|
| `exercise_id` | string | да | id упражнения из каталога |
| `order` | integer | да | Порядковый номер в программе, от 1 |
| `sets` | integer | да | Количество подходов, от 1 |
| `reps` | integer | да | Повторений в подходе, от 1 |
| `rest_sec` | integer | да | Отдых между подходами в секундах, от 0 |

```json
{
  "title": "Утро дома",
  "description": "Короткая тренировка перед работой",
  "is_public": false,
  "difficulty": "Beginner",
  "exercises": [
    { "exercise_id": "6ad315e89f3c1a7e524b1d27", "order": 1, "sets": 3, "reps": 12, "rest_sec": 60 },
    { "exercise_id": "6ad316609f3c1a7e524b1d2e", "order": 2, "sets": 3, "reps": 15, "rest_sec": 60 }
  ]
}
```

**Ответ `201 Created`** — созданная [программа](#программа). Сервер добавляет к упражнениям их названия из каталога (`exercise_name`).

```json
{
  "id": "6adc3a249f3c1a7e524b1d5f",
  "title": "Утро дома",
  "description": "Короткая тренировка перед работой",
  "is_public": false,
  "difficulty": "Beginner",
  "author_id": "6adc36a09f3c1a7e524b1d58",
  "exercises": [
    {
      "exercise_id": "6ad315e89f3c1a7e524b1d27",
      "exercise_name": "Push-up",
      "order": 1,
      "sets": 3,
      "reps": 12,
      "rest_sec": 60
    },
    {
      "exercise_id": "6ad316609f3c1a7e524b1d2e",
      "exercise_name": "Bodyweight squat",
      "order": 2,
      "sets": 3,
      "reps": 15,
      "rest_sec": 60
    }
  ],
  "created_at": "2026-10-24T04:55:00.000+00:00",
  "updated_at": "2026-10-24T04:55:00.000+00:00"
}
```

**Ошибки:** `400` — ошибка в полях или упражнения нет в каталоге (`"field": "exercises.0.exercise_id", "message": "Exercise not found"`); `401`.

#### Изменить программу

`PATCH /programs/{program_id}` · только автор программы

Меняет только переданные поля. Можно передать `title`, `description`, `difficulty` и `exercises` с теми же ограничениями, что при создании. Список `exercises` заменяется целиком. Поле `is_public` менять нельзя.

**Параметр пути:** `program_id` — id программы.

```json
{
  "title": "Утро дома: 20 минут",
  "difficulty": "Intermediate"
}
```

**Ответ `200 OK`** — [программа](#программа) после изменения, с новым `updated_at`

```json
{
  "id": "6adc3a249f3c1a7e524b1d5f",
  "title": "Утро дома: 20 минут",
  "description": "Короткая тренировка перед работой",
  "is_public": false,
  "difficulty": "Intermediate",
  "author_id": "6adc36a09f3c1a7e524b1d58",
  "exercises": [
    {
      "exercise_id": "6ad315e89f3c1a7e524b1d27",
      "exercise_name": "Push-up",
      "order": 1,
      "sets": 3,
      "reps": 12,
      "rest_sec": 60
    },
    {
      "exercise_id": "6ad316609f3c1a7e524b1d2e",
      "exercise_name": "Bodyweight squat",
      "order": 2,
      "sets": 3,
      "reps": 15,
      "rest_sec": 60
    }
  ],
  "created_at": "2026-10-24T04:55:00.000+00:00",
  "updated_at": "2026-10-24T05:10:00.000+00:00"
}
```

**Ошибки:** `400` — ошибка в полях, передан `is_public` или неверный формат id; `401`; `403` — программа чужая; `404` — программы нет.

#### Удалить программу

`DELETE /programs/{program_id}` · только автор программы

Программа удаляется и из избранного всех пользователей. Тренировки, проведённые по ней, остаются в истории.

**Параметр пути:** `program_id` — id программы.

**Ответ `204 No Content`** — тела нет.

**Ошибки:** `400` — неверный формат id; `401`; `403` — программа чужая; `404` — программы нет.

### Избранное

#### Получить избранное

`GET /me/favorites` · любой пользователь с токеном

**Параметры запроса:** `cursor`, `limit`. Сначала идут программы, созданные позже.

**Ответ `200 OK`** — страница [кратких карточек программ](#краткая-карточка-программы)

```json
{
  "data": [
    {
      "id": "6ad9b9209f3c1a7e524b1d4a",
      "title": "Кор за 15 минут",
      "description": "Планка и упражнения на пресс",
      "author_id": "6ad723049f3c1a7e524b1d3c",
      "is_public": true,
      "difficulty": "Intermediate"
    },
    {
      "id": "6ad88e4c9f3c1a7e524b1d43",
      "title": "Full body для начинающих",
      "description": "Базовая программа на всё тело без инвентаря",
      "author_id": "6ad723049f3c1a7e524b1d3c",
      "is_public": true,
      "difficulty": "Beginner"
    }
  ],
  "next": null,
  "has_more": false
}
```

**Ошибки:** `400` — неверный `cursor` или `limit`; `401`.

#### Добавить программу в избранное

`POST /me/favorites` · любой пользователь с токеном

Добавить можно только чужую публичную программу.

**Тело запроса**

| Поле | Тип | Обязательное | Описание |
|---|---|---|---|
| `program_id` | string | да | id программы |

```json
{
  "program_id": "6ad88e4c9f3c1a7e524b1d43"
}
```

**Ответ `201 Created`**

```json
{
  "status": "success"
}
```

**Ошибки:** `400` — неверный формат `program_id`; `401`; `403` — это своя программа; `404` — программы нет или она приватная; `409 CONFLICT` — программа уже в избранном.

#### Убрать программу из избранного

`DELETE /me/favorites/{program_id}` · любой пользователь с токеном

**Параметр пути:** `program_id` — id программы.

**Ответ `204 No Content`** — тела нет.

**Ошибки:** `400` — неверный формат id; `401`; `404` — программы нет в избранном.

### Тренировки

#### Начать тренировку

`POST /me/sessions` · любой пользователь с токеном

Создаёт тренировку по своей или публичной программе. Упражнения программы копируются в тренировку: изменения в тренировке не затрагивают программу, а последующие изменения программы — начатую тренировку.

**Тело запроса**

| Поле | Тип | Обязательное | Описание |
|---|---|---|---|
| `program_id` | string | да | id программы |

```json
{
  "program_id": "6adc3a249f3c1a7e524b1d5f"
}
```

**Ответ `201 Created`** — [тренировка](#тренировка) в статусе `in_progress`

```json
{
  "id": "6adc3b509f3c1a7e524b1d66",
  "user_id": "6adc36a09f3c1a7e524b1d58",
  "source_program_id": "6adc3a249f3c1a7e524b1d5f",
  "source_program_title": "Утро дома",
  "status": "in_progress",
  "started_at": "2026-10-24T05:00:00.000+00:00",
  "finished_at": null,
  "duration_sec": null,
  "exercises": [
    {
      "exercise_id": "6ad315e89f3c1a7e524b1d27",
      "exercise_name": "Push-up",
      "order": 1,
      "planned_sets": 3,
      "planned_reps": 12,
      "rest_sec": 60,
      "completed_sets": 0,
      "actual_reps": [],
      "is_completed": false,
      "is_skipped": false
    },
    {
      "exercise_id": "6ad316609f3c1a7e524b1d2e",
      "exercise_name": "Bodyweight squat",
      "order": 2,
      "planned_sets": 3,
      "planned_reps": 15,
      "rest_sec": 60,
      "completed_sets": 0,
      "actual_reps": [],
      "is_completed": false,
      "is_skipped": false
    }
  ]
}
```

**Ошибки:** `400` — неверный формат `program_id`; `401`; `404` — программы нет или она чужая приватная.

#### Получить историю тренировок

`GET /me/sessions` · любой пользователь с токеном

**Параметры запроса:** `cursor`, `limit`. Сначала идут новые тренировки.

**Ответ `200 OK`** — страница [кратких записей о тренировках](#краткая-запись-о-тренировке)

```json
{
  "data": [
    {
      "id": "6adc3b509f3c1a7e524b1d66",
      "source_program_id": "6adc3a249f3c1a7e524b1d5f",
      "source_program_title": "Утро дома",
      "status": "finished",
      "started_at": "2026-10-24T05:00:00.000+00:00",
      "finished_at": "2026-10-24T05:25:20.000+00:00",
      "duration_sec": 1520
    },
    {
      "id": "6ada19389f3c1a7e524b1d51",
      "source_program_id": "6ad88e4c9f3c1a7e524b1d43",
      "source_program_title": "Full body для начинающих",
      "status": "finished",
      "started_at": "2026-10-22T14:10:00.000+00:00",
      "finished_at": "2026-10-22T14:52:05.000+00:00",
      "duration_sec": 2525
    }
  ],
  "next": null,
  "has_more": false
}
```

**Ошибки:** `400` — неверный `cursor` или `limit`; `401`.

#### Получить тренировку

`GET /me/sessions/{session_id}` · любой пользователь с токеном

**Параметр пути:** `session_id` — id тренировки.

**Ответ `200 OK`** — [тренировка](#тренировка)

```json
{
  "id": "6adc3b509f3c1a7e524b1d66",
  "user_id": "6adc36a09f3c1a7e524b1d58",
  "source_program_id": "6adc3a249f3c1a7e524b1d5f",
  "source_program_title": "Утро дома",
  "status": "finished",
  "started_at": "2026-10-24T05:00:00.000+00:00",
  "finished_at": "2026-10-24T05:25:20.000+00:00",
  "duration_sec": 1520,
  "exercises": [
    {
      "exercise_id": "6ad315e89f3c1a7e524b1d27",
      "exercise_name": "Push-up",
      "order": 1,
      "planned_sets": 3,
      "planned_reps": 12,
      "rest_sec": 60,
      "completed_sets": 3,
      "actual_reps": [12, 12, 10],
      "is_completed": true,
      "is_skipped": false
    },
    {
      "exercise_id": "6ad316609f3c1a7e524b1d2e",
      "exercise_name": "Bodyweight squat",
      "order": 2,
      "planned_sets": 3,
      "planned_reps": 15,
      "rest_sec": 60,
      "completed_sets": 0,
      "actual_reps": [],
      "is_completed": false,
      "is_skipped": true
    }
  ]
}
```

**Ошибки:** `401`; `404` — тренировки нет или она чужая.

#### Сохранить результат тренировки

`PATCH /me/sessions/{session_id}` · любой пользователь с токеном, только своя тренировка

Во время тренировки сохраняет прогресс, в конце завершает её. Нужно передать хотя бы одно поле.

**Параметр пути:** `session_id` — id тренировки.

**Тело запроса**

| Поле | Тип | Обязательное | Описание |
|---|---|---|---|
| `exercises` | array | нет | Все упражнения тренировки с текущими результатами, заменяют прежний список. Поля элемента — в модели [упражнения в тренировке](#упражнение-в-тренировке) |
| `status` | string | нет | Значение `finished` завершает тренировку: сервер записывает `finished_at` и считает `duration_sec` |

В `exercises` можно менять порядок, план подходов и повторений и отдых; эти изменения касаются только этой тренировки. Состав упражнений менять нельзя. В `actual_reps` передаётся по одному числу на каждый выполненный подход.

```json
{
  "status": "finished",
  "exercises": [
    {
      "exercise_id": "6ad315e89f3c1a7e524b1d27",
      "exercise_name": "Push-up",
      "order": 1,
      "planned_sets": 3,
      "planned_reps": 12,
      "rest_sec": 60,
      "completed_sets": 3,
      "actual_reps": [12, 12, 10],
      "is_completed": true,
      "is_skipped": false
    },
    {
      "exercise_id": "6ad316609f3c1a7e524b1d2e",
      "exercise_name": "Bodyweight squat",
      "order": 2,
      "planned_sets": 3,
      "planned_reps": 15,
      "rest_sec": 60,
      "completed_sets": 0,
      "actual_reps": [],
      "is_completed": false,
      "is_skipped": true
    }
  ]
}
```

**Ответ `200 OK`** — [тренировка](#тренировка) после изменения. Для запроса выше — завершённая тренировка, как в примере [получения тренировки](#получить-тренировку):

```json
{
  "id": "6adc3b509f3c1a7e524b1d66",
  "user_id": "6adc36a09f3c1a7e524b1d58",
  "source_program_id": "6adc3a249f3c1a7e524b1d5f",
  "source_program_title": "Утро дома",
  "status": "finished",
  "started_at": "2026-10-24T05:00:00.000+00:00",
  "finished_at": "2026-10-24T05:25:20.000+00:00",
  "duration_sec": 1520,
  "exercises": [
    {
      "exercise_id": "6ad315e89f3c1a7e524b1d27",
      "exercise_name": "Push-up",
      "order": 1,
      "planned_sets": 3,
      "planned_reps": 12,
      "rest_sec": 60,
      "completed_sets": 3,
      "actual_reps": [12, 12, 10],
      "is_completed": true,
      "is_skipped": false
    },
    {
      "exercise_id": "6ad316609f3c1a7e524b1d2e",
      "exercise_name": "Bodyweight squat",
      "order": 2,
      "planned_sets": 3,
      "planned_reps": 15,
      "rest_sec": 60,
      "completed_sets": 0,
      "actual_reps": [],
      "is_completed": false,
      "is_skipped": true
    }
  ]
}
```

**Ошибки:** `400` — ошибка в полях, например упражнение не из этой тренировки или `status` не равен `finished`; `401`; `404` — тренировки нет или она чужая; `409 CONFLICT` — тренировка уже завершена.

#### Удалить тренировку

`DELETE /me/sessions/{session_id}` · любой пользователь с токеном, только своя тренировка

Удаляет тренировку из истории, например начатую по ошибке.

**Параметр пути:** `session_id` — id тренировки.

**Ответ `204 No Content`** — тела нет.

**Ошибки:** `401`; `404` — тренировки нет или она чужая.

## Модели данных

### Профиль пользователя

| Поле | Тип | Описание |
|---|---|---|
| `id` | string | id пользователя |
| `email` | string | Email |
| `role` | string | Роль: `USER` или `ADMIN` |
| `created_at` | string (date-time) | Дата регистрации |

### Упражнение

| Поле | Тип | Описание |
|---|---|---|
| `id` | string | id упражнения |
| `name` | string | Название |
| `description` | string | Описание; поля нет в ответе, если описание не задано |
| `muscle_groups` | array of string | Группы мышц ([значения](#перечисления)) |
| `equipment` | array of string | Инвентарь ([значения](#перечисления)) |
| `video_url` | string (URI) | Ссылка на видео; поля нет, если ссылка не задана |
| `image_url` | string (URI) | Ссылка на картинку; поля нет, если ссылка не задана |
| `created_at` | string (date-time) | Дата добавления в каталог |

### Программа

| Поле | Тип | Описание |
|---|---|---|
| `id` | string | id программы |
| `title` | string | Название |
| `description` | string | Описание, может быть пустой строкой |
| `is_public` | boolean | Видна ли программа другим пользователям |
| `difficulty` | string | Сложность ([значения](#перечисления)) |
| `author_id` | string | id автора |
| `exercises` | array | [Упражнения в программе](#упражнение-в-программе) |
| `created_at` | string (date-time) | Дата создания |
| `updated_at` | string (date-time) | Дата последнего изменения |

### Упражнение в программе

| Поле | Тип | Описание |
|---|---|---|
| `exercise_id` | string | id упражнения из каталога |
| `exercise_name` | string | Название упражнения на момент добавления в программу |
| `order` | integer | Порядковый номер, от 1 |
| `sets` | integer | Количество подходов, от 1 |
| `reps` | integer | Повторений в подходе, от 1 |
| `rest_sec` | integer | Отдых между подходами в секундах, от 0 |

### Краткая карточка программы

Используется в списке избранного.

| Поле | Тип | Описание |
|---|---|---|
| `id` | string | id программы |
| `title` | string | Название |
| `description` | string | Описание |
| `author_id` | string | id автора |
| `is_public` | boolean | Видна ли программа другим пользователям |
| `difficulty` | string | Сложность ([значения](#перечисления)) |

### Тренировка

| Поле | Тип | Описание |
|---|---|---|
| `id` | string | id тренировки |
| `user_id` | string | id пользователя |
| `source_program_id` | string | id программы, по которой начата тренировка |
| `source_program_title` | string | Название программы на момент начала |
| `status` | string | `in_progress` — идёт, `finished` — завершена |
| `started_at` | string (date-time) | Время начала |
| `finished_at` | string (date-time) или null | Время завершения, `null`, пока тренировка идёт |
| `duration_sec` | integer или null | Длительность в секундах, `null`, пока тренировка идёт |
| `exercises` | array | [Упражнения в тренировке](#упражнение-в-тренировке) |

### Упражнение в тренировке

| Поле | Тип | Описание |
|---|---|---|
| `exercise_id` | string | id упражнения из каталога |
| `exercise_name` | string | Название упражнения |
| `order` | integer | Порядковый номер, от 1 |
| `planned_sets` | integer | Запланировано подходов, от 1 |
| `planned_reps` | integer | Запланировано повторений в подходе, от 1 |
| `rest_sec` | integer | Отдых между подходами в секундах, от 0 |
| `completed_sets` | integer | Выполнено подходов, от 0 |
| `actual_reps` | array of integer | Фактические повторения в каждом выполненном подходе |
| `is_completed` | boolean | Упражнение выполнено |
| `is_skipped` | boolean | Упражнение пропущено |

### Краткая запись о тренировке

Используется в истории тренировок.

| Поле | Тип | Описание |
|---|---|---|
| `id` | string | id тренировки |
| `source_program_id` | string | id программы |
| `source_program_title` | string | Название программы на момент начала |
| `status` | string | `in_progress` или `finished` |
| `started_at` | string (date-time) | Время начала |
| `finished_at` | string (date-time) или null | Время завершения |
| `duration_sec` | integer или null | Длительность в секундах |

### Перечисления

| Поле | Значения |
|---|---|
| `muscle_groups`, параметр `muscle_group` | `CHEST`, `BACK`, `LEGS`, `ARMS`, `SHOULDERS`, `CORE`, `FULL_BODY` |
| `equipment` | `BARBELL`, `DUMBBELL`, `MACHINE`, `BODYWEIGHT`, `KETTLEBELL`, `RESISTANCE_BAND`, `OTHER` |
| `difficulty` | `Beginner`, `Intermediate`, `Advanced` |
| `role` | `USER`, `ADMIN` |
| `status` тренировки | `in_progress`, `finished` |

## Swagger

- Спецификация OpenAPI 3.0: [docs/openapi.yaml](docs/openapi.yaml).
- Swagger UI: [docs/swagger.html](docs/swagger.html). Страница загружает спецификацию с того же адреса, поэтому открывается через веб-сервер: `python -m http.server 8080 --directory docs`, затем http://localhost:8080/swagger.html.
