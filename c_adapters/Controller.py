#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Adapter/Controller gemäß Clean Architecture.

Dieser Controller kapselt die Orchestrierung der Anwendung:
- Generierung des Kontrapunkts aus einer gegebenen Choral-Melodie
- Export über einen Score-Export-Port
- Wiedergabe über einen Playback-Port (Driver wird injiziert)

Dadurch bleibt main.py schlank und die Adapter-Schicht frei von Driver-Details.
"""

from __future__ import annotations

from pathlib import Path

from a_domain.Melodie import Melodie
from a_domain.Tonleitern import f_dur
from .config import AppConfig
from .ports.score_export_port import ScoreExportPort
from .ports.playback_port import CounterpointPlaybackPort, PlaybackSettings
from .MidiAdapter import MidiAdapter
from b_application.use_case_interactor import UseCaseInteractor

class TwoPartCounterpointController:
    def __init__(self, base_path: Path | None = None, config: AppConfig | None = None,
                 score_exporter: ScoreExportPort | None = None,
                 playback_port: CounterpointPlaybackPort | None = None,
                 midi_adapter: MidiAdapter | None = None,
                 interactor: UseCaseInteractor | None = None) -> None:
        # base_path zeigt auf das Projekt-Root (eine Ebene über c_adapters)
        self.base_path = base_path or Path(__file__).resolve().parent.parent
        self.config = config or AppConfig()
        # Port für Partitur-Export (wird in Main per DI gesetzt)
        self.score_exporter = score_exporter
        # Port für Wiedergabe (Driver, wird in Main per DI gesetzt)
        self.playback_port = playback_port
        # Adapter zum Bau des Playback-Requests (neutral)
        self.midi_adapter = midi_adapter or MidiAdapter()
        # Use-Case-Interactor (Application-Schicht)
        self.interactor = interactor or UseCaseInteractor()

    def build_choral(self):
        return Melodie(self.config.wWIHNS_1, f_dur)

    # --------- Use-Case-Delegation ---------
    def generate_counterpoint(self, choral: Melodie):
        """Delegiert an den Application-Use-Case und liefert den Kontrapunkt zurück."""
        return self.interactor.generate_counterpoint(choral)

    def export_musescore(self, kontrapunkt: Melodie):
        """Exportiert den Kontrapunkt über den konfigurierten Score-Exporter und gibt den Pfad zurück."""
        if self.score_exporter is None:
            raise RuntimeError("Kein ScoreExportPort konfiguriert. Bitte in main einen Exporter injizieren.")
        out_pfad = self.score_exporter.export_melody(kontrapunkt)
        print(f"MuseScore-Datei geschrieben: {out_pfad}")

    def playback_realtime(self, choral: Melodie, kontrapunkt: Melodie, settings: PlaybackSettings) -> None:
        """Spielt Choral und Kontrapunkt über den injizierten Playback-Port ab.

        Der Controller kennt keine FluidSynth-Details mehr. Er baut lediglich
        einen neutralen PlaybackRequest über den MidiAdapter. Die nötigen
        Note-Events werden in der Application-Schicht (UseCaseInteractor)
        erzeugt und hier übergeben. Anschließend wird der Request an den
        Playback-Port (Driver) übergeben.
        """
        if self.playback_port is None:
            raise RuntimeError("Kein CounterpointPlaybackPort konfiguriert. Bitte in main einen Playback-Driver injizieren.")

        # Events zentral im Interactor erzeugen
        events = self.interactor.build_note_events(choral, kontrapunkt)
        # Request mit den erzeugten Events bauen
        request = self.midi_adapter.build_request(choral, kontrapunkt, settings, events=events)
        self.playback_port.play(request)
