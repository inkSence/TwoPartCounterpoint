#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Dateisystem-Konfiguration für Adapter-Schicht (Clean Architecture).

Enthält ausschließlich Angaben, die Pfade, Dateinamen und Template-Offsets
betreffen. Fachliche/Audio-Parameter verbleiben in c_adapters.config.AppConfig.
"""

from __future__ import annotations

from pathlib import Path


class FileSystemConfig:
    # MuseScore-Template relativ zum Projekt-Root
    score_template_relpath: Path = Path("data") / "wWIHNS_Choral.mscx"
    # Fragile Offsets für das aktuelle Template
    score_head_bytes: int = 5116
    score_tail_bytes: int = 3251

    # Ausgabeverzeichnis (relativ zum Projekt-Root) und Dateiname
    score_out_dirname: str = "Kontrapunkte"
    score_filename_prefix: str = "wWIHNS_mitKontrapunkt_"

    # SoundFonts: zuerst projektlokal, dann systemweit
    sf_local_relpath: Path = Path("soundFonts") / "1276-soft_tenor_sax.sf2"
    sf_system_path: Path = Path("/usr/share/sounds/sf2/FluidR3_GM.sf2")
