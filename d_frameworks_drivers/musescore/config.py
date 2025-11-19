#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path


class MuseScoreConfig:
    """Konfiguration für den MuseScore-Dateiexport (Driver-Schicht).

    Hinweis: Die Offsets sind fragil und hängen vom verwendeten Template ab.
    """

    # Template-Pfad: Standard ist die Datei direkt neben dieser Konfigurationsdatei.
    # Wir speichern hier einen absoluten Pfad, damit der Exporter ihn 1:1 nutzen kann.
    template_relpath: Path = Path(__file__).resolve().with_name("wWIHNS_Choral.mscx")
    # Bytes für Kopf/Ende (abhängig vom Template)
    head_bytes: int = 5116
    tail_bytes: int = 3251

    # Ausgabeverzeichnis und Dateiname
    out_dirname: str = "Kontrapunkte"
    filename_prefix: str = "wWIHNS_mitKontrapunkt_"
