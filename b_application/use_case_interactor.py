#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

"""Use-Case-Interactor (Application-Schicht).

Zentrale Fassade für Anwendungsfälle. Aktuell nur der Use Case zur
Kontrapunkt-Generierung, später erweiterbar.
"""

from a_domain.Melodie import Melodie
from .generate_counterpoint_use_case import GenerateCounterpointUseCase


class UseCaseInteractor:
    def __init__(self, generate_uc: GenerateCounterpointUseCase | None = None) -> None:
        self.generate_uc = generate_uc or GenerateCounterpointUseCase()

    # Öffentliche API für Adapter/Controller
    def generate_counterpoint(self, choral: Melodie) -> Melodie:
        return self.generate_uc.execute(choral)
