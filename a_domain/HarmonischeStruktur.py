#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from random import randint


class HarmonischeStruktur(object):
    def __init__(self, choral, kontrapunkt):
        self.interval_qualities = []
        self.choral = choral
        self.kontrapunkt = kontrapunkt

    def get_interval(self, note1, note2):
        # hier fehlen u.U. später Begriffe wie "vermindert" & "übermäßig"
        interval = abs(note2 - note1)
        # i_name wurde nie genutzt, daher Rückgabe nur der Zahl wie im Alt-Code
        return interval

    def interval_quality(self, intervall):
        if intervall > 12:
            intervall = intervall - 12
        if intervall in [0, 7, 12]:
            klang = "perfekteKonsonanz"
        elif intervall in [3, 4, 8, 9]:
            klang = "imperfekteKonsonanz"
        elif intervall in [1, 2, 5, 6, 10, 11]:
            klang = "Dissonanz"
        else:
            print("error: Intervall-Qualität konnte nicht bestimmt werden.", intervall)
            klang = "Dissonanz"
        return klang[-9:]

    def get_taktposition(self, position_im_stueck):
        """Schematische Einteilung eines 8-Viertel-Takts in Positionen."""
        rest = position_im_stueck % 8
        if rest in [0, 4]:
            taktposition = "Ganze"
        elif rest in [2, 6]:
            taktposition = "leichteHalbeposition"
        elif rest in [1, 3, 5, 7]:
            taktposition = "leichteViertelPosition"
        else:
            print("In get_taktposition konnte nichts taktposition zugeordnet werden.")
        return taktposition

    def get_erlaubte_notenlaenge(self, taktposition):
        notenlaengen = [1, 2, 3, 4, 6, 8]
        # d.h.: [Viertel, Halbe, punkt.Halbe, Ganze, punkt.Ganze, Brevis]
        if taktposition == "Ganze":
            erlaubte_notenlaenge = notenlaengen[:]
        elif taktposition == "leichteHalbeposition":
            erlaubte_notenlaenge = notenlaengen[:4]
        elif taktposition == "leichteViertelPosition":
            erlaubte_notenlaenge = notenlaengen[:2]
        else:
            erlaubte_notenlaenge = notenlaengen[:]
            print("error: else-Statement in get_erlaubte_notenlaenge")
        return erlaubte_notenlaenge

    def notenlaenge_waehlen(self, liste):
        return liste[randint(0, len(liste) - 1)]

    def genau_ein_ton_liegt(self, position_im_stueck):
        # schaut, ob in genau einer Stimme der Ton gerade NICHT beginnt
        beginn1 = self.choral.note_beginnt_gerade(position_im_stueck)
        beginn2 = self.kontrapunkt.note_beginnt_gerade(position_im_stueck)
        if beginn1 == False and beginn2 == True:
            return 1  # 1. Stimme hat liegenden Ton
        elif beginn1 == True and beginn2 == False:
            return 2  # 2. Stimme hat liegenden Ton
        elif beginn1 == False and beginn2 == False:
            return "b"  # beide Stimmen haben liegenden Ton
        elif beginn1 == True and beginn2 == True:
            return "k"  # keine Stimme liegt; beide Töne beginnen
        else:
            print("error in genau_ein_ton_liegt")

    def wie_lange_liegt_liegender_ton(self, position_im_stueck, anzahl_zaehlzeiten1, anzahl_zaehlzeiten2):
        # Vielleicht braucht man diese Funktion gar nicht.
        # Jede Tonlänge ist zulässig, um aus der Dissonanz wieder heraus zu gehen.
        # Diese Funktion sei nur ausgeführt, wenn überhaupt ein liegender Ton da ist.
        stimme = self.genau_ein_ton_liegt(position_im_stueck)
        differenz1 = anzahl_zaehlzeiten1 - position_im_stueck
        differenz2 = anzahl_zaehlzeiten2 - position_im_stueck
        if stimme == 1:
            return differenz1
        elif stimme == 2:
            return differenz2
