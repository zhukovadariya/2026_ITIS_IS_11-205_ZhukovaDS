import os
import re
import sys
from pathlib import Path
import pymorphy2

class TextProcessor:
    def __init__(self, input_dir="downloaded_pages", output_dir="processed_pages", stopwords_file="task2/stopwords.txt"):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.stopwords_file = stopwords_file
        self.morph = pymorphy2.MorphAnalyzer()
        self.stop_words = self.load_stop_words()

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def load_stop_words(self):
        stop_words = set()

        try:
            with open(self.stopwords_file, 'r', encoding='utf-8') as f:
                for line in f:
                    word = line.strip()
                    if word and not word.startswith('#'):
                        stop_words.add(word.lower())

        except Exception as e:
            print(f"Ошибка при загрузке стоп-слов: {str(e)}")

        return stop_words

    def tokenize(self, text):
        text = text.lower()
        tokens = re.findall(r'[а-яё]+', text, re.UNICODE)

        return tokens

    def lemmatize(self, tokens):
        lemmatized_tokens = []

        for token in tokens:
            try:
                parsed = self.morph.parse(token)[0]
                lemma = parsed.normal_form
                lemmatized_tokens.append(lemma)
            except Exception as e:
                lemmatized_tokens.append(token)

        return lemmatized_tokens

    def remove_stop_words(self, tokens):
        filtered_tokens = []
        for token in tokens:
            if token not in self.stop_words and len(token) > 1:
                filtered_tokens.append(token)

        return filtered_tokens

    def process_text(self, text):
        tokens = self.tokenize(text)
        print(f"Токенов: {len(tokens)}")

        lemmatized = self.lemmatize(tokens)
        print(f"После лемматизации: {len(lemmatized)}")

        filtered = self.remove_stop_words(lemmatized)
        print(f"После удаления стоп-слов: {len(filtered)}")

        return filtered

    def process_document(self, filename, doc_num):
        input_path = os.path.join(self.input_dir, filename)

        if not os.path.exists(input_path):
            print(f"Файл {filename} не найден")
            return 0

        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                text = f.read()
        except Exception as e:
            print(f" Ошибка чтения файла {filename}: {str(e)}")
            return 0

        print(f"\nОбработка документа {filename}")

        processed_tokens = self.process_text(text)

        try:
            doc_num_int = int(doc_num) if isinstance(doc_num, str) else doc_num
            output_filename = f"processed_{doc_num_int:04d}.txt"
        except (ValueError, TypeError):
            output_filename = f"processed_{doc_num}.txt"

        output_path = os.path.join(self.output_dir, output_filename)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(' '.join(processed_tokens))

        return len(processed_tokens)

    def process_all_documents(self):
        if not os.path.exists(self.input_dir):
            print(f"Директория {self.input_dir} не найдена")
            return 0

        input_files = sorted([f for f in os.listdir(self.input_dir) if f.endswith('.txt')])

        if not input_files:
            print(f"В директории {self.input_dir} не найдено текстовых файлов")
            return 0

        total_tokens = 0
        processed_count = 0
        skipped_count = 0

        for filename in input_files:
            doc_num = filename.split('.')[0]

            try:
                token_count = self.process_document(filename, doc_num)
                if token_count > 0:
                    total_tokens += token_count
                    processed_count += 1
                else:
                    skipped_count += 1
            except Exception as e:
                print(f"Ошибка при обработке {filename}: {str(e)}")
                skipped_count += 1

        return processed_count


def main():
    input_dir = "downloaded_pages"

    if not os.path.exists(input_dir):
        print(f"\nОшибка: директория '{input_dir}' не найдена.")
        sys.exit(1)

    processor = TextProcessor(input_dir)
    processed = processor.process_all_documents()


if __name__ == "__main__":
    main()