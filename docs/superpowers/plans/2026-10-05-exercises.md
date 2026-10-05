# Exercises Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Реализовать ровно пять операций Exercises по SmartWorkout 1.0.0 и согласованной логике фильтров.

**Architecture:** Сохранить слои handlers, dataclass DTO, services, repositories, errors, database. Использовать существующие middleware и сборку зависимостей в dependencies.py; проверку использования в Programs выполнять через репозиторий. Для корректного HTTP 204 требуется отдельная согласованная поправка общей отправки ответа.

**Tech Stack:** Python 3.13, стандартная библиотека (unittest, urllib.parse, re, http.server), pymongo==4.18.1, dnspython==2.8.0, локальная MongoDB 8.0. Новых зависимостей нет.

**Spec:** `docs/superpowers/specs/2026-10-05-exercises-design.md`.

## Global Constraints

- Ветка `fit_exercises`; никаких коммитов или push в main. Этот план не разрешает push, merge или публикацию.
- Только пять операций Exercises, пути/методы/поля/перечисления и ответы — по локальной копии актуального Swagger.
- Обработчики `(request, params)`, значения словарей через `.get()`; DTO — dataclass; сообщения ошибок на английском.
- Чтение require_auth; изменения require_auth, затем require_admin.
- Внутри каждого фильтра OR; между muscle_group и equipment AND — уже согласовано пользователем.
- name 1–100; description до 500; muscle_groups/equipment минимум 1 элемент с точными enum из спецификации; URL — uri, не только HTTP(S).
- PUT частичный; optional-поля не преобразовывать в null; уникальность названий и элементов массива не добавлять.
- limit 1–100, default 20; список `{data, next, limit, has_more}`; created_at date-time; Mongo ObjectId наружу строкой.
- Секреты и тестовые токены не сохранять в Git. Использовать отдельную временную БД с префиксом smartworkout_exercises_test_, не удалять данные fitness.
- Изменение app/server.py допустимо только после отдельного согласования конкретного diff для 204; auth/security/router/config не менять.

## Review Focus

1. Пропущенное поле и явный null должны различаться при PUT; пустой объект не стирает документ. Проверка в задачах 1 и 4.
2. В JSON может прийти массив вместо объекта, число вместо строки, строка вместо массива: ответ 400, не 500. Проверка в задачах 1 и 4.
3. Символы `.*`, `[`, `(` в search — буквальный текст; смешанный регистр и кириллица работают. Проверка в задачах 2 и 4.
4. Страницы при сочетании двух массивных фильтров не теряют и не повторяют упражнения. Проверка в задачах 2 и 4.
5. Используемое упражнение не удаляется ни при ObjectId, ни при строковой ссылке; два последовательных HTTP-запроса после DELETE не читают остаток `{}`. Проверка в задачах 3 и 5.

## Структура файлов

Создать `app/dtos/exercises.py`, `app/errors/exercises.py`, `app/repositories/exercises.py`, `app/services/exercises/__init__.py`, `app/services/exercises/service.py`, `app/handlers/exercises.py`.
Изменить реэкспорты errors/repositories/services, `app/handlers/__init__.py`, `app/dependencies.py`, `app/database/validators.py`, `app/database/indexes.py`.
Отдельная поправка: `app/server.py` (только 204).
Тесты: `tests/__init__.py`, `tests/test_exercises_dtos.py`, `tests/test_exercises_repository.py`, `tests/test_exercises_service.py`, `tests/test_exercises_api.py`, `tests/test_http_204.py`; при необходимости общий помощник `tests/exercises_support.py` для отдельной БД и локального тестового сервера.

### Task 1: DTO и ошибки

**Files:** Create `app/dtos/exercises.py`, `app/errors/exercises.py`, `tests/test_exercises_dtos.py`, `tests/__init__.py`; modify `app/errors/__init__.py`.

**Interfaces:**
- `MUSCLE_GROUPS: tuple[str, ...]`, `EQUIPMENT: tuple[str, ...]` — точные перечисления из Spec.
- `ExerciseCreateDTO(...)`, `ExerciseUpdateDTO(...)`: dataclass, поля name/description/muscle_groups/equipment/video_url/image_url; внутренний sentinel отсутствия поля; `to_document() -> dict` возвращает только переданные известные поля.
- `ExerciseListDTO(muscle_group=None, equipment=None, search=None, cursor=None, limit=20)`: dataclass; после валидации muscle_group/equipment — список или None, cursor — ObjectId или None, limit — int.
- `validate_exercise_id(value: str) -> ObjectId`: неверный формат вызывает DTOValidationError с field exercise_id.
- `ExerciseNotFoundError`: 404, code NOT_FOUND. `ExerciseInUseError`: 409, code CONFLICT, message Exercise is used in one or more programs.
- Использовать существующий DTOValidationError и AppError; не менять BaseDTO.

