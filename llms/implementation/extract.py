import re
import sys

def extract_sections(filepath):
    sections = []
    with open(filepath, 'r') as f:
        lines = f.readlines()

    capture = False
    buffer = []

    for line in lines:
        if '(* INSERT_CHATGPT_CODE *)' in line:
            capture = True
            buffer = []  # start new section, skip the marker line
        elif capture and re.match(r'^module Test\w+', line):
            sections.append(''.join(buffer))  # do not include module line
            capture = False
        elif capture:
            buffer.append(line)

    return sections

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python extract_sections.py <path_to_file>")
        sys.exit(1)

    file_path = sys.argv[1]
    sections = extract_sections(file_path)

    for i, section in enumerate(sections):
        print(f'{section}')

