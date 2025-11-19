#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Zentrale Konfiguration für Adapter/Controller.

Hier werden alle vormals hart codierten Werte gesammelt, damit
TwoPartCounterpointController übersichtlich bleibt und sich Werte
einfach anpassen lassen.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable


class AppConfig:
    # --- Choral/Eingabedaten ---
    # Choral „Wenn wir in höchsten Nöten sein“ als (MIDI-Pitch, Dauer in Achteln)
    wWIHNS_1: list[tuple[int, int]] = [
        (53, 4), (53, 2), (55, 2), (57, 4), (55, 2), (58, 4), (57, 2), (55, 4), (53, 4),
        (57, 4), (58, 2), (57, 2), (55, 2), (53, 2), (52, 4), (53, 4), (55, 8), (60, 4),
        (58, 2), (57, 2), (55, 4), (57, 4), (53, 4), (50, 4), (48, 4), (57, 4), (58, 2),
        (57, 2), (55, 2), (53, 2), (57, 4), (55, 4), (53, 8)
    ]

    # --- MuseScore-Export (fachliche Abbildung, kein FS) ---
    # Mapping von Achtel-Längen zu MuseScore-DurationType und Punktierung
    # Werte: (durationType, dots_xml)
    score_duration_map: dict[int, tuple[str, str]] = {
        1: ("eighth", ""),
        2: ("quarter", ""),
        3: ("quarter", "<dots>1</dots>"),
        4: ("half", ""),
        6: ("half", "<dots>1</dots>"),
        8: ("whole", ""),
    }

    # --- Audio-Wiedergabe (FluidSynth Realtime) ---
    synth_samplerate: float = 44100.0
    synth_gain: float = 1.0
    preferred_driver: str = "pulseaudio"
    fallback_drivers: list[str] = ["pipewire"]
    midi_velocity: int = 100
    midi_cc_volume: int = 127  # CC7
    midi_cc_expression: int = 127  # CC11
    tick_seconds: float = 0.25
    fadeout_seconds: float = 1.0

    # SoundFont-Preset-Reihenfolge (fachliche Auswahl, keine Pfade)
    # Preset-Reihenfolge: Liste von (bank, program)
    sf_presets: list[tuple[int, int]] = [(0, 0), (0, 65)]  # Piano, Tenor Sax

    def iter_audio_drivers(self) -> Iterable[str]:
        yield self.preferred_driver
        for drv in self.fallback_drivers:
            yield drv
