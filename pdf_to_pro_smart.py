#!/usr/bin/env python3
"""
PDF to ProPresenter 7 - Smart Bilingual Converter
- Curăță automat header-uri și metadata
- Identifică secțiuni (VERSE, CHORUS, BRIDGE, etc.)
- Aliniază versurile RO-EN paralel
- Generează grupuri în ProPresenter
"""

import sys
import os
import re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from SongEditorPro7Generic import save_song, get_text_block_names

try:
    import pdfplumber
    USE_PDFPLUMBER = True
except ImportError:
    from PyPDF2 import PdfReader
    USE_PDFPLUMBER = False


# Etichete de secțiuni (română și engleză)
SECTION_LABELS = {
    # Română
    'INTRO': 'Intro',
    'VERSE': 'Verse',
    'VERSE 1': 'Verse 1',
    'VERSE 2': 'Verse 2',
    'VERSE 3': 'Verse 3',
    'VERSE 4': 'Verse 4',
    'CHORUS': 'Chorus',
    'REFREN': 'Chorus',
    'BRIDGE': 'Bridge',
    'PUNTE': 'Bridge',
    'TAG': 'Tag',
    'TAG 1': 'Tag 1',
    'TAG 2': 'Tag 2',
    'OUTRO': 'Outro',
    'ENDING': 'Ending',
    'INST': 'Instrumental',
    'INSTRUMENTAL': 'Instrumental',
    'INTER': 'Interlude',
    'INTERLUDE': 'Interlude',
    'PRE-CHORUS': 'Pre-Chorus',
    'PRE CHORUS': 'Pre-Chorus',
}


def extract_text_from_pdf(pdf_path):
    """Extrage textul din PDF folosind pdfplumber (mai bun) sau PyPDF2."""
    lines = []

    if USE_PDFPLUMBER:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    for line in text.split('\n'):
                        lines.append(line.strip())
    else:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                for line in text.split('\n'):
                    lines.append(line.strip())

    return lines


def is_header_line(line, line_index):
    """Detectează dacă o linie e header/metadata."""
    line_lower = line.lower().strip()

    # Verifică pattern-uri de header (indiferent de poziție)
    if '[' in line and ']' in line:  # [Lyrics, 62 bpm, 4/4]
        return True
    if 'bpm' in line_lower:
        return True

    # Structura cântecului: conține ×, și multiple secțiuni separate prin virgulă
    # ex: "Intro, V1, V2, C1, Inter, V3, C1×2, Inst, B1×2"
    if '×' in line or (',' in line and re.search(r'\b(v\d|c\d?|intro|inst|inter|b\d?|tag)\b', line_lower)):
        return True

    # Primele 5 linii - verificări suplimentare
    if line_index < 5:
        # Titlu sau autor (de obicei nu conține cuvinte cheie de secțiuni)
        # Dar conține nume proprii sau titluri
        if line_index < 3 and not is_section_label(line):
            # Dacă nu e secțiune și e în primele 3 linii, probabil e header
            if not any(word in line_lower for word in ['să', 'și', 'pe', 'tu', 'eu', 'te', 'the', 'you', 'we', 'i']):
                # Nu pare a fi vers (nu conține cuvinte comune din versuri)
                if len(line.split()) <= 10:  # Header-urile sunt de obicei scurte
                    return True

    return False


def is_section_label(line):
    """Verifică dacă linia e o etichetă de secțiune."""
    line_clean = line.upper().strip()

    # Verifică exact match
    if line_clean in SECTION_LABELS:
        return SECTION_LABELS[line_clean]

    # Verifică pattern-uri cu numere
    for pattern in ['VERSE', 'TAG', 'CHORUS', 'BRIDGE']:
        match = re.match(rf'^({pattern})\s*(\d*)$', line_clean)
        if match:
            name = match.group(1)
            num = match.group(2)
            if num:
                return f"{name.capitalize()} {num}"
            return name.capitalize()

    return None


