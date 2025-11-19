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
from a_domain.HarmonischeStruktur import HarmonischeStruktur
from a_domain.KpRegeln import KpRegeln
from a_domain.Tonleitern import f_dur
from .config import AppConfig
from .FileSystemAdapter import FileSystemAdapter
from .ports.score_export_port import ScoreExportPort
from .ports.playback_port import CounterpointPlaybackPort, PlaybackSettings
from .MidiAdapter import MidiAdapter


class TwoPartCounterpointController:
    def __init__(self, base_path: Path | None = None, config: AppConfig | None = None,
                 score_exporter: ScoreExportPort | None = None,
                 playback_port: CounterpointPlaybackPort | None = None,
                 midi_adapter: MidiAdapter | None = None) -> None:
        # base_path zeigt auf das Projekt-Root (eine Ebene über c_adapters)
        self.base_path = base_path or Path(__file__).resolve().parent.parent
        self.config = config or AppConfig()
        # FileSystem-Adapter für alle Dateioperationen
        self.fs = FileSystemAdapter(self.base_path)
        # Port für Partitur-Export (wird in Main per DI gesetzt)
        self.score_exporter = score_exporter
        # Port für Wiedergabe (Driver, wird in Main per DI gesetzt)
        self.playback_port = playback_port
        # Adapter zum Bau des Playback-Requests (neutral)
        self.midi_adapter = midi_adapter or MidiAdapter(self.base_path, self.fs)

    def build_choral(self):
        return Melodie(self.config.wWIHNS_1, f_dur)

    # --------- Use-Case-ähnliche Schritte ---------
    def generate_contrapunt(self, choral: Melodie):
        """Erzeugt den Kontrapunkt und gibt (kontrapunkt, harmonie) zurück."""
        kontrapunkt = Melodie([], f_dur)
        harmonie = HarmonischeStruktur(choral, kontrapunkt)
        regeln = KpRegeln(harmonie, choral, kontrapunkt)

        position_im_stueck = 0
        anzahl_zaehlzeiten_1, anzahl_zaehlzeiten_2 = 0, 0

        laenge_des_stuecks = choral.laenge()

        while position_im_stueck < laenge_des_stuecks:
            ton_2 = [True]
            if position_im_stueck == anzahl_zaehlzeiten_1:
                notenNummer_1 = choral.get_aktuelleNotenNummer(position_im_stueck)
                midipitch_1 = choral.notenliste[notenNummer_1][0]
                anzahl_zaehlzeiten_1 = choral.laenge()
                choral.letzte_drei_haben_Extremum(notenNummer_1)

            if position_im_stueck == anzahl_zaehlzeiten_2:
                if position_im_stueck == 0:
                    midipitch_2 = midipitch_1 + 12  # type: ignore[name-defined]
                    notenlaenge = harmonie.notenlaenge_waehlen(
                        harmonie.get_erlaubte_notenlaenge(harmonie.get_taktposition(position_im_stueck))
                    )
                    kontrapunkt.notenliste.append((midipitch_2, notenlaenge))
                    anzahl_zaehlzeiten_2 = notenlaenge
                else:
                    ton_2 = regeln.get_contra(position_im_stueck)
                    midipitch_2 = ton_2[1]
                    notenlaenge = ton_2[2]
                    if ton_2[0] == True:
                        kontrapunkt.notenliste.append((midipitch_2, notenlaenge))
                    else:
                        position_im_stueck = ton_2[3] - 1
                    anzahl_zaehlzeiten_2 = kontrapunkt.laenge()

            if ton_2[0] == True:
                if choral.note_beginnt_gerade(position_im_stueck) == True or kontrapunkt.note_beginnt_gerade(position_im_stueck) == True:
                    interval = harmonie.get_interval(
                        choral.notenliste[choral.get_aktuelleNotenNummer(position_im_stueck)][0],
                        kontrapunkt.notenliste[kontrapunkt.get_aktuelleNotenNummer(position_im_stueck)][0],
                    )
                    harmonie.interval_qualities.append(
                        (position_im_stueck, interval, harmonie.interval_quality(interval))
                    )
            position_im_stueck += 1

        return kontrapunkt

    def export_musescore(self, kontrapunkt: Melodie):
        """Exportiert den Kontrapunkt über den konfigurierten Score-Exporter und gibt den Pfad zurück."""
        if self.score_exporter is None:
            raise RuntimeError("Kein ScoreExportPort konfiguriert. Bitte in main einen Exporter injizieren.")
        out_pfad = self.score_exporter.export_melody(kontrapunkt)
        print(f"MuseScore-Datei geschrieben: {out_pfad}")

    def playback_realtime(self, choral: Melodie, kontrapunkt: Melodie, settings: PlaybackSettings) -> None:
        """Spielt Choral und Kontrapunkt über den injizierten Playback-Port ab.

        Der Controller kennt keine FluidSynth-Details mehr. Er baut lediglich
        einen neutralen PlaybackRequest über den MidiAdapter und übergibt ihn
        an den Playback-Port (Driver).
        """
        if self.playback_port is None:
            raise RuntimeError("Kein CounterpointPlaybackPort konfiguriert. Bitte in main einen Playback-Driver injizieren.")
        if self.midi_adapter is None:
            # Sollte nie passieren, da im Konstruktor ein Default gebaut wird
            self.midi_adapter = MidiAdapter(self.base_path, self.fs)

        request = self.midi_adapter.build_request(choral, kontrapunkt, settings)
        self.playback_port.play(request)
