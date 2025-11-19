#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Grundlegende Tonleitern/Skalen-Konstanten.

Diese Konstanten wurden aus der bisherigen Monolith-Datei extrahiert,
damit Klassen-Module (z. B. Melodie, KpRegeln) sie ohne zyklische
Abhängigkeiten verwenden können.
"""

# Die folgende Liste umfasst die kleine und die eingestrichene Oktave.
# Genauer gesagt, sind es die Grenzen für einen Tenor mit großem Umfang. (vgl. T. Daniel S.35)
c_dur = [0, 48, 50, 52, 53, 55, 57, 59, 60, 62, 64, 65, 67, 69]

# In der folgenden Liste ist das h erniedrigt (entspricht f-Dur Kontext im Projekt).
f_dur = [0, 48, 50, 52, 53, 55, 57, 58, 60, 62, 64, 65, 67, 69]
