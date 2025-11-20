#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
from abc import ABC, abstractmethod

from a_domain.Melodie import Melodie
from typing import Sequence, Optional
import logging
logging.basicConfig(level=logging.INFO)

# Forward-Ref, um zirkuläre Imports zu vermeiden
try:
    from b_application.build_note_events_use_case import NoteEvent
except Exception:  # pragma: no cover - zur Importzeit evtl. noch nicht vorhanden
    class NoteEvent:  # type: ignore[misc]
        logging.exception("Unable to import NoteEvent")


@dataclass(frozen=True)
class PlaybackSettings:
    """Neutrale Abspiel-Parameter ohne Abhängigkeit von einem konkreten Driver.

    Diese Struktur kann von der äußeren Schicht (z. B. einem FluidSynth-Driver)
    befüllt werden und dient dem Adapter als Eingabe für den Request-Bau.
    """

    # Zeitsteuerung
    tick_seconds: float
    fadeout_seconds: float

    # Audio / Synth
    samplerate: float
    gain: float
    drivers: tuple[str, ...]  # bevorzugter Treiber zuerst, dann Fallbacks

    # MIDI-Parameter
    midi_velocity: int
    cc_volume: int  # CC7
    cc_expression: int  # CC11

    # Presets (ohne konkrete Synth-Details)
    presets: tuple[tuple[int, int], ...]  # (bank, program)


@dataclass(frozen=True)
class PlaybackRequest:
    """Beschreibt einen kompletten Abspielauftrag für einen zweistimmigen Kontrapunkt.

    Diese neutrale DTO wird der konkreten Playback-Implementierung (Driver)
    übergeben. Sie enthält die Musikdaten und die allgemeinen Abspiel-Parameter
    (PlaybackSettings). Der Driver selbst entscheidet anhand seiner eigenen
    Konfiguration, welchen SoundFont er verwendet.
    """

    # Musikdaten
    choral: Melodie
    kontrapunkt: Melodie

    # Allgemeine Abspiel-Parameter
    settings: PlaybackSettings

    # Optional: Vorgeplante Ereignisse (Note-On/Off) in Ticks
    events: Optional[Sequence[NoteEvent]] = None


class CounterpointPlaybackPort(ABC):
    """Abstrakte Schnittstelle für das Abspielen eines zweistimmigen Kontrapunkts."""

    @abstractmethod
    def play(self, request: PlaybackRequest) -> None:
        """Startet die Wiedergabe entsprechend der Angaben im Request und blockiert,
        bis die Wiedergabe abgeschlossen ist oder abgebrochen wurde.
        """
        raise NotImplementedError
