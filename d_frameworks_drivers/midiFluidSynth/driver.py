#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

"""FluidSynth-basierter Playback-Driver (Frameworks/Drivers-Schicht).

Diese Klasse implementiert den CounterpointPlaybackPort und kapselt die
gesamte FluidSynth-/MIDI-Echtzeitlogik. Dadurch bleibt die Adapter-/
Controller-Schicht frei von FluidSynth-Details (Clean Architecture).
"""

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
        """Ermittelt den SoundFont ausschließlich aus dem paketlokalen Ordner.

        Zugelassener Suchort:
        - d_frameworks_drivers/midiFluidSynth/soundFonts/
        """
        pkg_sf_dir = (self.project_root / "d_frameworks_drivers" / "midiFluidSynth" / "soundFonts").resolve()

        # Präferenz: in der Config angegebener lokale Standard (liegt ebenfalls unterhalb des Paketordners)
        cfg_local = (self.project_root / self.cfg.sf_local_relpath).resolve()
        if cfg_local.exists():
            return str(cfg_local)

        # Feste Kandidaten im paketlokalen Ordner
        pkg_candidates = [
            pkg_sf_dir / "1276-soft_tenor_sax.sf2",
            pkg_sf_dir / "alto_sax_2.sf2",
            pkg_sf_dir / "example.sf2",
        ]
        for c in pkg_candidates:
            if c.exists():
                return str(c)

        # Nichts gefunden: klare Fehlermeldung (nur paketlokaler Ort wird unterstützt)
        raise FileNotFoundError(
            "Kein SoundFont gefunden. Lege eine .sf2 in d_frameworks_drivers/midiFluidSynth/soundFonts/."
        )

    # --- Port-Implementierung ---
    def play(self, request: PlaybackRequest) -> None:  # noqa: C901 (Komplexität ok, da eng gekapselt)
        try:
            import fluidsynth  # lokale Abhängigkeit nur im Driver
        except Exception as e:  # pragma: no cover - Importfehler klar benennen
            raise RuntimeError(
                "pyfluidsynth/fluidsynth konnte nicht importiert werden. Bitte installieren: 'pip install pyfluidsynth'."
            ) from e

        settings = request.settings
        fl = None

        try:
            # Synth initialisieren
            fl = fluidsynth.Synth(samplerate=settings.samplerate, gain=settings.gain)

            # SoundFont wählen und laden
            sf_path = self._choose_soundfont()
            if not Path(sf_path).exists():
                raise FileNotFoundError(
                    f"Kein gültiger SoundFont gefunden (versucht: {sf_path}). "
                    "Lege eine .sf2 in d_frameworks_drivers/midiFluidSynth/soundFonts/."
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

            # Zeitgesteuerte Echtzeit-Schleife (nur noch Event-basiert)
            if not request.events:
                raise ValueError(
                    "PlaybackRequest.events fehlen – bitte den MidiAdapter/Sequencer verwenden."
                )

            t0 = time.perf_counter()
            for ev in request.events:
                target = t0 + ev.time_tick * settings.tick_seconds
                now = time.perf_counter()
                sleep_time = target - now
                if sleep_time > 0:
                    time.sleep(sleep_time)
                if ev.on:
                    fl.noteon(0, ev.pitch, settings.midi_velocity)
                else:
                    fl.noteoff(0, ev.pitch)

            # Ausklang
            time.sleep(max(0.0, settings.fadeout_seconds))

        except KeyboardInterrupt:
            print("Abbruch per Strg+C während der Audioausgabe.")
        finally:
            try:
                if fl is not None:
                    fl.delete()
            except Exception:
                pass
