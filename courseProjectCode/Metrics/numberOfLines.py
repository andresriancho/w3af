import os

def count_lines_by_language(directory, extensions_by_language):
    counts = {language: 0 for language in extensions_by_language}
    total_lines = 0

    for root, _, files in os.walk(directory):
        for file in files:
            for language, extensions in extensions_by_language.items():
                if any(file.endswith(ext) for ext in extensions):
                    filepath = os.path.join(root, file)
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        line_count = len(lines)
                        counts[language] += line_count
                        total_lines += line_count
                    break

    results = []
    for language, lines in counts.items():
        percent = (lines / total_lines * 100) if total_lines > 0 else 0
        results.append((language, lines, percent))

    results.sort(key=lambda x: x[1], reverse=True)
    return results, total_lines

extensions_by_language = {
    'Python': ['.py'],
    'HTML': ['.html', '.htm'],
    'Roff': ['.roff', '.man', '.mdoc'],
    'JavaScript': ['.js'],
    'Shell': ['.sh', '.bash'],
    'C': ['.c', '.h'],
}

project_path = './w3af'

result, total = count_lines_by_language(project_path, extensions_by_language)

print(f'Total lines of code: {total}\n')
for language, lines, pct in result:
    print(f'{language}: {lines} lines, {pct:.1f}%')
