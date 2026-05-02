#!/usr/bin/env python3
"""
ProPresenter Bilingual Editor - GUI (CustomTkinter Dark Theme)
Interfață grafică modernă pentru crearea de prezentări bilingve (RO + EN)
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    DND_SUPPORT = True
except ImportError:
    DND_SUPPORT = False

try:
    import pdfplumber
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("Warning: pdfplumber not installed. PDF import disabled.")

from SongEditorPro7Generic import save_song, get_text_block_names

# --- Appearance ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# --- Constants ---
SECTION_LABELS = [
    'VERSE', 'CHORUS', 'BRIDGE', 'TAG', 'INTRO', 'OUTRO',
    'REFREN', 'PUNTE', 'INST', 'INTERLUDE', 'PRE-CHORUS',
    'PRECHORUS', 'ENDING', 'VAMP', 'TURNAROUND', 'BLANK', 'EMPTY',
]
ACCENT_YELLOW = "#F0C040"
COLOR_GREEN = "#2ECC71"
COLOR_RED = "#E74C3C"
COLOR_MUTED = "#888888"
FONT_MONO = ("Courier New", 13)
FONT_MONO_BOLD = ("Courier New", 13, "bold")

# Section colors matching ProPresenter group colors
SECTION_COLORS = {
    'verse': '#3B82F6',
    'chorus': '#E91E63',
    'bridge': '#9C27B0',
    'prechorus': '#F06292',
    'pre-chorus': '#F06292',
    'tag': '#FF5722',
    'intro': '#FFC107',
    'ending': '#FFC107',
    'outro': '#FFC107',
    'interlude': '#4CAF50',
    'vamp': '#4CAF50',
    'turnaround': '#4CAF50',
    'blank': '#666666',
    'empty': '#666666',
}


class BilingualEditorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ProPresenter Bilingual Editor")
        self.geometry("1300x820")
        self.minsize(900, 600)

        # Enable drag & drop if available
        if DND_SUPPORT:
            try:
                self._tkdnd_version = TkinterDnD._require(self)
            except Exception:
                pass

        # Variables
        self.song_name = ctk.StringVar(value="Cantec Nou")
        self.lines_per_slide = ctk.StringVar(value="2")
        self.status_text = ctk.StringVar(value="Gata de lucru")
        self._instructions_visible = False
        self._syncing_scroll = False

        self._build_layout()
        self._bind_events()
        self._setup_drag_drop()

    # ------------------------------------------------------------------ #
    #  Layout                                                             #
    # ------------------------------------------------------------------ #
    def _build_layout(self):
        # Grid: sidebar (col 0) | editors (col 1) ; status bar (row 1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._build_sidebar()
        self._build_editors()
        self._build_status_bar()

    # --- Sidebar ---
    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        # App title
        ctk.CTkLabel(
            sidebar, text="Bilingual\nEditor",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(pady=(24, 20))

        # Song name
        ctk.CTkLabel(sidebar, text="Nume cantec:", anchor="w").pack(
            padx=16, pady=(10, 2), anchor="w")
        ctk.CTkEntry(sidebar, textvariable=self.song_name).pack(
            padx=16, fill="x")

        # Lines per slide
        ctk.CTkLabel(sidebar, text="Linii / slide:", anchor="w").pack(
            padx=16, pady=(16, 2), anchor="w")
        ctk.CTkOptionMenu(
            sidebar, variable=self.lines_per_slide,
            values=["1", "2", "3", "4"], width=80,
        ).pack(padx=16, anchor="w")

        # Separator
        ctk.CTkFrame(sidebar, height=2, fg_color=("gray70", "gray30")).pack(
            fill="x", padx=16, pady=20)

        # Import buttons
        ctk.CTkButton(
            sidebar, text="Import PDF  RO",
            command=self.import_pdf_ro,
            fg_color="#3B82F6", hover_color="#2563EB",
        ).pack(padx=16, pady=4, fill="x")

        ctk.CTkButton(
            sidebar, text="Import PDF  EN",
            command=self.import_pdf_en,
            fg_color="#3B82F6", hover_color="#2563EB",
        ).pack(padx=16, pady=4, fill="x")

        # Separator
        ctk.CTkFrame(sidebar, height=2, fg_color=("gray70", "gray30")).pack(
            fill="x", padx=16, pady=20)

        # Preview button
        ctk.CTkButton(
            sidebar, text="Preview Slides",
            command=self.show_preview,
            fg_color="#8B5CF6", hover_color="#7C3AED",
            height=36, font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(padx=16, pady=(0, 8), fill="x")

        # Generate button
        ctk.CTkButton(
            sidebar, text="Genereaza .PRO",
            command=self.generate_pro,
            fg_color=COLOR_GREEN, hover_color="#27AE60",
            height=42, font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(padx=16, fill="x")

        # Spacer pushes help button to bottom
        sidebar.pack_propagate(False)
        spacer = ctk.CTkFrame(sidebar, fg_color="transparent")
        spacer.pack(fill="both", expand=True)

        # Help / Instructions toggle
        self._help_btn = ctk.CTkButton(
            sidebar, text="?  Instructiuni",
            command=self._toggle_instructions,
            fg_color="transparent", border_width=1,
            border_color="gray50", hover_color=("gray75", "gray25"),
            height=30, font=ctk.CTkFont(size=12),
        )
        self._help_btn.pack(padx=16, pady=(0, 8), fill="x")

        # Collapsible instructions frame (hidden by default)
        self._instructions_frame = ctk.CTkFrame(sidebar, fg_color=("gray85", "gray20"))
        instructions_text = (
            "FORMAT:\n"
            "Fiecare linie = un slide.\n\n"
            "SECTIUNI:\n"
            "Scrie pe linie separata:\n"
            "Verse 1, Chorus, Bridge,\n"
            "Tag, Intro, Outro etc.\n\n"
            "IMPORTANT:\n"
            "Nr. linii RO = Nr. linii EN\n"
            "(fara sectiuni)"
        )
        ctk.CTkLabel(
            self._instructions_frame, text=instructions_text,
            justify="left", anchor="nw",
            font=ctk.CTkFont(size=11),
            wraplength=180,
        ).pack(padx=8, pady=8)

    # --- Editors ---
    def _build_editors(self):
        editor_area = ctk.CTkFrame(self, fg_color="transparent")
        editor_area.grid(row=0, column=1, sticky="nsew", padx=(4, 10), pady=10)
        editor_area.grid_rowconfigure(1, weight=1)
        editor_area.grid_columnconfigure(0, weight=1)
        editor_area.grid_columnconfigure(1, weight=1)

        # Column headers
        ctk.CTkLabel(
            editor_area, text="ROMANA",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=8, pady=(0, 4))

        ctk.CTkLabel(
            editor_area, text="ENGLISH",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=1, sticky="w", padx=8, pady=(0, 4))

        # RO textbox
        self.ro_text = ctk.CTkTextbox(
            editor_area, font=FONT_MONO, wrap="word",
            corner_radius=8, undo=True,
        )
        self.ro_text.grid(row=1, column=0, sticky="nsew", padx=(4, 2))
        self.ro_text.insert("1.0", self._placeholder("ro"))

        # EN textbox
        self.en_text = ctk.CTkTextbox(
            editor_area, font=FONT_MONO, wrap="word",
            corner_radius=8, undo=True,
        )
        self.en_text.grid(row=1, column=1, sticky="nsew", padx=(2, 4))
        self.en_text.insert("1.0", self._placeholder("en"))

    # --- Status bar ---
    def _build_status_bar(self):
        bar = ctk.CTkFrame(self, height=32, corner_radius=0)
        bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        bar.grid_propagate(False)

        self.line_count_label = ctk.CTkLabel(
            bar, text="RO: 0 linii | EN: 0 linii",
            font=ctk.CTkFont(size=12),
        )
        self.line_count_label.pack(side="left", padx=12)

        self.status_label = ctk.CTkLabel(
            bar, textvariable=self.status_text,
            font=ctk.CTkFont(size=12), text_color=COLOR_MUTED,
        )
        self.status_label.pack(side="right", padx=12)

    # ------------------------------------------------------------------ #
    #  Event bindings                                                     #
    # ------------------------------------------------------------------ #
    def _bind_events(self):
        # Live line counter + section highlight on any text change
        for tb in (self.ro_text, self.en_text):
            tb.bind("<KeyRelease>", lambda e: self._on_text_change())
            tb.bind("<ButtonRelease>", lambda e: self._on_text_change())
            # Catch paste via Cmd/Ctrl-V
            tb.bind("<<Paste>>", lambda e: self.after(50, self._on_text_change))

        # Sync scroll
        self._hook_scroll_sync()

    # ------------------------------------------------------------------ #
    #  Drag & Drop                                                        #
    # ------------------------------------------------------------------ #
    def _setup_drag_drop(self):
        """Register text boxes as drop targets for PDF files."""
        if not DND_SUPPORT:
            return
        try:
            ro_inner = self.ro_text._textbox
            en_inner = self.en_text._textbox
            ro_inner.drop_target_register(DND_FILES)
            en_inner.drop_target_register(DND_FILES)
            ro_inner.dnd_bind('<<Drop>>', self._on_drop_ro)
            en_inner.dnd_bind('<<Drop>>', self._on_drop_en)
        except Exception:
            pass

    def _handle_drop(self, event, target):
        """Process a dropped PDF file onto a text box."""
        path = event.data.strip()
        # Handle paths wrapped in braces (Windows/spaces)
        if path.startswith('{') and path.endswith('}'):
            path = path[1:-1]
        if not path.lower().endswith('.pdf'):
            self.status_text.set("Doar fisiere PDF sunt acceptate!")
            return
        text = self.extract_pdf_text(path)
        if not text:
            return
        if target == "ro":
            self.ro_text.delete("1.0", "end")
            self.ro_text.insert("1.0", text)
            self.status_text.set(f"PDF RO importat: {os.path.basename(path)}")
            first_line = text.split("\n")[0].strip()
            if first_line and not self.is_section_label(first_line):
                self.song_name.set(first_line)
        else:
            self.en_text.delete("1.0", "end")
            self.en_text.insert("1.0", text)
            self.status_text.set(f"PDF EN importat: {os.path.basename(path)}")
        self._on_text_change()

    def _on_drop_ro(self, event):
        self._handle_drop(event, "ro")

    def _on_drop_en(self, event):
        self._handle_drop(event, "en")

    def _hook_scroll_sync(self):
        """Synchronise vertical scroll between the two editors."""
        ro_inner = self.ro_text._textbox
        en_inner = self.en_text._textbox

        def _ro_scroll(*args):
            if self._syncing_scroll:
                return
            self._syncing_scroll = True
            en_inner.yview_moveto(args[0])
            self._syncing_scroll = False

        def _en_scroll(*args):
            if self._syncing_scroll:
                return
            self._syncing_scroll = True
            ro_inner.yview_moveto(args[0])
            self._syncing_scroll = False

        # Bind mouse-wheel on both
        def _on_mousewheel_ro(event):
            if self._syncing_scroll:
                return
            self._syncing_scroll = True
            en_inner.yview_scroll(int(-1 * (event.delta / 120)), "units")
            self._syncing_scroll = False

        def _on_mousewheel_en(event):
            if self._syncing_scroll:
                return
            self._syncing_scroll = True
            ro_inner.yview_scroll(int(-1 * (event.delta / 120)), "units")
            self._syncing_scroll = False

        ro_inner.bind("<MouseWheel>", _on_mousewheel_ro)
        en_inner.bind("<MouseWheel>", _on_mousewheel_en)

        # Also intercept the yscrollcommand so dragging the scrollbar syncs
        orig_ro_yscroll = ro_inner.cget("yscrollcommand")
        orig_en_yscroll = en_inner.cget("yscrollcommand")

        def _ro_yscrollcommand(first, last):
            if orig_ro_yscroll:
                ro_inner.tk.call(orig_ro_yscroll, first, last)
            _ro_scroll(first)

        def _en_yscrollcommand(first, last):
            if orig_en_yscroll:
                en_inner.tk.call(orig_en_yscroll, first, last)
            _en_scroll(first)

        ro_inner.configure(yscrollcommand=_ro_yscrollcommand)
        en_inner.configure(yscrollcommand=_en_yscrollcommand)

    # ------------------------------------------------------------------ #
    #  Live line counter                                                  #
    # ------------------------------------------------------------------ #
    def _count_content_lines(self, textbox):
        """Count non-empty, non-section-label lines."""
        text = textbox.get("1.0", "end-1c")
        count = 0
        for line in text.split("\n"):
            stripped = line.strip()
            if stripped and not self.is_section_label(stripped):
                count += 1
        return count

    def _on_text_change(self):
        ro_count = self._count_content_lines(self.ro_text)
        en_count = self._count_content_lines(self.en_text)
        match = ro_count == en_count
        color = COLOR_GREEN if match else COLOR_RED
        self.line_count_label.configure(
            text=f"RO: {ro_count} linii  |  EN: {en_count} linii",
            text_color=color,
        )
        self._highlight_sections()

    # ------------------------------------------------------------------ #
    #  Section label highlight                                            #
    # ------------------------------------------------------------------ #
    def _highlight_sections(self):
        """Apply bold + accent colour to section labels in the RO editor."""
        tb = self.ro_text._textbox  # underlying tk.Text widget
        tb.tag_delete("section")
        tb.tag_configure(
            "section",
            foreground=ACCENT_YELLOW,
            font=FONT_MONO_BOLD,
        )
        text = self.ro_text.get("1.0", "end-1c")
        for i, line in enumerate(text.split("\n"), start=1):
            if self.is_section_label(line.strip()):
                tb.tag_add("section", f"{i}.0", f"{i}.end")

    # ------------------------------------------------------------------ #
    #  Collapsible instructions                                           #
    # ------------------------------------------------------------------ #
    def _toggle_instructions(self):
        if self._instructions_visible:
            self._instructions_frame.pack_forget()
            self._help_btn.configure(text="?  Instructiuni")
        else:
            self._instructions_frame.pack(
                padx=16, pady=(0, 12), fill="x",
                before=self._help_btn,
            )
            # Re-pack help btn so it stays below
            self._help_btn.pack_forget()
            self._help_btn.pack(padx=16, pady=(0, 8), fill="x")
        self._instructions_visible = not self._instructions_visible

    # ------------------------------------------------------------------ #
    #  Placeholder text                                                   #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _placeholder(lang):
        if lang == "ro":
            return (
                "Verse 1\n"
                "Esti inaltat pe tronul milei\n"
                "Tu stralucesti cu slava Ta aici\n"
                "O, Doamne, Te laud!\n"
                "\n"
                "Chorus\n"
                "Cine e ca El, tare-n lupta?\n"
                "Cine e ca El, Mantuitor?\n"
                "\n"
                "(Importa un PDF sau scrie versurile aici)"
            )
        return (
            "You're seated on the throne of mercy\n"
            "Your glory shining bright for all to see\n"
            "Oh God I will praise You\n"
            "\n"
            "Who is like the Lord, strong in battle?\n"
            "Who is like the Lord, mighty to save?\n"
            "\n"
            "(Import a PDF or type lyrics here - NO labels needed, they come from RO)"
        )

    # ------------------------------------------------------------------ #
    #  PDF import                                                         #
    # ------------------------------------------------------------------ #
    def extract_pdf_text(self, pdf_path):
        if not PDF_SUPPORT:
            messagebox.showerror(
                "Eroare",
                "pdfplumber nu este instalat!\nRuleaza: pip3 install pdfplumber",
            )
            return None
        lines = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        for line in text.split("\n"):
                            lines.append(line.strip())
        except Exception as e:
            messagebox.showerror("Eroare", f"Nu pot citi PDF-ul:\n{e}")
            return None
        return self.clean_pdf_text(lines)

    @staticmethod
    def clean_pdf_text(lines):
        cleaned = []
        for i, line in enumerate(lines):
            if not line.strip():
                continue
            if "[" in line and "]" in line:
                continue
            if "bpm" in line.lower():
                continue
            if "\u00d7" in line:
                continue
            if i < 3 and "," in line and len(line.split(",")) > 3:
                continue
            if line.strip().isdigit():
                continue
            cleaned.append(line)
        return "\n".join(cleaned)

    def import_pdf_ro(self):
        path = filedialog.askopenfilename(
            title="Selecteaza PDF-ul in Romana",
            filetypes=[("PDF files", "*.pdf")],
        )
        if path:
            text = self.extract_pdf_text(path)
            if text:
                self.ro_text.delete("1.0", "end")
                self.ro_text.insert("1.0", text)
                self.status_text.set(f"PDF RO importat: {os.path.basename(path)}")
                first_line = text.split("\n")[0].strip()
                if first_line and not self.is_section_label(first_line):
                    self.song_name.set(first_line)
                self._on_text_change()

    def import_pdf_en(self):
        path = filedialog.askopenfilename(
            title="Selecteaza PDF-ul in Engleza",
            filetypes=[("PDF files", "*.pdf")],
        )
        if path:
            text = self.extract_pdf_text(path)
            if text:
                self.en_text.delete("1.0", "end")
                self.en_text.insert("1.0", text)
                self.status_text.set(f"PDF EN importat: {os.path.basename(path)}")
                self._on_text_change()

    # ------------------------------------------------------------------ #
    #  Section-label detection                                            #
    # ------------------------------------------------------------------ #
    @staticmethod
    def is_section_label(line):
        upper = line.upper().strip()
        for label in SECTION_LABELS:
            if upper.startswith(label):
                return True
        return False

    # ------------------------------------------------------------------ #
    #  Lyrics parsing  (kept identical to the original logic)             #
    # ------------------------------------------------------------------ #
    def parse_ro_lyrics(self, text):
        lines = text.strip().split("\n")
        result = []
        structure = []
        current_section = "Verse 1"
        current_count = 0

        for line in lines:
            line = line.strip()
            if not line:
                continue
            if self.is_section_label(line):
                if current_count > 0:
                    structure.append({"label": current_section, "count": current_count})
                current_section = line.title()
                current_count = 0
                result.append(current_section)
            else:
                result.append(line)
                current_count += 1

        if current_count > 0:
            structure.append({"label": current_section, "count": current_count})

        return structure, result

    def parse_en_with_ro_structure(self, en_text, ro_structure):
        lines = en_text.strip().split("\n")
        en_content = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if self.is_section_label(line):
                continue
            en_content.append(line)

        result = []
        en_index = 0
        for section in ro_structure:
            result.append(section["label"])
            for _ in range(section["count"]):
                if en_index < len(en_content):
                    result.append(en_content[en_index])
                    en_index += 1

        return result, en_index, len(en_content)

    # ------------------------------------------------------------------ #
    #  Preview                                                             #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _get_section_color(label):
        """Return ProPresenter-style color for a section label."""
        if not label:
            return '#666666'
        label_lower = label.lower()
        for key, color in SECTION_COLORS.items():
            if label_lower.startswith(key):
                return color
        return '#666666'

    def _build_preview_slides(self):
        """Parse lyrics and split into slides for preview."""
        ro_content = self.ro_text.get("1.0", "end-1c").strip()
        en_content = self.en_text.get("1.0", "end-1c").strip()
        if not ro_content:
            return []

        ro_structure, ro_lines = self.parse_ro_lyrics(ro_content)
        en_lines, _, _ = self.parse_en_with_ro_structure(en_content, ro_structure)
        lines_per_slide = int(self.lines_per_slide.get())

        slides = []
        current_label = "Verse 1"
        ro_buf = []
        en_buf = []

        for i in range(len(ro_lines)):
            ro_line = ro_lines[i]
            en_line = en_lines[i] if i < len(en_lines) else ""

            if self.is_section_label(ro_line):
                # Flush buffer
                while ro_buf:
                    slides.append({
                        "label": current_label,
                        "ro": "\n".join(ro_buf[:lines_per_slide]),
                        "en": "\n".join(en_buf[:lines_per_slide]),
                    })
                    ro_buf = ro_buf[lines_per_slide:]
                    en_buf = en_buf[lines_per_slide:]
                current_label = ro_line
            else:
                ro_buf.append(ro_line)
                en_buf.append(en_line)
                if len(ro_buf) == lines_per_slide:
                    slides.append({
                        "label": current_label,
                        "ro": "\n".join(ro_buf),
                        "en": "\n".join(en_buf),
                    })
                    ro_buf = []
                    en_buf = []

        # Flush remaining
        if ro_buf:
            slides.append({
                "label": current_label,
                "ro": "\n".join(ro_buf),
                "en": "\n".join(en_buf),
            })

        return slides

    def show_preview(self):
        """Open a preview window showing slides as they will appear."""
        content_slides = self._build_preview_slides()
        if not content_slides:
            messagebox.showwarning("Atentie", "Nu sunt versuri de previzualizat!")
            return

        # Build full slide list: Blank + content + Interlude + Ending
        all_slides = [{"label": "Blank", "ro": "", "en": ""}]
        all_slides.extend(content_slides)
        all_slides.append({"label": "Interlude", "ro": "", "en": ""})
        all_slides.append({"label": "Ending", "ro": "", "en": ""})

        # Create preview window
        preview = ctk.CTkToplevel(self)
        preview.title(f"Preview — {self.song_name.get()} — {len(all_slides)} slide-uri")
        preview.geometry("960x620")
        preview.transient(self)

        # Header
        header = ctk.CTkFrame(preview, height=44, corner_radius=0, fg_color="gray15")
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header,
            text=f"  {self.song_name.get()}  —  {len(all_slides)} slide-uri  |  {self.lines_per_slide.get()} linii/slide",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left", padx=12, pady=8)

        # Scrollable grid
        scroll = ctk.CTkScrollableFrame(preview, fg_color="gray10")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        cols = 4
        for col in range(cols):
            scroll.grid_columnconfigure(col, weight=1, uniform="card")

        for i, slide in enumerate(all_slides):
            row = i // cols
            col = i % cols
            self._create_slide_card(scroll, slide, i + 1, row, col)

    def _create_slide_card(self, parent, slide, number, row, col):
        """Create a single slide preview card."""
        color = self._get_section_color(slide["label"])

        # Card frame
        card = ctk.CTkFrame(
            parent, height=140, corner_radius=6,
            border_width=1, border_color="gray35",
            fg_color="gray14",
        )
        card.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")
        card.grid_propagate(False)
        card.grid_rowconfigure(0, weight=1)
        card.grid_columnconfigure(0, weight=1)

        # Content area
        content = ctk.CTkFrame(card, fg_color="gray14", corner_radius=0)
        content.grid(row=0, column=0, sticky="nsew", padx=6, pady=(6, 0))

        # RO text
        if slide["ro"]:
            ctk.CTkLabel(
                content, text=slide["ro"],
                font=ctk.CTkFont(size=10),
                text_color="white",
                anchor="nw", justify="left",
                wraplength=195,
            ).pack(anchor="nw")

        # EN text
        if slide["en"]:
            ctk.CTkLabel(
                content, text=slide["en"],
                font=ctk.CTkFont(size=10),
                text_color="#00CED1",
                anchor="nw", justify="left",
                wraplength=195,
            ).pack(anchor="nw", pady=(3, 0))

        # Section label bar at bottom
        label_bar = ctk.CTkFrame(card, height=22, fg_color=color, corner_radius=0)
        label_bar.grid(row=1, column=0, sticky="sew")
        label_bar.grid_propagate(False)
        ctk.CTkLabel(
            label_bar,
            text=f" {number}   {slide['label']}",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="white",
        ).pack(side="left", padx=4)

    # ------------------------------------------------------------------ #
    #  Generate .PRO                                                      #
    # ------------------------------------------------------------------ #
    def generate_pro(self):
        ro_content = self.ro_text.get("1.0", "end-1c").strip()
        en_content = self.en_text.get("1.0", "end-1c").strip()
        song_name = self.song_name.get().strip()

        if not ro_content or not en_content:
            messagebox.showwarning("Atentie", "Completeaza versurile in ambele limbi!")
            return
        if not song_name:
            messagebox.showwarning("Atentie", "Introdu numele cantecului!")
            return

        ro_structure, ro_lines = self.parse_ro_lyrics(ro_content)
        en_lines, en_used, en_total = self.parse_en_with_ro_structure(en_content, ro_structure)

        ro_verse_count = sum(s["count"] for s in ro_structure)
        if en_used != en_total:
            result = messagebox.askyesno(
                "Atentie",
                f"Numar diferit de versuri:\nRomana: {ro_verse_count} linii\n"
                f"Engleza: {en_total} linii (folosite: {en_used})\n\n"
                "Vrei sa continui oricum?",
            )
            if not result:
                return

        try:
            text_block_names = get_text_block_names()
        except Exception:
            messagebox.showerror("Eroare", "Template.pro lipseste sau e invalid!")
            return

        song_texts = {"RO": ro_lines, "ENG": en_lines}

        save_path = filedialog.asksaveasfilename(
            title="Salveaza fisierul ProPresenter",
            defaultextension=".pro",
            initialfile=song_name.replace(" ", "_"),
            filetypes=[("ProPresenter files", "*.pro")],
        )
        if not save_path:
            return

        try:
            output_name = save_path.replace(".pro", "")
            save_song(text_block_names, song_texts, int(self.lines_per_slide.get()), output_name)
            self.status_text.set(f"Salvat: {os.path.basename(save_path)}")
            messagebox.showinfo(
                "Succes",
                f"Fisierul a fost generat!\n\n{save_path}\n\nPoti sa-l importi in ProPresenter.",
            )
        except Exception as e:
            messagebox.showerror("Eroare", f"Nu am putut genera fisierul:\n{e}")


def main():
    app = BilingualEditorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
