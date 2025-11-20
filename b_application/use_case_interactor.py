#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

"""Use-Case-Interactor (Application-Schicht).

Zentrale Fassade für Anwendungsfälle. Aktuell nur der Use Case zur
Kontrapunkt-Generierung, später erweiterbar.
"""

from a_domain.Melodie import Melodie
from a_domain.Tonleitern import f_dur
from .generate_counterpoint_use_case import GenerateCounterpointUseCase
from .build_note_events_use_case import BuildNoteEventsUseCase, NoteEvent


class UseCaseInteractor:
    def __init__(self, generate_uc: GenerateCounterpointUseCase,
                 sequencer: BuildNoteEventsUseCase) -> None:
        """Fassade über Anwendungsfälle.

        Alle Abhängigkeiten werden von außen injiziert (Composition Root: Main).
        Es werden keine Default-Instanzen erstellt.
        """
        self.generate_uc = generate_uc
        # Sequencer für Playback-Events zentral in der Application-Schicht
        self.sequencer = sequencer

    # Öffentliche API für Adapter/Controller
    def generate_counterpoint(self, choral: Melodie) -> Melodie:
        return self.generate_uc.execute(choral)

    def build_choral(self, choral: list[tuple[int, int]]):
        return Melodie(choral, f_dur)

    def build_note_events(self, choral: Melodie, kontrapunkt: Melodie) -> list[NoteEvent]:
        """Erzeugt Note-On/Off-Events aus Choral und Kontrapunkt.

        Die Events werden für die Echtzeit-Wiedergabe verwendet und sind
        unabhängig vom konkreten Playback-Driver.
        """
        return self.sequencer.execute(choral, kontrapunkt)
