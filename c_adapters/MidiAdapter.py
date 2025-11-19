#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""MidiAdapter (Clean Architecture, Adapter-Schicht)

Dieser Adapter baut aus Domain-Objekten und der Anwendungs-/FS-Konfiguration
einen `PlaybackRequest`, der über den Port `CounterpointPlaybackPort` von einer
konkreten Driver-Implementierung (z. B. d_frameworks_drivers.midiFluidSynth)
abgearbeitet werden kann.

Wichtig: Dieser Adapter spielt NICHT selbst ab und hängt nicht von FluidSynth.
Er kapselt nur die Aggregation der nötigen Parameter.
"""

from __future__ import annotations

from pathlib import Path

from a_domain.Melodie import Melodie
from .FileSystemAdapter import FileSystemAdapter
from .ports.playback_port import PlaybackRequest, PlaybackSettings


class MidiAdapter:
    def __init__(self, base_path: Path, fs: FileSystemAdapter) -> None:
        self.base_path = base_path
        self.fs = fs

    def build_request(self, choral: Melodie, kontrapunkt: Melodie, settings: PlaybackSettings) -> PlaybackRequest:
        """Erstellt einen neutralen PlaybackRequest für den Driver.

        Hinweis: Alle Abspiel-Parameter kommen über `settings` aus der äußeren
        Schicht (z. B. d_frameworks_drivers.midiFluidSynth.config) und NICHT
        aus c_adapters.config.
        """
        return PlaybackRequest(
            choral=choral,
            kontrapunkt=kontrapunkt,
            settings=settings,
        )
