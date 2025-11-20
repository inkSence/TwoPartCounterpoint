#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from a_domain.Melodie import Melodie


@dataclass(frozen=True)
class NoteEvent:
    time_tick: int
    on: bool
    pitch: int


class BuildNoteEventsUseCase:
    """Erzeugt aus zwei Melodien Note-On/Off-Events in Ticks.

    - Ticks: Einheit entspricht der bestehenden Zählzeit (Achtel = 1).
    - Events werden nach Zeit sortiert, bei gleicher Zeit kommen Note-Off vor Note-On,
      um Hänger zu vermeiden.
    """

    def execute(self, choral: Melodie, kontra: Melodie) -> list[NoteEvent]:
        events: list[NoteEvent] = []

        # Stimme 1
        t = 0
        for pitch, duration in choral.notenliste:
            events.append(NoteEvent(t, True, pitch))
            events.append(NoteEvent(t + duration, False, pitch))
            t += duration

        # Stimme 2
        t = 0
        for pitch, duration in kontra.notenliste:
            events.append(NoteEvent(t, True, pitch))
            events.append(NoteEvent(t + duration, False, pitch))
            t += duration

        # Sortierung: Zeit, dann Off vor On
        events.sort(key=lambda e: (e.time_tick, 0 if not e.on else 1))
        return events
