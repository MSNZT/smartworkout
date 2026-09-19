import os

OUTPUT_FILE = 'project_all.txt'
IGNORE_DIRS = {'.git', '__pycache__', '.idea', '.vscode', 'venv'}
ALLOWED_EXTENSIONS = {'.py'}

with open(OUTPUT_FILE, 'w', encoding='utf-8') as outfile:
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for file in files:
            if file in {OUTPUT_FILE, 'output_text.py'}:
                continue

            # ИСПРАВЛЕНО: берем расширение по индексу [1]
            ext = os.path.splitext(file)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                continue

            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, '.')

            outfile.write(f"// ==========================================\n")
            outfile.write(f"// ФАЙЛ: {rel_path}\n")
            outfile.write(f"// ==========================================\n\n")

            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as infile:
                    outfile.write(infile.read())
                    outfile.write("\n\n")
            except Exception as e:
                outfile.write(f"// [Ошибка чтения файла: {e}]\n\n")

print(f"Успешно! Все файлы собраны в файл {OUTPUT_FILE}")
