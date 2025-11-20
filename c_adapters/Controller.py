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

from a_domain.Melodie import Melodie
from b_application.use_case_interactor import UseCaseInteractor
from .config import AppConfig
from .ports.score_export_port import ScoreExportPort
from .ports.playback_port import CounterpointPlaybackPort
from .MidiAdapter import MidiAdapter


class TwoPartCounterpointController:
    def __init__(self,
                 config: AppConfig,
                 score_exporter: ScoreExportPort,
                 playback_port: CounterpointPlaybackPort,
                 midi_adapter: MidiAdapter,
                 interactor: UseCaseInteractor) -> None:
        """Controller, dessen Abhängigkeiten vollständig via Main verdrahtet werden.
        """
        self.config = config
        # Ports/Adapter/Use-Cases (DI)
        self.score_exporter = score_exporter
        self.playback_port = playback_port
        self.midi_adapter = midi_adapter
        self.interactor = interactor

    def build_choral(self):
        return self.interactor.build_choral(self.config.wWIHNS_1)

    # --------- Use-Case-Delegation ---------
    def generate_counterpoint(self, choral: Melodie):
        """Delegiert an den Application-Use-Case und liefert den Kontrapunkt zurück."""
        return self.interactor.generate_counterpoint(choral)

    def export_musescore(self, kontrapunkt: Melodie):
        """Exportiert den Kontrapunkt über den konfigurierten Score-Exporter und gibt den Pfad zurück."""
        out_pfad = self.score_exporter.export_melody(kontrapunkt)
        print(f"MuseScore-Datei geschrieben: {out_pfad}")

    def playback_realtime(self, choral: Melodie, kontrapunkt: Melodie) -> None:
        """Spielt Choral und Kontrapunkt über den injizierten Playback-Port ab.
        """
        # Events zentral im Interactor erzeugen
        events = self.interactor.build_note_events(choral, kontrapunkt)
        # Request mit den erzeugten Events bauen
        request = self.midi_adapter.build_request(choral, kontrapunkt, events=events)
        self.playback_port.play(request)
