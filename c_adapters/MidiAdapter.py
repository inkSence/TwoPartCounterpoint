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
from b_application.build_note_events_use_case import BuildNoteEventsUseCase


class MidiAdapter:
    def __init__(self, sequencer: BuildNoteEventsUseCase | None = None) -> None:
        # Sequencer für Event-Erzeugung (optional injizierbar)
        self.sequencer = sequencer or BuildNoteEventsUseCase()

    def build_request(self, choral: Melodie, kontrapunkt: Melodie, settings: PlaybackSettings) -> PlaybackRequest:
        """Erstellt einen neutralen PlaybackRequest für den Driver.

        Hinweis: Alle Abspiel-Parameter kommen über `settings` aus der äußeren
        Schicht (z. B. d_frameworks_drivers.midiFluidSynth.config) und NICHT
        aus c_adapters.config.
        """
        events = self.sequencer.execute(choral, kontrapunkt)
        return PlaybackRequest(
            choral=choral,
            kontrapunkt=kontrapunkt,
            settings=settings,
            events=tuple(events),
        )
