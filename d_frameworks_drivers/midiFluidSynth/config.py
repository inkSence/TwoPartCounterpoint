#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

"""Konfiguration für die MIDI/Audio-Wiedergabe via FluidSynth (Driver-Schicht).

Diese Datei hält alle Abspiel-bezogenen Parameter, die NICHT in die
Adapter-Schicht (c_adapters) gehören. Sie wird vom Driver on-demand genutzt,
um PlaybackSettings zu erzeugen.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class PlaybackSettings:
    """Wiedergabe-Parameter für den FluidSynth-Driver.

    Diese Settings sind lokal in der Driver-Schicht definiert und werden
    on-demand aus MidiFluidSynthConfig erzeugt. Sie werden NICHT mehr über die
    Adapter-/Port-Schicht herumgereicht.
    """

    # Zeitsteuerung
    tick_seconds: float
    fadeout_seconds: float

    # Audio / Synth
    samplerate: float
    gain: float
    drivers: tuple[str, ...]

    # MIDI-Parameter
    midi_velocity: int
    cc_volume: int
    cc_expression: int

    # Presets (bank, program)
    presets: tuple[tuple[int, int], ...]


@dataclass
class MidiFluidSynthConfig:
    # Zeitsteuerung
    tick_seconds: float = 0.25
    fadeout_seconds: float = 1.0

    # Audio / Synth
    samplerate: float = 44100.0
    gain: float = 1.0

    # Treiberreihenfolge (bevorzugt zuerst)
    preferred_driver: str = "pulseaudio"
    fallback_drivers: list[str] = field(default_factory=lambda: ["pipewire"])  # noqa: RUF009

    # MIDI-Parameter
    midi_velocity: int = 100
    cc_volume: int = 127  # CC7
    cc_expression: int = 127  # CC11

    # GM-Preset-Reihenfolge (bank, program), z. B. Piano (0), Tenor Sax (65)
    presets: list[tuple[int, int]] = field(default_factory=lambda: [(0, 0), (0, 65)])

    # SoundFont
    sf_local_relpath: Path = Path("d_frameworks_drivers") / "midiFluidSynth" / "soundFonts" / "1276-soft_tenor_sax.sf2"

    def iter_audio_drivers(self) -> Iterable[str]:
        yield self.preferred_driver
        for drv in self.fallback_drivers:
            yield drv

    def to_settings(self) -> PlaybackSettings:
        """Erzeugt PlaybackSettings für den FluidSynth-Driver.

        Hinweis: Der SoundFont-Pfad ist kein Teil der Settings, sondern wird im
        Driver selbst (_choose_soundfont) ermittelt.
        """
        return PlaybackSettings(
            tick_seconds=self.tick_seconds,
            fadeout_seconds=self.fadeout_seconds,
            samplerate=self.samplerate,
            gain=self.gain,
            drivers=tuple(self.iter_audio_drivers()),
            midi_velocity=self.midi_velocity,
            cc_volume=self.cc_volume,
            cc_expression=self.cc_expression,
            presets=tuple(self.presets),
        )