- [x] Написать тесты `test_create_required_and_boundaries`, `test_optional_missing_vs_null`, `test_update_preserves_omitted_fields`, `test_enum_arrays`, `test_query_validation`, `test_uri_scheme`. Assertions: имя 100 принято/101 отклонено; описание 500 принято/501 отклонено; пустой массив отклонён; CHEST и BODYWEIGHT приняты; неизвестный enum/нестроковый элемент отклонён; дубликаты сохраняются; пустой PUT даёт `{}`; null даёт DTOValidationError; default limit=20, 0/101/нечисловой limit отклонены; uri `https://example.org/video` и `urn:example:video` приняты, относительная ссылка и URI с пробелами отклонены.
- [x] Запустить `.\venv\Scripts\python.exe -m unittest tests.test_exercises_dtos -v`; до реализации ожидается ошибка отсутствующего модуля, не ошибка конфигурации.
- [x] Реализовать перечисленные DTO/ошибки, sentinel и проверку типов/длин/enum. Query-массивы разделять по запятой; курсор проверять по 24-hex и преобразовывать в ObjectId. Для uri использовать стандартный urllib.parse и проверку схемы/пробелов.
- [x] Повторить unittest: все тесты проходят.
- [x] Коммит только файлов задачи в fit_exercises: `feat: add exercise DTO validation`.

### Task 2: Репозиторий и MongoDB-схема

**Files:** Create `app/repositories/exercises.py`, `tests/test_exercises_repository.py`, `tests/exercises_support.py`; modify repositories реэкспорт, `app/database/validators.py`, `app/database/indexes.py`.

**Interfaces:** `ExerciseRepository(db: Database)`; `create(values: dict) -> dict`, `find_by_id(exercise_id: ObjectId) -> dict | None`, `find_page(filters: ExerciseListDTO) -> list[dict]` (не более limit+1), `update(exercise_id: ObjectId, changes: dict) -> dict | None`, `is_used_in_programs(exercise_id: ObjectId) -> bool`, `delete(exercise_id: ObjectId) -> bool`.

- [x] Написать интеграционные тесты с отдельной UUID-БД: create возвращает ObjectId/дату UTC; PUT меняет только name; две отдельные карточки CHEST и ARMS обе попадают в OR-фильтр; BODYWEIGHT исключается при equipment=DUMBBELL; search=`.*` находит только имя/описание с буквальным `.*`; последовательные страницы имеют непересекающиеся ID; ссылки на упражнение каждого из двух типов определяются; схема Mongo отклоняет лишнее поле/пустой массив/неизвестный enum.
- [x] Запустить `.\venv\Scripts\python.exe -m unittest tests.test_exercises_repository -v`; до реализации ожидается отсутствие репозитория. Отсутствие MongoDB считать проблемой окружения, не успешным тестом.
- [x] Реализовать create с UTC, find/update/delete по _id. update использовать `$set` только переданных полей и ReturnDocument.AFTER; пустой changes — чтение. find_page: `$in` для каждого массива, AND между полями, escaped regex `i` по name/description через `$or`, `_id > cursor`, сортировка _id ASC, limit+1. is_used_in_programs ищет вложенный exercise_id по ObjectId или hex-строке.
- [x] Добавить strict Mongo-схему EXERCISES: required name/muscle_groups/equipment/created_at; _id objectId; типы и ограничения из Spec; optional-строки; additionalProperties=false. Индексы: `(muscle_groups, _id)`, `(equipment, _id)`, `programs.exercises.exercise_id`. Не создавать составной индекс по двум массивам и не добавлять text-индекс для поиска подстроки.
- [x] Повторить тесты DTO и репозитория; завершение тестов удаляет только созданную UUID-БД после проверки префикса, закрывает клиент.
- [x] Коммит файлов задачи: `feat: add exercise persistence and schema`.

### Task 3: Сервис справочника

**Files:** Create `app/services/exercises/service.py`, `app/services/exercises/__init__.py`, `tests/test_exercises_service.py`; modify `app/services/__init__.py`.

**Interfaces:** `ExerciseService(exercise_repo: ExerciseRepository)`; `create(values: dict) -> dict`, `get(exercise_id: ObjectId) -> dict`, `update(exercise_id: ObjectId, changes: dict) -> dict`, `delete(exercise_id: ObjectId) -> None`, `list(filters: ExerciseListDTO) -> dict` (сырой data с документами, next/limit/has_more готовые).

- [x] Написать тесты с управляемым repository mock: отсутствие при get/update/delete вызывает ExerciseNotFoundError; использование вызывает ExerciseInUseError и delete не вызывается; свободное упражнение удаляется; исчезновение между проверкой и delete возвращает 404; лишний результат страницы не попадает в data, next — ID последнего выданного; конец списка next=None/has_more=False, включая пустую страницу.
- [x] Запустить `.\venv\Scripts\python.exe -m unittest tests.test_exercises_service -v`; ожидается отсутствие сервиса до реализации.
- [x] Реализовать методы по интерфейсам. Для delete сначала проверить существование и использование; MongoDB без FK не обеспечивает атомарность с будущим созданием Programs — не добавлять транзакции, блокировки или изменения чужого модуля.
- [x] Повторить тесты: все проходят.
- [x] Коммит: `feat: add exercise service rules`.

### Task 4: HTTP-обработчики и DI

