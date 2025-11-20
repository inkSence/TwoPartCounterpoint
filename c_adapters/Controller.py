#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from a_domain.Melodie import Melodie
from b_application.use_case_interactor import UseCaseInteractor
from c_adapters.config import AppConfig
from c_adapters.ports.score_export_port import ScoreExportPort
from c_adapters.ports.playback_port import CounterpointPlaybackPort

class TwoPartCounterpointController:
    def __init__(self,
                 config: AppConfig,
                 score_exporter: ScoreExportPort,
                 playback_port: CounterpointPlaybackPort,
                 interactor: UseCaseInteractor) -> None:

        self.config = config
        # Ports/Adapter/Use-Cases (DI)
        self.score_exporter = score_exporter
        self.playback_port = playback_port
        self.interactor = interactor

    def build_choral(self):
        return self.interactor.build_choral(self.config.wWIHNS_1)

    def generate_counterpoint(self, choral: Melodie):
        return self.interactor.generate_counterpoint(choral)

    def export_musescore(self, kontrapunkt: Melodie):
        out_pfad = self.score_exporter.export_melody(kontrapunkt)
        print(f"MuseScore-Datei geschrieben: {out_pfad}")

    def playback_realtime(self, choral: Melodie, kontrapunkt: Melodie) -> None:
        events = self.interactor.build_note_events(choral, kontrapunkt)
        self.playback_port.play(events)
