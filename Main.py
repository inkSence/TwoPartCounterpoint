#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Einstiegspunkt und Orchestrierung der Anwendung.

"""

from c_adapters.Controller import TwoPartCounterpointController


def main() -> int:
    # Controller instanziieren (liefert Pfad- und Hilfsfunktionen)
    ctrl = TwoPartCounterpointController()

    # 1) Domänenobjekte aufbauen
    choral = ctrl.build_choral()
    kontrapunkt, _harmonie = ctrl.generate_contrapunt(choral)

    # 2) Export
    out_file = ctrl.export_musescore(kontrapunkt)
    print(f"MuseScore-Datei geschrieben: {out_file}")

    # 3) Wiedergabe
    ctrl.playback_realtime(choral, kontrapunkt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
