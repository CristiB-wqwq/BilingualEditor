#!/usr/bin/env python3
"""
PDF to ProPresenter 7 - Convertor versuri bilingve (RO + EN)
Generează fișier .pro cu 2 text labels separate pentru Stage Display
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from SongEditorPro7Generic import save_song, get_text_block_names
from PyPDF2 import PdfReader


def extract_text_from_pdf(pdf_path):
    """Extrage textul din PDF."""
    reader = PdfReader(pdf_path)
    lines = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            for line in text.split('\n'):
                stripped = line.strip()
                lines.append(stripped)  # Păstrăm și liniile goale
    return lines


def group_into_stanzas(lines, lines_per_stanza=4):
    """Grupează liniile în strofe."""
    non_empty_lines = [l for l in lines if l.strip()]
    empty_count = len(lines) - len(non_empty_lines)

    # Dacă avem linii goale semnificative, le folosim ca separatori
    if empty_count >= 2:
        stanzas = []
        current_stanza = []
        for line in lines:
            if line.strip():
                current_stanza.append(line)
            else:
                if current_stanza:
                    stanzas.append(current_stanza)
                    current_stanza = []
        if current_stanza:
            stanzas.append(current_stanza)
        return stanzas

    # Altfel, grupăm după număr fix de linii
    stanzas = []
    for i in range(0, len(non_empty_lines), lines_per_stanza):
        stanza_lines = non_empty_lines[i:i + lines_per_stanza]
        if stanza_lines:
            stanzas.append(stanza_lines)
    return stanzas


def main():
    print("\n" + "=" * 60)
    print("   PDF → ProPresenter 7 - Versuri Bilingve (RO + EN)")
    print("   Cu 2 Label-uri separate pentru Stage Display")
    print("=" * 60 + "\n")

    if len(sys.argv) < 3:
        print("Utilizare:")
        print("  python3 pdf_to_pro.py <pdf_romana.pdf> <pdf_engleza.pdf> [nume] [linii/strofa]")
        print("\nExemplu:")
        print("  python3 pdf_to_pro.py versuri_ro.pdf versuri_en.pdf 'Amazing Grace' 4")
        print()
        sys.exit(1)

    pdf_ro = sys.argv[1]
    pdf_en = sys.argv[2]
    song_name = sys.argv[3] if len(sys.argv) > 3 else "Cantec"
    lines_per_stanza = int(sys.argv[4]) if len(sys.argv) > 4 else 4

    # Verificăm fișierele
    if not os.path.exists(pdf_ro):
        print(f"Eroare: {pdf_ro} nu există!")
        sys.exit(1)
    if not os.path.exists(pdf_en):
        print(f"Eroare: {pdf_en} nu există!")
        sys.exit(1)

    print(f"PDF Română:   {pdf_ro}")
    print(f"PDF Engleză:  {pdf_en}")
    print(f"Nume cântec:  {song_name}")
    print(f"Linii/strofă: {lines_per_stanza}")

    # Extragem text
    print("\nExtrag textul din PDF-uri...")
    ro_lines = extract_text_from_pdf(pdf_ro)
    en_lines = extract_text_from_pdf(pdf_en)

    # Grupăm în strofe
    print("Grupez în strofe...")
    ro_stanzas = group_into_stanzas(ro_lines, lines_per_stanza)
    en_stanzas = group_into_stanzas(en_lines, lines_per_stanza)

    print(f"  Română:  {len(ro_stanzas)} strofe")
    print(f"  Engleză: {len(en_stanzas)} strofe")

    # Aliniem strofele
    min_stanzas = min(len(ro_stanzas), len(en_stanzas))
    if len(ro_stanzas) != len(en_stanzas):
        print(f"\n  Atentie: numar diferit de strofe! Se folosesc {min_stanzas}.")

    # Pregătim datele pentru ProPresenter
    # Fiecare LINIE = un SLIDE separat (nu strofă)
    text_block_names = get_text_block_names()  # ['Eng', 'Rom']
    print(f"\nText blocks din template: {text_block_names}")

    # Extragem toate liniile non-goale
    ro_all_lines = [l for l in ro_lines if l.strip()]
    en_all_lines = [l for l in en_lines if l.strip()]

    min_lines = min(len(ro_all_lines), len(en_all_lines))
    if len(ro_all_lines) != len(en_all_lines):
        print(f"\n  Atentie: numar diferit de linii! RO={len(ro_all_lines)}, EN={len(en_all_lines)}")
        print(f"  Se folosesc primele {min_lines} linii.")

    print(f"  Total slide-uri: {min_lines}")

    # Construim listele - UN VERS PER SLIDE
    rom_lines_for_pp = []
    eng_lines_for_pp = []

    for i in range(min_lines):
        # Linie goală între slide-uri (separator)
        if i > 0:
            rom_lines_for_pp.append("")
            eng_lines_for_pp.append("")

        # Adăugăm versul
        rom_lines_for_pp.append(ro_all_lines[i])
        eng_lines_for_pp.append(en_all_lines[i])

    # Mapăm corect: 'Eng' -> engleză, 'Rom' -> română
    song_texts = {
        'Eng': eng_lines_for_pp,
        'Rom': rom_lines_for_pp
    }

    # Generăm fișierul .pro
    output_dir = os.path.dirname(os.path.abspath(pdf_ro))
    output_name = os.path.join(output_dir, song_name.replace(' ', '_'))

    print(f"\nGenerez fișierul ProPresenter...")
    # 1 linie per slide
    save_song(text_block_names, song_texts, 1, output_name)

    print("\n" + "=" * 60)
    print("GATA!")
    print("=" * 60)
    print(f"\nFișier generat: {output_name}.pro")
    print("\nPentru a importa în ProPresenter 7:")
    print("  1. File → Import → Presentation")
    print(f"  2. Selectează: {song_name.replace(' ', '_')}.pro")
    print("\nPentru Stage Display cu doar Română:")
    print("  1. Screens → Stage Display → Edit Layout")
    print("  2. Adaugă element care afișează doar 'Rom'")
    print()


if __name__ == "__main__":
    main()
