#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Einstiegspunkt und Orchestrierung der Anwendung.

MuseScore-spezifische Details liegen in d_frameworks_drivers.musescore.
Hier wird die konkrete Export-Implementierung erstellt und über einen
Port (ScoreExportPort) in den Controller injiziert.
"""

from pathlib import Path

from c_adapters.Controller import TwoPartCounterpointController
from c_adapters.config import AppConfig
from d_frameworks_drivers.musescore.exporter import MuseScoreFileExporter
from d_frameworks_drivers.midiFluidSynth.config import MidiFluidSynthConfig
from d_frameworks_drivers.midiFluidSynth.driver import FluidSynthPlaybackDriver


def main() -> int:
    base = Path(__file__).resolve().parent
    app_cfg = AppConfig()
    score_exporter = MuseScoreFileExporter(project_root=base, app_cfg=app_cfg)
    # Playback-Driver (FluidSynth) und neutrale Settings
    mf_cfg = MidiFluidSynthConfig()
    playback_settings = mf_cfg.to_settings()
    playback_driver = FluidSynthPlaybackDriver(project_root=base, cfg=mf_cfg)

    # Controller instanziieren (liefert Pfad- und Hilfsfunktionen)
    ctrl = TwoPartCounterpointController(
        base_path=base,
        config=app_cfg,
        score_exporter=score_exporter,
        playback_port=playback_driver,
    )

    # 1) Domänenobjekte aufbauen
    choral = ctrl.build_choral()
    kontrapunkt = ctrl.generate_counterpoint(choral)

    # 2) Export
    ctrl.export_musescore(kontrapunkt)

    # 3) Wiedergabe
    ctrl.playback_realtime(choral, kontrapunkt, playback_settings)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
