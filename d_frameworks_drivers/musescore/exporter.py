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
                 ms_cfg: MuseScoreConfig | None = None,
                 fs: FileSystemAdapter | None = None) -> None:
        self.project_root = project_root
        self.app_cfg = app_cfg
        self.musescore = ms_cfg or MuseScoreConfig()
        # FileSystem-Adapter für alle Dateioperationen (Clean Architecture)
        self.fs = fs or FileSystemAdapter(project_root)

    # --- interne Helfer ---
    def _template_path(self) -> Path:
        # Unterstützt absolute Pfade in der Config sowie relative (vom Projekt-Root aus)
        return self.fs.resolve_path(self.musescore.template_relpath)

    # --- XML-Helfer ---
    def _find_target_measure(self, root: ET.Element, staff_id: str = "1", measure_number: str = "1") -> ET.Element:
        """Sucht Staff[id] und darin Measure[number].

        Hebt eine klare Exception, wenn nicht gefunden.
        """
        target_staff = None
        for staff in root.findall('.//Staff'):
            if staff.get('id') == staff_id:
                target_staff = staff
                break
        if target_staff is None:
            raise ValueError(f"Staff mit id='{staff_id}' wurde im Template nicht gefunden.")

        for ms in target_staff.findall('./Measure'):
            if ms.get('number') == measure_number:
                return ms
        raise ValueError(f"Measure number='{measure_number}' in Staff id='{staff_id}' wurde nicht gefunden.")

    def _find_insertion_index_after(self, container: ET.Element, tag_name: str = "TimeSig") -> int:
        """Gibt den Index zum Einfügen direkt nach dem ersten Kind mit tag_name zurück.

        Fallbacks: nach "KeySig" oder an den Anfang, falls tag_name nicht existiert.
        """
        children = list(container)
        for idx, child in enumerate(children):
            if child.tag == tag_name:
                return idx + 1
        # Fallbacks
        for idx, child in enumerate(children):
            if child.tag == "KeySig":
                return idx + 1
        return 0

    def _remove_content_until_barline(self, container: ET.Element, start_idx: int, barline_tag: str = "BarLine") -> None:
        """Entfernt alle Kinder im Bereich [start_idx, barline_idx) –
        typischerweise Platzhalter wie <Rest> oder vorhandene <Chord>-Elemente –
        lässt die erste gefundene <BarLine> (und alles danach) unangetastet.

        Wenn keine <BarLine> vorhanden ist, werden alle Kinder ab start_idx entfernt.
        """
        children = list(container)
        # Finde den Index der ersten BarLine ab start_idx
        end_idx = None
        for idx in range(start_idx, len(children)):
            if children[idx].tag == barline_tag:
                end_idx = idx
                break
        if end_idx is None:
            end_idx = len(children)

        # Von hinten nach vorne entfernen, damit Indizes nicht verrutschen
        for idx in range(end_idx - 1, start_idx - 1, -1):
            container.remove(children[idx])

    def _ensure_out_dir(self) -> Path:
        return self.fs.ensure_dir(Path(self.musescore.out_dirname))

    def _build_out_path(self) -> Path:
        name = f"{self.musescore.filename_prefix}{time.strftime('%b%d.%H-%M-%S')}.mscx"
        return (self._ensure_out_dir() / name)

    def _melody_to_chord_elements(self, melody: Melodie) -> list[ET.Element]:
        """Wandelt die Domänen-Melodie in eine Liste von <Chord>-Elementen um."""
        chords: list[ET.Element] = []
        for pitch, laenge in melody.notenliste:
            duration_type, dots_text = self.app_cfg.score_duration_map.get(laenge, ("quarter", ""))

            chord_el = ET.Element("Chord")

            # optional <dots>
            if dots_text:
                # Erwartetes Format: "<dots>1</dots>" – robust extrahieren
                dots_value = None
                if "<dots" in dots_text:
                    try:
                        start = dots_text.index("<dots>") + len("<dots>")
                        end = dots_text.index("</dots>", start)
                        dots_value = dots_text[start:end].strip() or "1"
                    except ValueError:
                        dots_value = "1"
                if dots_value is not None:
                    dots_el = ET.SubElement(chord_el, "dots")
                    dots_el.text = dots_value

            dt_el = ET.SubElement(chord_el, "durationType")
            dt_el.text = str(duration_type)

            note_el = ET.SubElement(chord_el, "Note")
            pitch_el = ET.SubElement(note_el, "pitch")
            pitch_el.text = str(pitch)

            chords.append(chord_el)

        return chords

    # --- Port-Implementierung ---
    def export_melody(self, melody: Melodie) -> Path:
        # 1) Template als XML laden
        template_path = self._template_path()
        tree = ET.parse(template_path)
        root = tree.getroot()

        # 2) Ziel-Measure finden (Standard: Staff id="1", Measure number="1")
        measure = self._find_target_measure(root, staff_id="1", measure_number="1")

        # 3) Einfügepunkt nach <TimeSig>
        insert_idx = self._find_insertion_index_after(measure, tag_name="TimeSig")

        # 3b) Vorhandene Inhalte (z. B. measure-weiter <Rest>) bis zur nächsten <BarLine> entfernen
        self._remove_content_until_barline(measure, insert_idx)

        # 4) Chord-Elemente aus Melodie erzeugen
        chord_elements = self._melody_to_chord_elements(melody)

        # 5) Einfügen in richtiger Reihenfolge
        for offset, element in enumerate(chord_elements):
            measure.insert(insert_idx + offset, element)

        # 5b) Sicherstellen, dass eine BarLine am Measure-Ende existiert
        if not any(child.tag == "BarLine" for child in list(measure)):
            bar = ET.SubElement(measure, "BarLine")
            sub = ET.SubElement(bar, "subtype")
            sub.text = "5"

        # 6) Schreiben (Verzeichnis sicherstellen)
        out_path = self._build_out_path()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        tree.write(out_path, encoding="utf-8", xml_declaration=True)

        # 7) Wohlgeformtheit validieren
        ET.parse(out_path)

        return out_path
