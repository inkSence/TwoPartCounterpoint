#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Adapter/Controller gemäß Clean Architecture.

Dieser Controller kapselt die Orchestrierung der Anwendung:
- Generierung des Kontrapunkts aus einer gegebenen Choral-Melodie
- Export nach MuseScore
- Echtzeit-Wiedergabe über FluidSynth (PulseAudio, Fallback PipeWire)

Dadurch bleibt main.py schlank und enthält nur noch den Programmstart.
"""

from __future__ import annotations

import time
from pathlib import Path

import fluidsynth

from a_domain.Melodie import Melodie
from a_domain.HarmonischeStruktur import HarmonischeStruktur
from a_domain.KpRegeln import KpRegeln
from a_domain.Tonleitern import f_dur
from .config import AppConfig
from .FileSystemAdapter import FileSystemAdapter
from .fs_config import FileSystemConfig


class TwoPartCounterpointController:
    def __init__(self, base_path: Path | None = None, config: AppConfig | None = None) -> None:
        # base_path zeigt auf das Projekt-Root (eine Ebene über c_adapters)
        self.base_path = base_path or Path(__file__).resolve().parent.parent
        self.config = config or AppConfig()
        # FileSystem-Adapter für alle Dateioperationen
        self.fs = FileSystemAdapter(self.base_path, FileSystemConfig())

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

    def export_musescore(self, kontrapunkt: Melodie) -> Path:
        """Schreibt eine MuseScore-Datei mit dem erzeugten Kontrapunkt und gibt den Pfad zurück.

        Die Ausgabe wird im Unterordner "Kontrapunkte" abgelegt.
        """
        # Body-XML aus den Noten erzeugen
        museScore = ""
        for i in range(0, len(kontrapunkt.notenliste), 1):
            laenge = kontrapunkt.notenliste[i][1]
            durationType, dots = self.config.score_duration_map.get(laenge, ("quarter", ""))
            museScore = (
                museScore
                + "<Chord>"
                + str(dots)
                + "<durationType>"
                + str(durationType)
                + "</durationType><Note><pitch>"
                + str(kontrapunkt.notenliste[i][0])
                + "</pitch></Note></Chord>\n"
            )
        # Datei über den FileSystemAdapter schreiben
        out_pfad = self.fs.write_musescore_file(museScore)
        print(f"MuseScore-Datei geschrieben: {out_pfad}")
        return out_pfad

    def playback_realtime(self, choral: Melodie, kontrapunkt: Melodie):
        """Spielt Choral und Kontrapunkt in Echtzeit mit FluidSynth über PulseAudio (Fallback PipeWire)."""
        position_im_stueck = 0
        anzahl_zaehlzeiten_1, anzahl_zaehlzeiten_2 = 0, 0
        tick_seconds = self.config.tick_seconds

        fl = None
        midipitch_1 = None
        midipitch_2 = None

        try:
            # Synth initialisieren und SoundFont laden
            fl = fluidsynth.Synth(samplerate=self.config.synth_samplerate, gain=self.config.synth_gain)
            # SoundFont-Pfad über FileSystemAdapter wählen
            sf_path = str(self.fs.choose_soundfont_path())
            sfid = fl.sfload(sf_path)
            # Preset-Reihenfolge aus Konfiguration
            preset_selected = False
            for bank, program in self.config.sf_presets:
                try:
                    fl.program_select(0, sfid, bank, program)
                    preset_selected = True
                    break
                except Exception:
                    continue

            # Audioausgabe starten: bevorzugt PulseAudio
            last_err = None
            for drv in self.config.iter_audio_drivers():
                try:
                    fl.start(driver=drv)
                    print(f"FluidSynth: {drv}-Treiber aktiv.")
                    last_err = None
                    break
                except Exception as e:
                    last_err = e
                    print(f"Warnung: {drv} konnte nicht gestartet werden ({e}).")
            if last_err is not None:
                raise last_err

            # Lautstärke sicherheitshalber hochziehen
            try:
                fl.cc(0, 7, self.config.midi_cc_volume)
                fl.cc(0, 11, self.config.midi_cc_expression)
            except Exception:
                pass

            # Zeitgesteuerte Echtzeit-Schleife
            t0 = time.perf_counter()
            laenge_des_stuecks = choral.laenge()
            for _ in range(0, laenge_des_stuecks, 1):
                if position_im_stueck == anzahl_zaehlzeiten_1:
                    if position_im_stueck != 0 and midipitch_1 is not None:
                        fl.noteoff(0, midipitch_1)
                    notenNummer_1 = choral.get_aktuelleNotenNummer(position_im_stueck)
                    midipitch_1 = choral.notenliste[notenNummer_1][0]
                    fl.noteon(0, midipitch_1, self.config.midi_velocity)
                    anzahl_zaehlzeiten_1 += choral.notenliste[notenNummer_1][1]

                if position_im_stueck == anzahl_zaehlzeiten_2:
                    if position_im_stueck != 0 and midipitch_2 is not None:
                        fl.noteoff(0, midipitch_2)
                    notenNummer_2 = kontrapunkt.get_aktuelleNotenNummer(position_im_stueck)
                    midipitch_2 = kontrapunkt.notenliste[notenNummer_2][0]
                    fl.noteon(0, midipitch_2, self.config.midi_velocity)
                    anzahl_zaehlzeiten_2 += kontrapunkt.notenliste[notenNummer_2][1]

                position_im_stueck += 1
                next_time = t0 + position_im_stueck * tick_seconds
                now = time.perf_counter()
                sleep_time = next_time - now
                if sleep_time > 0:
                    time.sleep(sleep_time)

            # Ausklang
            try:
                if midipitch_1 is not None:
                    fl.noteoff(0, midipitch_1)
                if midipitch_2 is not None:
                    fl.noteoff(0, midipitch_2)
            except Exception:
                pass
            time.sleep(self.config.fadeout_seconds)

        except KeyboardInterrupt:
            print("Abbruch per Strg+C während der Audioausgabe.")
        finally:
            try:
                if fl is not None:
                    fl.delete()
            except Exception:
                pass
