#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path

from c_adapters.Controller import TwoPartCounterpointController
from c_adapters.config import AppConfig
from c_adapters.FileSystemAdapter import FileSystemAdapter
from c_adapters.MuseScoreXmlAdapter import MuseScoreXmlAdapter
from b_application.generate_counterpoint_use_case import GenerateCounterpointUseCase
from b_application.build_note_events_use_case import BuildNoteEventsUseCase
from b_application.use_case_interactor import UseCaseInteractor
from d_frameworks_drivers.musescore.exporter import MuseScoreFileExporter
from d_frameworks_drivers.midiFluidSynth.driver import FluidSynthPlaybackDriver
from d_frameworks_drivers.musescore.config import MuseScoreConfig


def main() -> int:
    base = Path(__file__).resolve().parent
    app_cfg = AppConfig()
    ms_cfg = MuseScoreConfig()

    # Adapter/Driver für MuseScore-Export (alle Abhängigkeiten hier gebaut)
    fs = FileSystemAdapter(base)
    xml = MuseScoreXmlAdapter()
    score_exporter = MuseScoreFileExporter(project_root=base, app_cfg=app_cfg, ms_cfg=ms_cfg, fs=fs, xml=xml)
    # Playback-Driver (FluidSynth) – nutzt Default-Konfiguration
    playback_driver = FluidSynthPlaybackDriver(project_root=base)

    # Application-Use-Cases und Interactor
    generate_uc = GenerateCounterpointUseCase()
    sequencer = BuildNoteEventsUseCase()
    interactor = UseCaseInteractor(generate_uc=generate_uc, sequencer=sequencer)

    ctrl = TwoPartCounterpointController(
        config=app_cfg,
        score_exporter=score_exporter,
        playback_port=playback_driver,
        interactor=interactor,
    )

    # 1) Domänenobjekte aufbauen
    choral = ctrl.build_choral()
    kontrapunkt = ctrl.generate_counterpoint(choral)

    # 2) Export
    ctrl.export_musescore(kontrapunkt)

    # 3) Wiedergabe
    ctrl.playback_realtime(choral, kontrapunkt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
