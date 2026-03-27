import os
import re
import sys
from collections import defaultdict

class InvertedIndex:
    def __init__(self, processed_dir="processed_pages"):
        self.processed_dir = processed_dir
        self.index = defaultdict(set)
        self.documents = {}
        self.doc_count = 0

    def build_index(self):
        if not os.path.exists(self.processed_dir):
            print(f"Директория {self.processed_dir} не найдена")
            return False

        files = sorted([f for f in os.listdir(self.processed_dir)
                        if f.startswith('processed_') and f.endswith('.txt')])

        if not files:
            print("Нет документов")
            return False

        for filename in files:
            doc_num = filename.replace('processed_', '').replace('.txt', '')

            filepath = os.path.join(self.processed_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    terms = content.split()

                self.documents[doc_num] = terms

                for term in terms:
                    self.index[term].add(doc_num)

                self.doc_count += 1
                print(f"Обработан документ {doc_num}: {len(terms)} терминов")

            except Exception as e:
                print(f"Ошибка при обработке {filename}: {str(e)}")

        return True

    def save_index(self, index_file="inverted_index.txt"):
        sorted_terms = sorted(self.index.keys())

        with open(index_file, 'w', encoding='utf-8') as f:
            for term in sorted_terms:
                doc_list = sorted(list(self.index[term]))
                doc_list_str = ', '.join(doc_list)
                f.write(f"{term} - {doc_list_str}\n")

        return True

    def load_index(self, index_file="inverted_index.txt"):
        if not os.path.exists(index_file):
            print(f"Файл индекса {index_file} не найден")
            return False

        self.index.clear()

        with open(index_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                if '-' in line:
                    term, docs_str = line.split('-')
                    term = term.strip()
                    docs_str = docs_str.strip()

                    if docs_str:
                        docs = docs_str.split(', ')
                        self.index[term] = set(docs)

        return True

    def parse_query(self, query):
        query = query.replace('&', ' И ')
        query = query.replace('|', ' ИЛИ ')
        query = query.replace('!', ' НЕ ')

        tokens = []
        current_token = ""
        i = 0
        while i < len(query):
            char = query[i]

            if query[i:i + 3] == ' И ':
                if current_token.strip():
                    tokens.append(current_token.strip())
                tokens.append('И')
                i += 3
                current_token = ""
            elif query[i:i + 5] == ' ИЛИ ':
                if current_token.strip():
                    tokens.append(current_token.strip())
                tokens.append('ИЛИ')
                i += 5
                current_token = ""
            elif query[i:i + 4] == ' НЕ ':
                if current_token.strip():
                    tokens.append(current_token.strip())
                tokens.append('НЕ')
                i += 4
                current_token = ""
            else:
                current_token += char
                i += 1

        if current_token.strip():
            tokens.append(current_token.strip())

        return tokens

    def evaluate_query(self, tokens):
        precedence = {'НЕ': 3, 'И': 2, 'ИЛИ': 1}

        output = []
        operators = []

        for token in tokens:
            if token in precedence:
                while (operators and operators[-1] != '(' and
                       precedence.get(operators[-1], 0) >= precedence.get(token, 0)):
                    output.append(operators.pop())
                operators.append(token)
            elif token == '(':
                operators.append(token)
            elif token == ')':
                while operators and operators[-1] != '(':
                    output.append(operators.pop())
                if operators and operators[-1] == '(':
                    operators.pop()
            else:
                output.append(token)

        while operators:
            output.append(operators.pop())

        stack = []
        for token in output:
            if token in precedence:
                if token == 'НЕ':
                    if not stack:
                        return set()
                    operand = stack.pop()
                    if isinstance(operand, set):
                        result = self.not_operation(operand)
                    else:
                        result = self.not_operation(self.get_documents_for_term(operand))
                    stack.append(result)
                else:
                    if len(stack) < 2:
                        return set()
                    right = stack.pop()
                    left = stack.pop()

                    if isinstance(left, str):
                        left = self.get_documents_for_term(left)
                    if isinstance(right, str):
                        right = self.get_documents_for_term(right)

                    if token == 'И':
                        result = self.and_operation(left, right)
                    elif token == 'ИЛИ':
                        result = self.or_operation(left, right)
                    else:
                        result = set()

                    stack.append(result)
            else:
                stack.append(token)

        if not stack:
            return set()

        result = stack[0]
        if isinstance(result, str):
            result = self.get_documents_for_term(result)

        return result

    def get_documents_for_term(self, term):
        return self.index.get(term, set())

    def and_operation(self, set1, set2):
        return set1 & set2

    def or_operation(self, set1, set2):
        return set1 | set2

    def not_operation(self, docs_set):
        all_docs = set(self.documents.keys())
        return all_docs - docs_set

    def search(self, query):
        tokens = self.parse_query(query)

        result = self.evaluate_query(tokens)

        result_sorted = sorted(result, key=lambda x: int(x))

        if result_sorted:
            print(f"\nРезультат: {len(result_sorted)} документов")
            print(f"Документы: {', '.join(result_sorted)}")
        else:
            print("Документы не найдены")

        return result_sorted


def main():
    index = InvertedIndex()

    if not index.load_index():
        if not index.build_index():
            print("Не удалось построить индекс")
            return
        index.save_index()

    while True:
        query = input("\nЗапрос: ").strip()
        if query.lower() in ['выход', 'exit', 'quit', 'q']:
            break

        if not query:
            continue

        result = index.search(query)


if __name__ == "__main__":
    main()