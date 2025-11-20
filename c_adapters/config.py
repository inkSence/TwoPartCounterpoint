#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Zentrale Konfiguration für Adapter/Controller.

Hier werden alle vormals hart codierten Werte gesammelt, damit
TwoPartCounterpointController übersichtlich bleibt und sich Werte
einfach anpassen lassen.
"""

from __future__ import annotations



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

    # Hinweis: Wiedergabe-/Synth-Parameter sind in der Driver-Schicht
    # d_frameworks_drivers.midiFluidSynth.config.MidiFluidSynthConfig
    # definiert. Diese AppConfig enthält bewusst keine Audio-/Synth-Werte.
