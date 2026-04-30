from pathlib import Path

def ensure_folder(folder):
    Path(folder).mkdir(parents=True, exist_ok=True)
    return folder

def get_txt_files(folder):
    return list(Path(folder).glob('*.txt'))

def read_text_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def write_text_file(filepath, content):
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)