**Files:** Create `app/handlers/exercises.py`, `tests/test_exercises_api.py`; modify `app/handlers/__init__.py`, `app/dependencies.py`; extend `tests/exercises_support.py`.

**Interfaces:** пять `(request, params)` обработчиков: `list_exercises`, `get_exercise`, `create_exercise`, `update_exercise`, `delete_exercise`; `serialize_exercise(document: dict) -> dict`; зависимость `exercise_service` из dependencies.py.

- [x] Написать интеграционные HTTP-тесты через ThreadingHTTPServer на 127.0.0.1, временном свободном порту и отдельной тестовой БД. Выпускать тестовые USER/ADMIN access tokens существующей issue; не менять реальные роли или сохранять токены. Проверить GET без токена=401; USER может читать, но POST/PUT/DELETE=403; ADMIN create=201, get/update=200; API ID/date-time строковые, обязательные поля на месте, отсутствующие optional-поля не появляются как null; несуществующий ID=404; использованное упражнение=409 с точным message; массив вместо объекта/невалидные поля=400 с английскими errors; PUT={} сохраняет документ; буквальный поиск и совмещённые фильтры/курсоры соответствуют Spec.
- [x] Запустить `.\venv\Scripts\python.exe -m unittest tests.test_exercises_api -v`; до регистрации маршрутов ожидается 404 вместо нужного результата.
- [x] Реализовать маршруты с существующими middleware, DTO и сервисом. Значения извлекать через `.get(key, sentinel)`. Проверять JSON-объект до извлечения полей. DTOValidationError преобразовывать в 400 BAD_REQUEST/Validation failed/errors; GET/DELETE невалидный ID — 404, PUT — validation 400. Общую инфраструктуру не менять.
- [x] Создать repo/service в dependencies.py и подключить обработчики в register_routes. Сериализовать только Exercise-поля: _id в id, created_at в date-time UTC; не отдавать неизвестные поля Mongo.
- [x] Повторить HTTP-тесты плюс предыдущие задачи. Пока поправка 204 не согласована, проверку точного пустого тела проводить отдельной задачей и явно отмечать зависимость, не заявлять полный контракт выполненным.
- [x] Коммит: `feat: expose Exercises API routes`.

### Task 5: Пустой HTTP 204 — отдельно согласуемая поправка

**Files:** Modify только `app/server.py`, метод `_send`; create `tests/test_http_204.py`. Предварительный diff для согласования: `.local_setup/http-204-proposal.patch`.

**Interface:** существующая `HTTPRequestHandler._send(response: Response) -> None` сохраняется. Для 204 отправить status и пользовательские headers (включая X-Request-Id), завершить headers и return: тело, автоматические Content-Type/Content-Length не отправлять. Остальные статусы используют прежний путь JSON.

- [x] До изменения сервера получить согласование приложенного diff. Его наличие в плане само по себе не отменяет требование согласовать инфраструктуру.
- [x] Написать тесты `test_204_has_no_body_or_content_length`, `test_json_responses_unchanged`, `test_keepalive_after_delete`. Assertions: 204 сохраняет X-Request-Id, bytes тела пусты, Content-Length отсутствует; 200 со словарём и 400 с ошибкой возвращают прежний JSON; два запроса по одному HTTP/1.1 соединению после DELETE корректно читаются без остаточных байтов.
- [x] Запустить `.\venv\Scripts\python.exe -m unittest tests.test_http_204 -v`; тест 204 должен упасть на текущем сервере с `{}`.
- [x] После согласования применить только раннюю ветку для HTTPStatus.NO_CONTENT. Никакого рефакторинга server/router/security или изменения порта.
- [x] Повторить все unittest: `.\venv\Scripts\python.exe -m unittest discover -s tests -v`; тесты проходят без skips интеграции.
- [x] Коммит отдельно: `fix: send HTTP 204 without a response body`.

### Task 6: Итоговая проверка и передача результата

- [x] Проверить полный набор тестов, `git diff --check`, `.\venv\Scripts\python.exe -m pip check`; сопоставить реальные HTTP-пути/поля/enum/статусы с `.local_setup/openapi.json`. Не менять Swagger для подгонки тестов.
- [x] Обновить только локальный README_LOCAL результатами, командами проверки и принятыми уточнениями. Не утверждать, что недокументированные случаи GET прописаны автором Swagger.
- [x] Перед перезапуском локального сервера убедиться, что PID принадлежит Python main.py именно этого проекта; не останавливать процесс по устаревшему PID. Запустить проект скрыто с логами после подтверждения кода, проверить Mongo ping и доступность Exercises с авторизацией.
- [x] Проверить diff на изменения вне объёма/секреты/добавленные зависимости и ветку fit_exercises. Push и PR не делать без дальнейшего запроса пользователя. Сообщить, что реализовано, какими проверками подтверждено и какие технические уточнения согласованы.

## Исполнение

Пользователь подтвердил самостоятельную реализацию в этом чате и отдельно разрешил конкретный diff для HTTP 204. Задачи выполнены через executing-plans и TDD; 42 теста проходят. После выполнения задач проводится одна независимая проверка ветки, предусмотренная executing-plans. Push, PR и merge не выполнялись.
