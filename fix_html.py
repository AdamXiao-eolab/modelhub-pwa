#!/usr/bin/env python3
"""Fix all encoding issues in ModelHub HTML files."""
import re, os, shutil

BASE = os.path.dirname(os.path.abspath(__file__))
files = ["index.html", "pricing.html", "docs.html", "privacy.html"]

def fix_file(filename):
    path = os.path.join(BASE, filename)
    with open(path, "rb") as f:
        raw = f.read()
    
    # Detect if BOM exists
    if raw[:3] == b'\xef\xbb\xbf':
        raw = raw[3:]  # Remove UTF-8 BOM
    
    text = raw.decode("utf-8", errors="replace")
    
    changes = []
    original = text
    
    # 1. Fix broken closing tags: "→?/a>" → "</a>"
    # This pattern: arrow + ? + /a>
    # Important: match any closing tag that got corrupted
    text = re.sub(r'→\?/a>', '</a>', text)
    
    # 2. Fix broken "→?>" in other contexts
    text = re.sub(r'→\?(\w)', r'→\1', text)
    
    # 3. Fix standalone "→?/" patterns
    text = re.sub(r'→\?/(\w)', r'→</\1', text)
    
    # 4. Fix Unicode replacement chars in content
    # Replace common garbled characters
    replacements = {
        '\u2014': '—',  # em dash
        '\u2022': '•',  # bullet
        '\u2713': '✓',  # checkmark
        '\u2714': '✔',  # heavy checkmark
        '\u2605': '★',  # star
        '\u2728': '✨',  # sparkles
        '\uf0e7': '',    # unknown
    }
    
    # 5. Fix specific garbled sequences
    fix_map = {
        'â"': '✓',     # check mark corruption
        'âŒ': '',        # various corruption
        'é': '★',       # star corruption
        'é': '→',       # arrow corruption
        'é¥': '→',      # arrow corruption
        'æ¼': '©',       # copyright corruption  
        'è': '×',       # times corruption
        'ç´': '',         # garbage
        'ğŸ': '',         # emoji corruption
        'ĞŸ': '',
        'ğŸ': '',
        'ē?' : '',
        'EUR': '',
    }
    
    # 6. Fix the pricing.html specific issues: è³ → ×
    text = re.sub(r'è³', '×', text)
    text = re.sub(r'é¥?', '→', text)
    text = re.sub(r'é¥o', '→', text)
    text = re.sub(r'é?', '★', text)
    text = re.sub(r'æ¼?', '©', text)
    text = re.sub(r'æ¼', '©', text)
    
    # 7. Fix the "鈥?" pattern → —
    text = text.replace('\u2019', "'")  # right single quote
    text = text.replace('\u2018', "'")  # left single quote
    text = text.replace('\u201c', '"')  # left double quote  
    text = text.replace('\u201d', '"')  # right double quote
    
    # 8. Fix Unicode escape issues in CSS content
    # "content: '鉁?" → should be a checkmark or star
    text = text.replace("鉁?", "★")
    
    # 9. Fix broken BOM in content
    text = text.replace('\ufeff', '')
    
    # 10. Fix title encoding garbles
    text = text.replace("鈥?", "—")  # em dash in title
    
    # Check for "©" in footer
    if "2026 ModelHub" in text and "©" not in text:
        text = text.replace("2026 ModelHub", "© 2026 ModelHub")
    
    # Final check: ensure no remaining "→?/" patterns
    text = re.sub(r'→\?', '→', text)
    
    if text != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"✅ {filename} — FIXED")
    else:
        print(f"  {filename} — No changes needed")
    
    return text != original

for f in files:
    fix_file(f)

print("\nDone! Now run: check_html_fix.py to verify")
