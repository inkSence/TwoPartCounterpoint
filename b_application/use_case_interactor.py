#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

"""Use-Case-Interactor (Application-Schicht).

Zentrale Fassade für Anwendungsfälle. Aktuell nur der Use Case zur
Kontrapunkt-Generierung, später erweiterbar.
"""

from a_domain.Melodie import Melodie
from .generate_counterpoint_use_case import GenerateCounterpointUseCase
from .build_note_events_use_case import BuildNoteEventsUseCase, NoteEvent


class UseCaseInteractor:
    def __init__(self, generate_uc: GenerateCounterpointUseCase | None = None,
                 sequencer: BuildNoteEventsUseCase | None = None) -> None:
        self.generate_uc = generate_uc or GenerateCounterpointUseCase()
        # Sequencer für Playback-Events zentral in der Application-Schicht
        self.sequencer = sequencer or BuildNoteEventsUseCase()

    # Öffentliche API für Adapter/Controller
    def generate_counterpoint(self, choral: Melodie) -> Melodie:
        return self.generate_uc.execute(choral)

    def build_note_events(self, choral: Melodie, kontrapunkt: Melodie) -> list[NoteEvent]:
        """Erzeugt Note-On/Off-Events aus Choral und Kontrapunkt.

        Die Events werden für die Echtzeit-Wiedergabe verwendet und sind
        unabhängig vom konkreten Playback-Driver.
        """
        return self.sequencer.execute(choral, kontrapunkt)
