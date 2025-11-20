#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import time
from pathlib import Path
import xml.etree.ElementTree as ET

from a_domain.Melodie import Melodie
from c_adapters.config import AppConfig
from c_adapters.ports.score_export_port import ScoreExportPort
from c_adapters.FileSystemAdapter import FileSystemAdapter
from c_adapters.MuseScoreXmlAdapter import MuseScoreXmlAdapter
from .config import MuseScoreConfig


class MuseScoreFileExporter(ScoreExportPort):
    """Konkreter Driver für den Export einer Melodie als MuseScore-Datei (.mscx).

    XML-basiertes Einfügen statt fragiler Head/Tail-Offsets:
    - lädt ein `.mscx`-Template als XML,
    - findet in Staff id="1" / Measure number="1" die Position direkt nach <TimeSig>,
    - entfernt ggf. vorhandene Platzhalter-Inhalte (z. B. <Rest>) bis zur nächsten <BarLine>,
    - fügt dort <Chord>-Knoten für die übergebene Melodie ein,
    - schreibt das Ergebnis als wohlgeformtes XML in `Kontrapunkte/`.
    """

    def __init__(self, project_root: Path, app_cfg: AppConfig,
                 ms_cfg: MuseScoreConfig,
                 fs: FileSystemAdapter,
                 xml: MuseScoreXmlAdapter) -> None:
        self.project_root = project_root
        self.app_cfg = app_cfg
        self.musescore = ms_cfg
        # FileSystem-Adapter für alle Dateioperationen (Clean Architecture)
        self.fs = fs
        # XML-Adapter kapselt Template-Navigation und Knotenbau
        self.xml = xml

    # --- interne Helfer ---
    def _template_path(self) -> Path:
        # Unterstützt absolute Pfade in der Config sowie relative (vom Projekt-Root aus)
        return self.fs.resolve_path(self.musescore.template_relpath)


    def _ensure_out_dir(self) -> Path:
        return self.fs.ensure_dir(Path(self.musescore.out_dirname))

    def _build_out_path(self) -> Path:
        name = f"{self.musescore.filename_prefix}{time.strftime('%b%d.%H-%M-%S')}.mscx"
        return (self._ensure_out_dir() / name)

    # Interne XML-Helfer wurden in den Adapter ausgelagert

    # --- Port-Implementierung ---
    def export_melody(self, melody: Melodie) -> Path:
        # 1) Template als XML laden
        template_path = self._template_path()
        tree, root = self.xml.parse(template_path)

        # 2) Ziel-Measure finden (Standard: Staff id="1", Measure number="1")
        measure = self.xml.find_staff_measure(root, staff_id="1", measure_number="1")

        # 3) Einfügepunkt nach <TimeSig>
        insert_idx = self.xml.insertion_index_after(measure, tag_name="TimeSig")

        # 3b) Vorhandene Inhalte (z. B. measure-weiter <Rest>) bis zur nächsten <BarLine> entfernen
        self.xml.clear_until_barline(measure, insert_idx)

        # 4) Chord-Elemente aus Melodie erzeugen
        chord_elements = self.xml.make_chords(self.app_cfg.score_duration_map, melody.notenliste)

        # 5) Einfügen in richtiger Reihenfolge
        for offset, element in enumerate(chord_elements):
            measure.insert(insert_idx + offset, element)

        # 5b) Sicherstellen, dass eine BarLine am Measure-Ende existiert
        self.xml.ensure_barline(measure, subtype="5")

        # 6) Schreiben (Verzeichnis sicherstellen)
        out_path = self._build_out_path()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        self.xml.write(tree, out_path)

        # 7) Wohlgeformtheit validieren
        ET.parse(out_path)

        return out_path
