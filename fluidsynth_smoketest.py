#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fluidsynth Audio Smoketest für PipeWire/Pulse

Ziel: Beim Ausführen soll ein kurzer Ton hörbar sein. Primär wird der
FluidSynth-Audiotreiber "pipewire" verwendet, mit Fallback auf
"pulseaudio". Optional können SoundFont und Treiber per Argument gewählt
werden.

Aufrufbeispiele:
  python3 fluidsynth_smoketest.py
  python3 fluidsynth_smoketest.py --driver pulseaudio
  python3 fluidsynth_smoketest.py --sf2 d_frameworks_drivers/midiFluidSynth/soundFonts/1276-soft_tenor_sax.sf2

Hinweis: Dieser Test verwendet FluidSynths eigenen Audioausgang;
PyAudio/PortAudio wird hier bewusst nicht genutzt.

SoundFonts: Es wird ausschließlich im paketlokalen Ordner
"d_frameworks_drivers/midiFluidSynth/soundFonts/" gesucht (es sei denn,
ein Pfad wird explizit via --sf2 übergeben).
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

try:
    import fluidsynth
except Exception as e:
    print("Fehler: pyfluidsynth/fluidsynth konnte nicht importiert werden:", e)
    sys.exit(1)


def find_soundfont(explicit: str | None = None) -> str:
    """Finde eine brauchbare SF2-Datei.

    Priorität:
    1) explizit per Argument --sf2
    2) Paketlokale SoundFonts unter d_frameworks_drivers/midiFluidSynth/soundFonts
    """
    if explicit:
        p = Path(explicit)
        if p.exists():
            return str(p)
        raise FileNotFoundError(f"Angegebenes --sf2 nicht gefunden: {explicit}")
    pkg = Path(__file__).parent / "d_frameworks_drivers/midiFluidSynth/soundFonts"
    candidates = [
        pkg / "1276-soft_tenor_sax.sf2",
        pkg / "alto_sax_2.sf2",
        pkg / "example.sf2",
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    raise FileNotFoundError(
        "Keine SoundFont-Datei gefunden. Lege eine .sf2 in d_frameworks_drivers/midiFluidSynth/soundFonts/"
    )


def play_test_tone(driver: str = "pipewire", sf2_path: str | None = None, duration: float = 1.5) -> None:
    """Spielt einen kurzen A4-Ton (MIDI 69) über FluidSynth direkt aus.

    Wir versuchen zuerst den angegebenen Treiber; bei Fehler versuchen wir
    automatisch noch einen sinnvollen Fallback.
    """
    sf2 = find_soundfont(sf2_path)
    tried = []
    last_err = None
    for drv in [driver, "pulseaudio"]:
        if drv in tried:
            continue
        tried.append(drv)
        try:
            print(f"Starte FluidSynth mit Treiber='{drv}' und SF2='{sf2}' ...")
            fs = fluidsynth.Synth(samplerate=44100.0, gain=0.8)
            sfid = fs.sfload(sf2)
            # GM Piano als sicheres Preset
            fs.program_select(0, sfid, 0, 0)
            # Startet den Audioausgang (PipeWire/Pulse)
            fs.start(driver=drv)
            # Lautstärke vorsorglich hochziehen
            try:
                fs.cc(0, 7, 127)  # Volume
                fs.cc(0, 11, 127) # Expression
            except Exception:
                pass
            midi_note = 69  # A4 / Kammerton
            velocity = 100
            fs.noteon(0, midi_note, velocity)
            time.sleep(max(0.1, duration))
            fs.noteoff(0, midi_note)
            time.sleep(0.25)
            fs.delete()
            print("OK: Testton wurde ausgegeben.")
            return
        except KeyboardInterrupt:
            try:
                fs.delete()  # type: ignore[name-defined]
            except Exception:
                pass
            print("Abbruch per Strg+C. Ressourcen freigegeben.")
            raise
        except Exception as e:
            last_err = e
            try:
                # Aufräumen, falls start()/noteon teilweise erfolgreich war
                fs.delete()  # type: ignore[name-defined]
            except Exception:
                pass
            print(f"Warnung: Treiber '{drv}' fehlgeschlagen: {e}")

    # Wenn wir hier ankommen, haben beide Versuche nicht geklappt
    raise RuntimeError(
        f"FluidSynth konnte keinen Audio-Treiber starten. Letzter Fehler: {last_err}"
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="FluidSynth PipeWire/Pulse Smoketest")
    p.add_argument(
        "--driver",
        default="pipewire",
        choices=["pipewire", "pulseaudio", "alsa", "jack", "sdl2", "portaudio"],
        help="Bevorzugter FluidSynth-Audiotreiber (Default: pipewire)",
    )
    p.add_argument("--sf2", help="Pfad zur SoundFont-Datei (.sf2)")
    p.add_argument("--seconds", type=float, default=1.5, help="Dauer des Testtons in Sekunden")
    args = p.parse_args(argv)

    try:
        play_test_tone(driver=args.driver, sf2_path=args.sf2, duration=args.seconds)
        return 0
    except KeyboardInterrupt:
        return 130
    except Exception as e:
        print("Fehlschlag:", e)
        print(
            "Hinweis: Prüfe, ob PipeWire/Pulse läuft und ob FluidSynth mit dem jeweiligen Treiber gebaut ist.\n"
            "Tipp: 'fluidsynth -a pipewire /usr/share/sounds/sf2/FluidR3_GM.sf2' funktioniert bei dir;\n"
            "verwende ggf. denselben SoundFont-Pfad mit --sf2."
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
