#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import time
from pathlib import Path

from a_domain.Melodie import Melodie
from c_adapters.config import AppConfig
from c_adapters.ports.score_export_port import ScoreExportPort
from c_adapters.FileSystemAdapter import FileSystemAdapter

from .config import MuseScoreConfig


class MuseScoreFileExporter(ScoreExportPort):
    """Konkreter Driver für den Export einer Melodie als MuseScore-Datei (.mscx).

    - Verwendet ein statisches Template und fügt den generierten Body-XML ein.
    - Schreibt in das Verzeichnis `Kontrapunkte/` unterhalb des Projekt-Roots.
    - Fragile Head-/Tail-Offsets sind in MuseScoreConfig hinterlegt.
    """

    def __init__(self, project_root: Path, app_cfg: AppConfig,
                 ms_cfg: MuseScoreConfig | None = None,
                 fs: FileSystemAdapter | None = None) -> None:
        self.project_root = project_root
        self.app_cfg = app_cfg
        self.ms = ms_cfg or MuseScoreConfig()
        # FileSystem-Adapter für alle Dateioperationen (Clean Architecture)
        self.fs = fs or FileSystemAdapter(project_root)

    # --- interne Helfer ---
    def _template_path(self) -> Path:
        # Unterstützt absolute Pfade in der Config sowie relative (vom Projekt-Root aus)
        return self.fs.resolve_path(self.ms.template_relpath)

    def _read_template_parts(self) -> tuple[str, str]:
        return self.fs.read_head_tail(self._template_path(), self.ms.head_bytes, self.ms.tail_bytes)

    def _ensure_out_dir(self) -> Path:
        return self.fs.ensure_dir(Path(self.ms.out_dirname))

    def _build_out_path(self) -> Path:
        name = f"{self.ms.filename_prefix}{time.strftime('%b%d.%H-%M-%S')}.mscx"
        return (self._ensure_out_dir() / name)

    def _melody_to_body_xml(self, melody: Melodie) -> str:
        body = []
        for pitch, laenge in melody.notenliste:
            durationType, dots = self.app_cfg.score_duration_map.get(laenge, ("quarter", ""))
            body.append(
                "<Chord>"
                + str(dots)
                + "<durationType>" + str(durationType) + "</durationType>"
                + "<Note><pitch>" + str(pitch) + "</pitch></Note>"
                + "</Chord>\n"
            )
        return "".join(body)

    # --- Port-Implementierung ---
    def export_melody(self, melody: Melodie) -> Path:
        head, tail = self._read_template_parts()
        body = self._melody_to_body_xml(melody)
        out_path = self._build_out_path()
        self.fs.write_text(out_path, head + body + tail)
        return out_path
