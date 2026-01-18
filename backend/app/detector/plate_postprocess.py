import re

LETTER_TO_DIGIT = {
    'O': '0', 'Q': '0', 'D': '0',
    'I': '1', 'L': '1',
    'Z': '2',
    'S': '5',
    'B': '8',
    'G': '6',
}

DIGIT_TO_LETTER = {
    '0': 'O',
    '1': 'I',
    '2': 'Z',
    '5': 'S',
    '6': 'G',
    '8': 'B',
}

COUNTRY_SYNTAX = {
    "IN": ["L","L","D","D","L","L","D","D","D","D"],   # KA01AB1234
    "UK": ["L","L","D","D","L","L","L"],              # AB12CDE
    "DE": ["L","L","L","D","D","D","D"],              # BMW1234
}

def apply_plate_syntax(text: str, country="IN") -> str:
    text = re.sub(r'[^A-Z0-9]', '', text.upper())
    pattern = COUNTRY_SYNTAX.get(country)

    # If country unknown or length mismatch → return cleaned text
    if not pattern or len(text) != len(pattern):
        return text

    corrected = list(text)

    for i, expected in enumerate(pattern):
        c = corrected[i]

        if expected == "D" and c.isalpha():
            corrected[i] = LETTER_TO_DIGIT.get(c, c)

        elif expected == "L" and c.isdigit():
            corrected[i] = DIGIT_TO_LETTER.get(c, c)

    return "".join(corrected)
