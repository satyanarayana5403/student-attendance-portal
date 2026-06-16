"""
Fix mojibake encoding issues in all HTML template files.
These occur when UTF-8 multi-byte sequences were saved through
a Windows-1252 (cp1252) codec, turning emojis/special chars into
garbled sequences of Windows special characters.
"""
import os
import glob

PROJECT_DIR = r'c:\Users\knvv1\Desktop\student attendence portal project'
TEMPLATES_DIR = os.path.join(PROJECT_DIR, 'templates')

# Windows-1252 byte -> Python codepoint mapping for 0x80-0x9F range
# (standard cp1252 decoding of the "extra" bytes)
CP1252_MAP = {
    0x80: 0x20ac,  # €
    0x82: 0x201a,  # ‚
    0x83: 0x0192,  # ƒ
    0x84: 0x201e,  # „
    0x85: 0x2026,  # …
    0x86: 0x2020,  # †
    0x87: 0x2021,  # ‡
    0x88: 0x02c6,  # ˆ
    0x89: 0x2030,  # ‰
    0x8a: 0x0160,  # Š
    0x8b: 0x2039,  # ‹
    0x8c: 0x0152,  # Œ
    0x8e: 0x017d,  # Ž
    0x91: 0x2018,  # '
    0x92: 0x2019,  # '
    0x93: 0x201c,  # "
    0x94: 0x201d,  # "
    0x95: 0x2022,  # •
    0x96: 0x2013,  # –
    0x97: 0x2014,  # —
    0x98: 0x02dc,  # ˜
    0x99: 0x2122,  # ™
    0x9a: 0x0161,  # š
    0x9b: 0x203a,  # ›
    0x9c: 0x0153,  # œ
    0x9e: 0x017e,  # ž
    0x9f: 0x0178,  # Ÿ
}

# Reverse: cp1252 codepoint -> original byte value
REVERSE_MAP = {v: k for k, v in CP1252_MAP.items()}

# Also include the straightforward latin-1 range (0xa0-0xff maps to itself)
for b in range(0xa0, 0x100):
    REVERSE_MAP[b] = b

MOJIBAKE_TRIGGERS = set(REVERSE_MAP.keys())


def fix_mojibake(text):
    """Convert cp1252-decoded text back to correct Unicode."""
    result = []
    i = 0
    chars = list(text)
    n = len(chars)

    while i < n:
        c = chars[i]
        code = ord(c)

        if code in MOJIBAKE_TRIGGERS:
            # Collect consecutive mojibake chars and convert back to bytes
            byte_seq = []
            j = i
            while j < n and ord(chars[j]) in MOJIBAKE_TRIGGERS:
                byte_seq.append(REVERSE_MAP[ord(chars[j])])
                j += 1

            if len(byte_seq) >= 2:
                try:
                    decoded = bytes(byte_seq).decode('utf-8')
                    result.append(decoded)
                    i = j
                    continue
                except (UnicodeDecodeError, ValueError):
                    pass  # Not a valid UTF-8 sequence, keep as-is

        result.append(c)
        i += 1

    return ''.join(result)


def fix_file(path):
    with open(path, encoding='utf-8') as f:
        original = f.read()

    fixed = fix_mojibake(original)

    if fixed != original:
        with open(path, 'w', encoding='utf-8', newline='') as f:
            f.write(fixed)
        return True
    return False


def main():
    patterns = [
        os.path.join(TEMPLATES_DIR, '*.html'),
        os.path.join(PROJECT_DIR, 'static', '**', '*.js'),
        os.path.join(PROJECT_DIR, 'static', '**', '*.css'),
    ]

    fixed_count = 0
    checked_count = 0

    for pattern in patterns:
        for path in glob.glob(pattern, recursive=True):
            if '.venv' in path or '__pycache__' in path:
                continue
            checked_count += 1
            try:
                if fix_file(path):
                    rel = os.path.relpath(path, PROJECT_DIR)
                    print(f'  [FIXED] {rel}')
                    fixed_count += 1
            except Exception as e:
                print(f'  [ERROR] {path}: {e}')

    print(f'\nChecked {checked_count} files, fixed {fixed_count} files.')


if __name__ == '__main__':
    main()
