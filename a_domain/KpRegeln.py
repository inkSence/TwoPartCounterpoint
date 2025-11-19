#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from random import randint
from .Tonleitern import c_dur, f_dur


class KpRegeln(object):
    def __init__(self, harmonie, choral, kontrapunkt):
        self.harmonie = harmonie
        self.choral = choral
        self.kontrapunkt = kontrapunkt

    def mi_contra_fa(self, note_1, note_2):
        if (
            (note_1 == f_dur[3] and note_2 == f_dur[7])
            or (note_1 == f_dur[7] and note_2 == f_dur[3])
            or (note_1 == c_dur[4] and note_2 == c_dur[7])
            or (note_1 == c_dur[7] and note_2 == c_dur[4])
            or (note_1 == f_dur[10] and note_2 == f_dur[7])
            or (note_1 == f_dur[7] and note_2 == f_dur[10])
            or (note_1 == c_dur[11] and note_2 == c_dur[7])
            or (note_1 == c_dur[7] and note_2 == c_dur[11])
            or (note_1 == c_dur[7] and note_2 == f_dur[7])
            or (note_1 == f_dur[7] and note_2 == c_dur[7])
        ):
            return True  # diabolus in musica
        else:
            return False

    def halbe_Pausen_oder_groesser_erlaubt(self, taktposition):
        if taktposition == 0 or taktposition == 4:
            return True
        else:
            return False

    def melodie_intervall_erlaubt(self, intervall):  # dies funktionert auch für negative Intervalle
        moegliche_intervalle = [0, 1, 2, 3, 4, 5, 7, 12, 8]
        if intervall < 0:
            erlaubte_intervalle = moegliche_intervalle[:-1]
        else:
            erlaubte_intervalle = moegliche_intervalle[:]
        if abs(intervall) in erlaubte_intervalle:
            return True
        else:
            return False

    def dissonanz_moeglich(self, last_interval_quality, position_im_stueck):
        # Dissonanz möglich, wenn genau eine Stimme liegt und das letzte Intervall konsonant war.
        stimme = self.harmonie.genau_ein_ton_liegt(position_im_stueck)
        return (stimme in (1, 2)) and (last_interval_quality == "Konsonanz")

    def welche_stimme_darf_dissonieren(self, last_interval_quality, position_im_stueck):
        if self.dissonanz_moeglich(last_interval_quality, position_im_stueck):
            stimme = self.harmonie.genau_ein_ton_liegt(position_im_stueck)
            if stimme == 1:
                return "2"
            elif stimme == 2:
                return "1"
        return None

    def schrittweises_verlassen(self, midipitch_1, midipitch_2):
        # Diese Funktion wird nur ausgeführt, nachdem geklärt ist, DASS überhaupt
        # schrittweise verlassen werden muss (Dissonanz, Exzerpt S. 3).
        # Es wird immer abwärts aufgelöst, deshalb ist die Richtung nicht zufällig (Exzerpt S. 4)
        # Jedoch kann sich die Stimme ausgesucht werden, die (abwärts) auflöst, deshalb hier der Zufall.
        stimme = randint(1, 2)
        if stimme == 1:
            for i in range(0, len(f_dur), 1):
                if f_dur[i] == midipitch_1:
                    print(str(f_dur[i - 1]), str(f_dur[i]))
                    midipitch_1 = f_dur[i - 1]
        elif stimme == 2:
            for i in range(0, len(f_dur), 1):
                if f_dur[i] == midipitch_2:
                    print(str(f_dur[i - 1]), str(f_dur[i]))
                    midipitch_2 = f_dur[i - 1]
        return midipitch_1, midipitch_2

    def get_contra(self, position_im_stueck):
        # Herzfunktion get_contra sucht nach einem Ton, der im Kontrapunkt passt.
        midipitch_1 = self.choral.aktuelleNote(position_im_stueck)[0]
        lastMidipitch_2 = self.kontrapunkt.notenliste[-1][0]
        testlist = f_dur[:]
        contra = 0
        for i in range(1, len(testlist), 1):
            test_note = testlist.pop(randint(1, len(testlist) - 1))
            intervalQuality = self.harmonie.interval_quality(
                self.harmonie.get_interval(midipitch_1, test_note)
            )
            if (
                (self.mi_contra_fa(midipitch_1, test_note) == False)
                and (self.melodie_intervall_erlaubt(test_note - lastMidipitch_2) == True)
                and (intervalQuality == "Konsonanz")
            ):
                if (
                    self.harmonie.interval_qualities[-1][2] == "Konsonanz"
                    or (
                        self.harmonie.interval_qualities[-1][2] == "Dissonanz"
                        and (
                            lastMidipitch_2 - test_note == 1
                            or lastMidipitch_2 - test_note == 2
                        )
                    )
                ):
                    if len(self.harmonie.interval_qualities) > 1:
                        # Wenn der letzte Ton Konsonanz bildete, oder zumindest der neue Ton nicht aus der Dissonanz herausspringt
                        if (
                            (
                                (self.harmonie.interval_qualities[-2][1] == 0)
                                and (self.harmonie.interval_qualities[-1][1] == 0)
                            )
                            == False
                        ) and (
                            (
                                (self.harmonie.interval_qualities[-2][1] == 7)
                                and (self.harmonie.interval_qualities[-1][1] == 7)
                            )
                            == False
                        ) and (
                            (
                                (self.harmonie.interval_qualities[-2][1] == 12)
                                and (self.harmonie.interval_qualities[-1][1] == 12)
                            )
                            == False
                        ):
                            # Verbotene Parallelführungen vermeiden
                            contra = test_note
                            break
                    else:
                        contra = test_note
                        break

        notenlaenge = self.harmonie.notenlaenge_waehlen(
            self.harmonie.get_erlaubte_notenlaenge(
                self.harmonie.get_taktposition(position_im_stueck)
            )
        )
        if (
            position_im_stueck
            >= self.choral.laenge()
            - self.choral.notenliste[-2][1]
            - self.choral.notenliste[-1][1]
        ):
            # Gestaltung der vorletzten Note
            if (self.choral.notenliste[-2][0] - self.choral.notenliste[-1][0]) == 2:
                vorletztes_intervall = 11
            elif (self.choral.notenliste[-2][0] - self.choral.notenliste[1][0]) == -1:
                vorletztes_intervall = 14
            else:
                print("Der Choral endet weder mit einer Tenor- noch mit einer Sopran-Klausel.")
            contra = self.choral.notenliste[-1][0] + vorletztes_intervall
            notenlaenge = (
                self.choral.laenge() - self.choral.notenliste[-1][1] - position_im_stueck
            )
        if position_im_stueck == self.choral.laenge() - self.choral.notenliste[-1][1]:
            # Gestaltung der letzten Note
            contra = midipitch_1 + 12
            notenlaenge = self.choral.notenliste[-1][1]
        if contra == 0:
            print("get_contra konnte keine mögliche Note finden")
            subtract = self.kontrapunkt.notenliste.pop(-1)[1]
            # löscht gleichzeitig das letzte Element & ergibt, wann position_im_stueck nochmal ansetzen muss.
            if len(self.harmonie.interval_qualities) > 0:
                self.harmonie.interval_qualities.pop(-1)
            position_im_stueck = position_im_stueck - subtract
            return False, contra, notenlaenge, position_im_stueck
        else:
            return True, contra, notenlaenge, position_im_stueck