def fix_spacing(text):
    """Curăță textul - elimină spații multiple."""
    # Cu pdfplumber textul e deja corect, doar curățăm spații extra
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def parse_song(lines, is_primary=True):
    """
    Parsează versurile și le organizează pe secțiuni.
    Returnează: list of {section: str, lyrics: list}
    """
    sections = []
    current_section = "Verse 1"
    current_lyrics = []

    # Găsim prima linie de conținut (skip headers)
    start_index = 0
    for i, line in enumerate(lines):
        if is_header_line(line, i):
            continue
        if is_section_label(line):
            start_index = i
            break
        # Dacă găsim text normal după headers, începem de acolo
        if line.strip() and i >= 2:
            start_index = i
            break

    for i, line in enumerate(lines[start_index:], start=start_index):
        line = line.strip()

        # Skip linii goale
        if not line:
            continue

        # Skip headers
        if is_header_line(line, i):
            continue

        # Skip numere singure (ex: "1" la final)
        if line.isdigit():
            continue

        # Verifică dacă e etichetă de secțiune
        section_name = is_section_label(line)
        if section_name:
            # Salvează secțiunea anterioară dacă are versuri
            if current_lyrics:
                sections.append({
                    'section': current_section,
                    'lyrics': current_lyrics
                })
            current_section = section_name
            current_lyrics = []
            continue

        # Adaugă linia la versurile curente
        fixed_line = fix_spacing(line)
        current_lyrics.append(fixed_line)

    # Salvează ultima secțiune
    if current_lyrics:
        sections.append({
            'section': current_section,
            'lyrics': current_lyrics
        })

    return sections


def normalize_section_name(name):
    """Normalizează numele secțiunii pentru comparație."""
    # Elimină numerele pentru comparație de bază
    base = re.sub(r'\s*\d+$', '', name).strip()
    return base


def align_sections(ro_sections, en_sections):
    """
    Aliniază secțiunile RO și EN.
    Folosește secțiunile din română ca referință.
    Potrivește flexibil (Tag = Tag 1, Chorus = Chorus 1, etc.)
    """
    aligned = []

    # Creăm un dict pentru secțiunile EN (după bază normalizată)
    en_dict = {}
    en_exact_dict = {}
    for sec in en_sections:
        name = sec['section']
        base = normalize_section_name(name)

        # Dict exact
        if name not in en_exact_dict:
            en_exact_dict[name] = []
        en_exact_dict[name].append(sec['lyrics'])

        # Dict bază (pentru match flexibil)
        if base not in en_dict:
            en_dict[base] = []
        en_dict[base].append(sec['lyrics'])

    # Index pentru a urmări câte de fiecare secțiune am folosit
    en_used = {}
    en_base_used = {}

    for ro_sec in ro_sections:
        section_name = ro_sec['section']
        base_name = normalize_section_name(section_name)
        ro_lyrics = ro_sec['lyrics']

        # Căutăm secțiunea corespunzătoare în EN
        en_lyrics = []

        # Întâi încercăm match exact
        if section_name in en_exact_dict and en_exact_dict[section_name]:
            idx = en_used.get(section_name, 0)
            if idx < len(en_exact_dict[section_name]):
                en_lyrics = en_exact_dict[section_name][idx]
                en_used[section_name] = idx + 1

        # Dacă nu găsim exact, încercăm match pe bază
        if not en_lyrics and base_name in en_dict and en_dict[base_name]:
            idx = en_base_used.get(base_name, 0)
            if idx < len(en_dict[base_name]):
                en_lyrics = en_dict[base_name][idx]
                en_base_used[base_name] = idx + 1

        aligned.append({
            'section': section_name,
            'ro': ro_lyrics,
            'en': en_lyrics
        })

    return aligned


