#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from a_domain.Melodie import Melodie


class ScoreExportPort(ABC):
    """Abstrakte Schnittstelle für den Partitur-Export.

    Adapter/Controller spricht nur gegen diese Schnittstelle und kennt die
    konkrete Implementierung (MuseScore, MusicXML, etc.) nicht.
    """

    @abstractmethod
    def export_melody(self, melody: Melodie) -> Path:
        """Exportiert die übergebene Melodie und liefert den Ausgabepfad zurück."""
        raise NotImplementedError
