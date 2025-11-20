#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""MidiAdapter

Dieser Adapter baut aus Domain-Objekten und der Anwendungs-/FS-Konfiguration
einen `PlaybackRequest`, der über den Port `CounterpointPlaybackPort` von einer
konkreten Driver-Implementierung (z. B. d_frameworks_drivers.midiFluidSynth)
abgearbeitet werden kann.

"""

from __future__ import annotations


from a_domain.Melodie import Melodie
from .ports.playback_port import PlaybackRequest, PlaybackSettings
from typing import Sequence, Optional
try:
    # nur für Typen, zur Laufzeit optional
    from b_application.build_note_events_use_case import NoteEvent
except Exception:  # pragma: no cover
    class NoteEvent:  # type: ignore[misc]
        ...


class MidiAdapter:
    def __init__(self) -> None:
        # Zustandsloser Adapter: baut nur DTOs
        pass

    def build_request(
        self,
        choral: Melodie,
        kontrapunkt: Melodie,
        settings: PlaybackSettings,
        events: Optional[Sequence[NoteEvent]] = None,
    ) -> PlaybackRequest:
        """Erstellt einen neutralen PlaybackRequest für den Driver.

        Hinweis: Alle Abspiel-Parameter kommen über `settings` aus der äußeren
        Schicht (z. B. d_frameworks_drivers.midiFluidSynth.config) und NICHT
        aus c_adapters.config.
        """
        return PlaybackRequest(
            choral=choral,
            kontrapunkt=kontrapunkt,
            settings=settings,
            events=tuple(events) if events is not None else None,
        )