def main():
    print("\n" + "=" * 65)
    print("   PDF → ProPresenter 7 - Smart Bilingual Converter")
    print("   Auto-clean | Section detection | Parallel alignment")
    print("=" * 65 + "\n")

    if len(sys.argv) < 3:
        print("Utilizare:")
        print("  python3 pdf_to_pro_smart.py <pdf_romana.pdf> <pdf_engleza.pdf> [nume]")
        print("\nExemplu:")
        print("  python3 pdf_to_pro_smart.py versuri_ro.pdf versuri_en.pdf 'Noi Te Asteptam'")
        print()
        sys.exit(1)

    pdf_ro = sys.argv[1]
    pdf_en = sys.argv[2]
    song_name = sys.argv[3] if len(sys.argv) > 3 else "Cantec"

    if not os.path.exists(pdf_ro):
        print(f"Eroare: {pdf_ro} nu există!")
        sys.exit(1)
    if not os.path.exists(pdf_en):
        print(f"Eroare: {pdf_en} nu există!")
        sys.exit(1)

    print(f"PDF Română:   {pdf_ro}")
    print(f"PDF Engleză:  {pdf_en}")
    print(f"Nume cântec:  {song_name}")

    # Extragem text
    print("\n[1/4] Extrag textul din PDF-uri...")
    ro_lines = extract_text_from_pdf(pdf_ro)
    en_lines = extract_text_from_pdf(pdf_en)

    # Parsăm și organizăm pe secțiuni
    print("[2/4] Parsez și identific secțiunile...")
    ro_sections = parse_song(ro_lines, is_primary=True)
    en_sections = parse_song(en_lines, is_primary=False)

    print(f"\n  Secțiuni RO găsite:")
    for sec in ro_sections:
        print(f"    - {sec['section']}: {len(sec['lyrics'])} linii")

    print(f"\n  Secțiuni EN găsite:")
    for sec in en_sections:
        print(f"    - {sec['section']}: {len(sec['lyrics'])} linii")

    # Aliniem secțiunile
    print("\n[3/4] Aliniez secțiunile RO-EN...")
    aligned = align_sections(ro_sections, en_sections)

    # Pregătim datele pentru ProPresenter
    text_block_names = get_text_block_names()
    print(f"\n  Text blocks din template: {text_block_names}")

    # Construim listele pentru ProPresenter
    # Format: fiecare linie + linie goală = slide nou
    # Section label la început
    rom_lines_for_pp = []
    eng_lines_for_pp = []

    total_slides = 0

    for section_data in aligned:
        section_name = section_data['section']
        ro_lyrics = section_data['ro']
        en_lyrics = section_data['en']

        # Aliniem liniile din secțiune
        max_lines = max(len(ro_lyrics), len(en_lyrics))

        for i in range(max_lines):
            # Separator pentru slide nou
            if total_slides > 0:
                rom_lines_for_pp.append("")
                eng_lines_for_pp.append("")

            # Prima linie din secțiune primește label-ul
            if i == 0:
                rom_lines_for_pp.append(section_name)
                eng_lines_for_pp.append(section_name)

            # Adăugăm versul
            ro_line = ro_lyrics[i] if i < len(ro_lyrics) else ""
            en_line = en_lyrics[i] if i < len(en_lyrics) else ""

            rom_lines_for_pp.append(ro_line)
            eng_lines_for_pp.append(en_line)

            total_slides += 1

    print(f"  Total slide-uri: {total_slides}")

    song_texts = {
        'Eng': eng_lines_for_pp,
        'Rom': rom_lines_for_pp
    }

    # Generăm fișierul .pro
    output_dir = os.path.dirname(os.path.abspath(pdf_ro))
    output_name = os.path.join(output_dir, song_name.replace(' ', '_'))

    print(f"\n[4/4] Generez fișierul ProPresenter...")
    save_song(text_block_names, song_texts, 1, output_name)

    # Afișăm preview
    print("\n" + "-" * 65)
    print("PREVIEW (primele slide-uri):")
    print("-" * 65)

    preview_count = 0
    for section_data in aligned:
        if preview_count >= 8:
            print("  ...")
            break
        section_name = section_data['section']
        ro_lyrics = section_data['ro']
        en_lyrics = section_data['en']

        print(f"\n  [{section_name}]")
        max_lines = min(3, max(len(ro_lyrics), len(en_lyrics)))
        for i in range(max_lines):
            ro = ro_lyrics[i] if i < len(ro_lyrics) else "(lipsă)"
            en = en_lyrics[i] if i < len(en_lyrics) else "(missing)"
            print(f"    RO: {ro}")
            print(f"    EN: {en}")
            preview_count += 1
            if preview_count >= 8:
                break

    print("\n" + "=" * 65)
    print("GATA!")
    print("=" * 65)
    print(f"\nFișier generat: {output_name}.pro")
    print(f"\nImportă în ProPresenter: File → Import → Presentation")
    print()


if __name__ == "__main__":
    main()
