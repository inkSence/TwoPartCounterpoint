#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
from abc import ABC, abstractmethod

from a_domain.Melodie import Melodie
from typing import Sequence

# Forward-Ref, um zirkuläre Imports zu vermeiden
try:
    from b_application.build_note_events_use_case import NoteEvent
except Exception:  # pragma: no cover - zur Importzeit evtl. noch nicht vorhanden
    class NoteEvent:  # type: ignore[misc]
        ...


@dataclass(frozen=True)
class PlaybackRequest:
    """Beschreibt einen kompletten Abspielauftrag für einen zweistimmigen Kontrapunkt.

    Diese neutrale DTO wird der konkreten Playback-Implementierung (Driver)
    übergeben. Sie enthält die Musikdaten und eine vorgeplante
    Eventliste (Note-On/Off in Ticks). Der konkrete Driver liest seine
    Wiedergabe-Parameter aus
    seiner eigenen Konfiguration.
    """

    # Musikdaten
    choral: Melodie
    kontrapunkt: Melodie

    # Vorgeplante Ereignisse (Note-On/Off) in Ticks – Pflicht
    events: Sequence[NoteEvent]


class CounterpointPlaybackPort(ABC):
    """Abstrakte Schnittstelle für das Abspielen eines zweistimmigen Kontrapunkts."""

    @abstractmethod
    def play(self, request: PlaybackRequest) -> None:
        """Startet die Wiedergabe entsprechend der Angaben im Request und blockiert,
        bis die Wiedergabe abgeschlossen ist oder abgebrochen wurde.
        """
        raise NotImplementedError
