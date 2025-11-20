#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

"""
Zentrale Fassade für Anwendungsfälle.
"""

from a_domain.Melodie import Melodie
from a_domain.Tonleitern import f_dur
from .generate_counterpoint_use_case import GenerateCounterpointUseCase
from .build_note_events_use_case import BuildNoteEventsUseCase, NoteEvent


class UseCaseInteractor:
    def __init__(self, generate_uc: GenerateCounterpointUseCase,
                 sequencer: BuildNoteEventsUseCase) -> None:
        self.generate_uc = generate_uc
        self.sequencer = sequencer

    def generate_counterpoint(self, choral: Melodie) -> Melodie:
        return self.generate_uc.execute(choral)

    def build_choral(self, choral: list[tuple[int, int]]):
        return Melodie(choral, f_dur)

    def build_note_events(self, choral: Melodie, kontrapunkt: Melodie) -> list[NoteEvent]:
        return self.sequencer.execute(choral, kontrapunkt)
