#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass


# Basistypen für zukünftige, typsichere Domain-Modelle.

Ticks = int  # Einheit: Achtel = 1 Tick (wie im bestehenden Code)


@dataclass(frozen=True)
class Note:
    pitch: int
    duration: Ticks


@dataclass(frozen=True)
class ContraDecision:
    ok: bool
    pitch: int | None = None
    duration: Ticks | None = None
    retry_position: int | None = None
