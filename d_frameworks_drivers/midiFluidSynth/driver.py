#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

"""FluidSynth-basierter Playback-Driver (Frameworks/Drivers-Schicht).

Diese Klasse implementiert den CounterpointPlaybackPort und kapselt die
gesamte FluidSynth-/MIDI-Echtzeitlogik. Dadurch bleibt die Adapter-/
Controller-Schicht frei von FluidSynth-Details (Clean Architecture).
"""

import os
import time
from pathlib import Path

from c_adapters.ports.playback_port import CounterpointPlaybackPort, PlaybackRequest
from .config import MidiFluidSynthConfig


class FluidSynthPlaybackDriver(CounterpointPlaybackPort):
    def __init__(self, project_root: Path, cfg: MidiFluidSynthConfig | None = None) -> None:
        self.project_root = project_root
        self.cfg = cfg or MidiFluidSynthConfig()

    # --- interne Helfer ---
    def _choose_soundfont(self) -> str:
        # 1) explizit via ENV
        env_sf = os.environ.get("FS_SF2")
        if env_sf and Path(env_sf).exists():
            return env_sf
        # 2) projektlokal (gemäß Driver-Config)
        local = (self.project_root / self.cfg.sf_local_relpath).resolve()
        if local.exists():
            return str(local)
        # 3) systemweit (gemäß Driver-Config)
        return str(self.cfg.sf_system_path)

    # --- Port-Implementierung ---
    def play(self, request: PlaybackRequest) -> None:  # noqa: C901 (Komplexität ok, da eng gekapselt)
        try:
            import fluidsynth  # lokale Abhängigkeit nur im Driver
        except Exception as e:  # pragma: no cover - Importfehler klar benennen
            raise RuntimeError(
                "pyfluidsynth/fluidsynth konnte nicht importiert werden. Bitte installieren: 'pip install pyfluidsynth'."
            ) from e

        settings = request.settings
        choral = request.choral
        kontrapunkt = request.kontrapunkt

        position_im_stueck = 0
        anzahl_zaehlzeiten_1, anzahl_zaehlzeiten_2 = 0, 0
        midipitch_1 = None
        midipitch_2 = None
        fl = None

        try:
            # Synth initialisieren
            fl = fluidsynth.Synth(samplerate=settings.samplerate, gain=settings.gain)

            # SoundFont wählen und laden
            sf_path = self._choose_soundfont()
            if not Path(sf_path).exists():
                raise FileNotFoundError(
                    f"Kein gültiger SoundFont gefunden (versucht: {sf_path}). Setze ENV FS_SF2 oder lege eine .sf2 in soundFonts/."
                )
            sfid = fl.sfload(sf_path)

            # Preset auswählen (erste funktionierende Kombination verwenden)
            preset_selected = False
            for bank, program in settings.presets:
                try:
                    fl.program_select(0, sfid, bank, program)
                    preset_selected = True
                    break
                except Exception:
                    continue
            if not preset_selected:
                # Fallback: GM Piano
                try:
                    fl.program_select(0, sfid, 0, 0)
                except Exception:
                    pass

            # Audio-Treiber starten (z. B. pulseaudio → pipewire)
            last_err = None
            for drv in settings.drivers:
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
                fl.cc(0, 7, settings.cc_volume)      # CC7 Volume
                fl.cc(0, 11, settings.cc_expression)  # CC11 Expression
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
                    fl.noteon(0, midipitch_1, settings.midi_velocity)
                    anzahl_zaehlzeiten_1 += choral.notenliste[notenNummer_1][1]

                if position_im_stueck == anzahl_zaehlzeiten_2:
                    if position_im_stueck != 0 and midipitch_2 is not None:
                        fl.noteoff(0, midipitch_2)
                    notenNummer_2 = kontrapunkt.get_aktuelleNotenNummer(position_im_stueck)
                    midipitch_2 = kontrapunkt.notenliste[notenNummer_2][0]
                    fl.noteon(0, midipitch_2, settings.midi_velocity)
                    anzahl_zaehlzeiten_2 += kontrapunkt.notenliste[notenNummer_2][1]

                position_im_stueck += 1
                next_time = t0 + position_im_stueck * settings.tick_seconds
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
            time.sleep(max(0.0, settings.fadeout_seconds))

        except KeyboardInterrupt:
            print("Abbruch per Strg+C während der Audioausgabe.")
        finally:
            try:
                if fl is not None:
                    fl.delete()
            except Exception:
                pass
