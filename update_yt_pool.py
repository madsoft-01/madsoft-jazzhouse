import json
import subprocess
import sys
from pathlib import Path

# Настройки
JSON_FILE = Path("jazzhouse_ids.json")
CHANNEL_URL = "https://www.youtube.com/@jazzhousestudio/videos"
SKIP_OLDEST_COUNT = 11  # Сколько самых первых (старых) видео канала игнорируем


def main():
    # 1. Читаем текущий список ID из JSON
    if not JSON_FILE.exists():
        print(f"Ошибка: файл {JSON_FILE} не найден!")
        sys.exit(1)

    current_ids = json.loads(JSON_FILE.read_text(encoding="utf-8"))
    existing_set = set(current_ids)
    print(f"Сейчас в базе: {len(current_ids)} видео.")

    # 2. Запрашиваем через yt-dlp плоский список всех ID со вкладки Videos
    # (YouTube отдает их в порядке от самого свежего к самому старому)
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--print", "id",
        CHANNEL_URL
    ]

    print(f"Запрашиваем список видео с {CHANNEL_URL} ...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("Ошибка при запуске yt-dlp:")
        print(result.stderr)
        sys.exit(1)

    fetched_ids = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    print(f"Всего найдено видео на канале: {len(fetched_ids)}")

    if len(fetched_ids) <= SKIP_OLDEST_COUNT:
        print("Видео на канале меньше или равно числу пропускаемых. Выходим.")
        return

    # 3. Отрезаем 11 самых старых видео (они лежат в самом конце списка)
    valid_fetched = fetched_ids[:-SKIP_OLDEST_COUNT]

    # 4. Отбираем только те ID, которых еще нет в нашем JSON
    # Так как valid_fetched идет от новых к старым, в new_ids самый свежий ролик тоже будет первым
    new_ids = [vid for vid in valid_fetched if vid not in existing_set]

    if not new_ids:
        print("Новых видео нет. База уже в актуальном состоянии.")
        return

    print(f"Найдено новых видео: {len(new_ids)} -> {new_ids}")

    # 5. Дописываем новые ID в самое начало списка (перед ubfDsT8gQeE)
    updated_ids = new_ids + current_ids

    # 6. Форматируем массив по 5 штук в ряд, отсчитывая полные пятерки снизу,
    # чтобы старые строки вообще не сдвигались, а заполнялась только верхняя строка
    rem = len(updated_ids) % 5
    lines = []

    if rem > 0:
        first_row = ", ".join(f'"{vid}"' for vid in updated_ids[:rem])
        lines.append(f"  {first_row}")

    for i in range(rem, len(updated_ids), 5):
        chunk = ", ".join(f'"{vid}"' for vid in updated_ids[i:i + 5])
        lines.append(f"  {chunk}")

    formatted_json = "[\n" + ",\n".join(lines) + "\n]\n"
    JSON_FILE.write_text(formatted_json, encoding="utf-8")

    print(f"Готово! Обновленный список ({len(updated_ids)} шт.) записан в {JSON_FILE}.")


if __name__ == "__main__":
    main()
