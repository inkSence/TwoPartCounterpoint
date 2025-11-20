#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

"""Konfiguration für die MIDI/Audio-Wiedergabe via FluidSynth (Driver-Schicht).

Diese Datei hält alle Abspiel-bezogenen Parameter, die NICHT in die
Adapter-Schicht (c_adapters) gehören. Sie kann von außen (main/Composition
Root) verwendet werden, um neutrale PlaybackSettings zu erzeugen.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from c_adapters.ports.playback_port import PlaybackSettings


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

    # SoundFonts: bevorzugt paketlokal (innerhalb von d_frameworks_drivers/midiFluidSynth), sonst systemweit
    # Hinweis: Der Pfad ist relativ zum Projekt-Root (Composition Root reicht project_root an den Driver durch).
    # Neuer Standard-Suchort: d_frameworks_drivers/midiFluidSynth/soundFonts/
    sf_local_relpath: Path = Path("d_frameworks_drivers") / "midiFluidSynth" / "soundFonts" / "1276-soft_tenor_sax.sf2"
    sf_system_path: Path = Path("/usr/share/sounds/sf2/FluidR3_GM.sf2")

    def iter_audio_drivers(self) -> Iterable[str]:
        yield self.preferred_driver
        for drv in self.fallback_drivers:
            yield drv

    def to_settings(self) -> PlaybackSettings:
        """Erzeuge neutrale PlaybackSettings für den Port/Adapter.

        Hinweis: Der SoundFont-Pfad ist bewusst NICHT Teil der Settings, sondern
        wird separat durch den FileSystemAdapter ermittelt und in den
        PlaybackRequest eingefügt.
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
