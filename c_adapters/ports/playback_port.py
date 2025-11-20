#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations


from abc import ABC, abstractmethod
from b_application.build_note_events_use_case import NoteEvent


class CounterpointPlaybackPort(ABC):
    """Abstrakte Schnittstelle für das Abspielen eines zweistimmigen Kontrapunkts."""

    @abstractmethod
    def play(self, events : list[NoteEvent]) -> None:
        """Startet die Wiedergabe entsprechend der Angaben im Request und blockiert,
        bis die Wiedergabe abgeschlossen ist oder abgebrochen wurde.
        """
        raise NotImplementedError
