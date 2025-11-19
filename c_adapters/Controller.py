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


# Eingabemelodie (Choral) als Midi-Liste (Pitch, Dauer in Achteln)
wWIHNS_1 = [
    (53, 4), (53, 2), (55, 2), (57, 4), (55, 2), (58, 4), (57, 2), (55, 4), (53, 4),
    (57, 4), (58, 2), (57, 2), (55, 2), (53, 2), (52, 4), (53, 4), (55, 8), (60, 4),
    (58, 2), (57, 2), (55, 4), (57, 4), (53, 4), (50, 4), (48, 4), (57, 4), (58, 2),
    (57, 2), (55, 2), (53, 2), (57, 4), (55, 4), (53, 8)
]


class TwoPartCounterpointController:
    def __init__(self, base_path: Path | None = None) -> None:
        # base_path zeigt auf das Projekt-Root (eine Ebene über c_adapters)
        self.base_path = base_path or Path(__file__).resolve().parent.parent

    # --------- Anwendungsfluss ---------
    def run(self) -> int:
        """Kompatibilitäts-Wrapper.

        Hinweis: Die eigentliche Orchestrierung liegt nun in main.main().
        Diese Methode delegiert lediglich dorthin, damit bestehende Aufrufe
        (TwoPartCounterpointController().run()) weiterhin funktionieren.
        """
        from importlib import import_module

        main_mod = import_module("main")
        return int(getattr(main_mod, "main")())

    def build_choral(self):
        return Melodie(wWIHNS_1, f_dur)

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

        return kontrapunkt, harmonie

    def export_musescore(self, kontrapunkt: Melodie) -> Path:
        """Schreibt eine MuseScore-Datei mit dem erzeugten Kontrapunkt und gibt den Pfad zurück.

        Die Ausgabe wird im Unterordner "Kontrapunkte" abgelegt.
        """
        vorlage_pfad = self.base_path / "data" / "wWIHNS_Choral.mscx"
        with open(vorlage_pfad, "r", encoding="utf-8") as vorlage:
            anfang = vorlage.read(5116)
            x = vorlage.read()
        ende = x[-3251:]

        museScore = ""
        for i in range(0, len(kontrapunkt.notenliste), 1):
            laenge = kontrapunkt.notenliste[i][1]
            if laenge == 1:
                dots = ""
                durationType = "eighth"
            elif laenge == 2:
                dots = ""
                durationType = "quarter"
            elif laenge == 3:
                dots = "<dots>1</dots>"
                durationType = "quarter"
            elif laenge == 4:
                dots = ""
                durationType = "half"
            elif laenge == 6:
                dots = "<dots>1</dots>"
                durationType = "half"
            elif laenge == 8:
                dots = ""
                durationType = "whole"
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

        out_dir = self.base_path / "Kontrapunkte"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_pfad = out_dir / f"wWIHNS_mitKontrapunkt_{time.strftime('%b%d.%H-%M-%S')}.mscx"
        with open(out_pfad, "w", encoding="utf-8") as ausgabe:
            ausgabe.write(anfang)
            ausgabe.write(museScore)
            ausgabe.write(ende)
        return out_pfad

    def playback_realtime(self, choral: Melodie, kontrapunkt: Melodie):
        """Spielt Choral und Kontrapunkt in Echtzeit mit FluidSynth über PulseAudio (Fallback PipeWire)."""
        position_im_stueck = 0
        anzahl_zaehlzeiten_1, anzahl_zaehlzeiten_2 = 0, 0
        tick_seconds = 0.25

        fl = None
        midipitch_1 = None
        midipitch_2 = None

        try:
            # Synth initialisieren und SoundFont laden
            fl = fluidsynth.Synth(samplerate=44100.0, gain=1.0)
            sf_local = (self.base_path / "soundFonts/1276-soft_tenor_sax.sf2").resolve()
            sf_path = str(sf_local) if sf_local.exists() else \
                "/usr/share/sounds/sf2/FluidR3_GM.sf2"
            sfid = fl.sfload(sf_path)
            # Preset: zuerst Piano (0), bei Fehler Tenor Sax (65)
            preset_selected = False
            try:
                fl.program_select(0, sfid, 0, 0)
                preset_selected = True
            except Exception:
                pass
            if not preset_selected:
                try:
                    fl.program_select(0, sfid, 0, 65)
                    preset_selected = True
                except Exception:
                    pass

            # Audioausgabe starten: bevorzugt PulseAudio
            try:
                fl.start(driver="pulseaudio")
                print("FluidSynth: PulseAudio-Treiber aktiv.")
            except Exception as e:
                print("Warnung: PulseAudio konnte nicht gestartet werden (", e, ") – versuche PipeWire …")
                fl.start(driver="pipewire")
                print("FluidSynth: PipeWire-Treiber aktiv.")

            # Lautstärke sicherheitshalber hochziehen
            try:
                fl.cc(0, 7, 127)
                fl.cc(0, 11, 127)
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
                    fl.noteon(0, midipitch_1, 100)
                    anzahl_zaehlzeiten_1 += choral.notenliste[notenNummer_1][1]

                if position_im_stueck == anzahl_zaehlzeiten_2:
                    if position_im_stueck != 0 and midipitch_2 is not None:
                        fl.noteoff(0, midipitch_2)
                    notenNummer_2 = kontrapunkt.get_aktuelleNotenNummer(position_im_stueck)
                    midipitch_2 = kontrapunkt.notenliste[notenNummer_2][0]
                    fl.noteon(0, midipitch_2, 100)
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
            time.sleep(1.0)

        except KeyboardInterrupt:
            print("Abbruch per Strg+C während der Audioausgabe.")
        finally:
            try:
                if fl is not None:
                    fl.delete()
            except Exception:
                pass
