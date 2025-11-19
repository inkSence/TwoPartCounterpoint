#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""FileSystemAdapter: Kapselt alle Dateisystem-Zugriffe.

Gemäß Clean Architecture sollen Komponenten außerhalb der Adapter-Schicht
keine direkten Dateioperationen durchführen. Dieser Adapter bündelt:
- Lesen der MuseScore-Vorlage (Head/Tail anhand fester Offsets)
- Erzeugen des Ausgabepfads und Schreiben der Ausgabedatei
- Auswahl eines geeigneten SoundFont-Pfads (lokal vs. systemweit)
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Tuple

from .fs_config import FileSystemConfig


class FileSystemAdapter:
    def __init__(self, base_path: Path, config: FileSystemConfig | None = None) -> None:
        # base_path zeigt auf das Projekt-Root
        self.base_path = base_path
        self.config = config or FileSystemConfig()

    # --- MuseScore-Vorlage ---
    def _template_path(self) -> Path:
        return (self.base_path / self.config.score_template_relpath).resolve()

    def read_musescore_template(self) -> Tuple[str, str]:
        """Liest den Kopf- und End-Teil aus der MuseScore-Vorlage.

        Rückgabe: (head_str, tail_str)
        """
        tpl = self._template_path()
        with open(tpl, "r", encoding="utf-8") as f:
            head = f.read(self.config.score_head_bytes)
            remainder = f.read()
        tail = remainder[-self.config.score_tail_bytes :]
        return head, tail

    # --- Ausgabedatei ---
    def ensure_output_dir(self) -> Path:
        out_dir = self.base_path / self.config.score_out_dirname
        out_dir.mkdir(parents=True, exist_ok=True)
        return out_dir

    def build_output_path(self) -> Path:
        out_dir = self.ensure_output_dir()
        name = f"{self.config.score_filename_prefix}{time.strftime('%b%d.%H-%M-%S')}.mscx"
        return out_dir / name

    def write_musescore_file(self, body_xml: str) -> Path:
        """Schreibt die MuseScore-Datei und gibt den Pfad zurück."""
        head, tail = self.read_musescore_template()
        out_path = self.build_output_path()
        with open(out_path, "w", encoding="utf-8") as out:
            out.write(head)
            out.write(body_xml)
            out.write(tail)
        return out_path

    # --- SoundFont-Auswahl ---
    def choose_soundfont_path(self) -> Path:
        """Wählt bevorzugt die projektlokale SoundFont-Datei, sonst den System-Pfad."""
        local = (self.base_path / self.config.sf_local_relpath).resolve()
        if local.exists():
            return local
        return self.config.sf_system_path
