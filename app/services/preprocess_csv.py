# app/services/preprocess_csv.py

import csv
from io import StringIO


class CSVPreprocessor:

    @staticmethod
    def process(file_path):
        """
        Читает CSV файл, удаляет пустые строки и строки без данных.
        """
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()

        cleaned_lines = []

        for line in lines:
            line = line.strip()

            # Пропускаем пустые строки
            if not line:
                if cleaned_lines and cleaned_lines[-1] != '':
                    cleaned_lines.append('')  # Разделитель между таблицами
                continue

            # Пропускаем строки, состоящие только из запятых
            if line.replace(',', '').strip() == '':
                continue

            # Проверяем, есть ли в строке хоть какие-то данные кроме заголовка
            parts = [p.strip() for p in line.split(',')]

            # Если все части пустые - пропускаем
            if all(p == '' for p in parts):
                continue

            cleaned_lines.append(line)

        # Убираем множественные пустые строки в конце
        while cleaned_lines and cleaned_lines[-1] == '':
            cleaned_lines.pop()

        return '\n'.join(cleaned_lines)