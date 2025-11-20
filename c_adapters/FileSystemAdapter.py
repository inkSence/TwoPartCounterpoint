#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""FileSystemAdapter: Kapselt generische Dateisystem-Zugriffe.

Gemäß Clean Architecture gehören framework-/format-spezifische Details
(wie das konkrete MuseScore-XML) nicht hierher. Dieser Adapter stellt
allgemeine FS-Helfer bereit, die von äußeren Schichten genutzt werden
können (z. B. Lesen/Schreiben von Dateien, Verzeichnisse anlegen,
Pfade relativ zum Projekt-Root auflösen).
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple



class FileSystemAdapter:
    def __init__(self, base_path: Path) -> None:
        # base_path zeigt auf das Projekt-Root
        self.base_path = base_path

    # --- Pfadfunktionen ---
    def resolve_path(self, rel_or_abs: Path) -> Path:
        """Löst einen Pfad relativ zum Projekt-Root auf, falls er nicht absolut ist."""
        return rel_or_abs if rel_or_abs.is_absolute() else (self.base_path / rel_or_abs).resolve()

    # --- Lesen ---
    def read(self, file_path: Path, encoding: str = "utf-8") -> str:
        path = self.resolve_path(file_path)
        with open(path, "r", encoding=encoding) as file:
            return file.read()

    def ensure_dir(self, directory: Path) -> Path:
        """Stellt sicher, dass ein Verzeichnis existiert, und gibt den Pfad zurück."""
        d = self.resolve_path(directory)
        d.mkdir(parents=True, exist_ok=True)
        return d

    # --- Schreiben ---
    def write_text(self, file_path: Path, content: str, encoding: str = "utf-8") -> Path:
        """Schreibt Textinhalt in eine Datei, legt Elternverzeichnisse bei Bedarf an, und gibt den Pfad zurück."""
        p = self.resolve_path(file_path)
        parent = p.parent
        parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding=encoding) as out:
            out.write(content)
        return p
