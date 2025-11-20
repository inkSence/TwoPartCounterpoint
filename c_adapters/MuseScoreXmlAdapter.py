#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET


class MuseScoreXmlAdapter:
    """MuseScore-spezifische XML-Helfer (ElementTree-basiert).

    Diese Klasse kapselt wiederkehrende Operationen auf .mscx-Dateien.
    """

    # --- IO ---
    def parse(self, path: Path) -> tuple[ET.ElementTree, ET.Element]:
        tree = ET.parse(path)
        return tree, tree.getroot()

    def write(self, tree: ET.ElementTree, out_path: Path) -> None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        tree.write(out_path, encoding="utf-8", xml_declaration=True)

    # --- Suche / Navigation ---
    def find_staff_measure(self, root: ET.Element, staff_id: str = "1", measure_number: str = "1") -> ET.Element:
        staff = None
        for s in root.findall('.//Staff'):
            if s.get('id') == staff_id:
                staff = s
                break
        if staff is None:
            raise ValueError(f"Staff id='{staff_id}' nicht gefunden")
        for m in staff.findall('./Measure'):
            if m.get('number') == measure_number:
                return m
        raise ValueError(f"Measure number='{measure_number}' in Staff id='{staff_id}' nicht gefunden")

    def insertion_index_after(self, container: ET.Element, tag_name: str = "TimeSig") -> int:
        children = list(container)
        for i, c in enumerate(children):
            if c.tag == tag_name:
                return i + 1
        for i, c in enumerate(children):
            if c.tag == "KeySig":
                return i + 1
        return 0

    def clear_until_barline(self, container: ET.Element, start_idx: int, barline_tag: str = "BarLine") -> None:
        children = list(container)
        end_idx = None
        for i in range(start_idx, len(children)):
            if children[i].tag == barline_tag:
                end_idx = i
                break
        if end_idx is None:
            end_idx = len(children)
        for idx in range(end_idx - 1, start_idx - 1, -1):
            container.remove(children[idx])

    # --- Knotenbau ---
    def make_chords(self, score_duration_map: dict[int, tuple[str, str]], notes: list[tuple[int, int]]) -> list[ET.Element]:
        els: list[ET.Element] = []
        for pitch, laenge in notes:
            duration_type, dots_text = score_duration_map.get(laenge, ("quarter", ""))
            chord = ET.Element("Chord")
            if dots_text and "<dots>" in dots_text:
                # sehr einfache Extraktion, da Mapping kontrolliert ist
                try:
                    v = dots_text[dots_text.index("<dots>") + 6:dots_text.index("</dots>")].strip() or "1"
                except ValueError:
                    v = "1"
                d = ET.SubElement(chord, "dots"); d.text = v
            dt = ET.SubElement(chord, "durationType"); dt.text = str(duration_type)
            note = ET.SubElement(chord, "Note")
            p = ET.SubElement(note, "pitch"); p.text = str(pitch)
            els.append(chord)
        return els

    def ensure_barline(self, measure: ET.Element, subtype: str = "5") -> None:
        if not any(child.tag == "BarLine" for child in list(measure)):
            bar = ET.SubElement(measure, "BarLine")
            sub = ET.SubElement(bar, "subtype"); sub.text = subtype
