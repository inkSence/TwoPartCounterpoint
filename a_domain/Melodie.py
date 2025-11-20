#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .Tonleitern import c_dur, f_dur


class Melodie(object):
    def __init__(self, notenliste, tonart):
        self.notenliste = notenliste
        self.tonart = tonart
        self.neuesLokalesExtremum = ()
        self.letztesLokalesExtremum = ()

    def laenge(self):
        laenge_der_melodie = 0
        for i in range(0, len(self.notenliste), 1):
            laenge_der_melodie += self.notenliste[i][1]
        return laenge_der_melodie

    def get_aktuelleNotenNummer(self, position_im_stueck):
        if self.notenliste == []:
            return 0  # Auch wenn die Liste noch leer ist, kann die Melodie eine Position haben.
        else:
            anzahl_zaehlzeiten = 0
            for i in range(0, len(self.notenliste), 1):
                anzahl_zaehlzeiten += self.notenliste[i][1]
                if anzahl_zaehlzeiten > position_im_stueck:
                    return i
            return len(self.notenliste)

    def anzahl_zaehlzeiten_bis_zur_note(self, notennummer):
        if self.notenliste == []:
            return 0
        elif len(self.notenliste) <= notennummer:
            print("anzahl_zaehlzeiten_bis_zur_note hat eine zu große notennummer.")
            print("Durch die notennummer kann kein Element der notenliste erreicht werden.")
        else:
            anzahl_zaehlzeiten = 0
            for i in range(0, notennummer, 1):
                anzahl_zaehlzeiten += self.notenliste[i][1]
            return anzahl_zaehlzeiten

    def aktuelleNote(self, position_im_stueck):
        nummer = self.get_aktuelleNotenNummer(position_im_stueck)
        return self.notenliste[nummer]

    def getMidipitch(self, position_im_stueck):
        note = self.aktuelleNote(position_im_stueck)
        return note[0]

    def letzte_drei_haben_Extremum(self, nummer):
        if nummer == 0:
            self.letztesLokalesExtremum = ("Anfangston", self.notenliste[0][0])
        elif nummer == 1:
            newMidipitch = self.notenliste[nummer][0]
            lastMidipitch = self.notenliste[nummer - 1][0]
            if (lastMidipitch < newMidipitch):
                self.neuesLokalesExtremum = "lokalesMinimum", lastMidipitch
                return True
            elif (lastMidipitch > newMidipitch):
                self.neuesLokalesExtremum = "lokalesMaximum", lastMidipitch
            else:
                self.neuesLokalesExtremum = "Anfangston", lastMidipitch
        if nummer > 1:
            newMidipitch = self.notenliste[nummer][0]
            lastMidipitch = self.notenliste[nummer - 1][0]
            beforeLastMidipitch = self.notenliste[nummer - 2][0]
            if (lastMidipitch < beforeLastMidipitch) and (lastMidipitch < newMidipitch):
                self.letztesLokalesExtremum = self.neuesLokalesExtremum
                self.neuesLokalesExtremum = "lokalesMinimum", lastMidipitch
                return True
            elif (lastMidipitch > beforeLastMidipitch) and (lastMidipitch > newMidipitch):
                self.letztesLokalesExtremum = self.neuesLokalesExtremum
                self.neuesLokalesExtremum = "lokalesMaximum", lastMidipitch
                return True
            else:
                return False

    def mi_contra_fa_melodisch(self, position_im_stueck, regeln_obj):
        nummer = self.get_aktuelleNotenNummer(position_im_stueck)
        self.letzte_drei_haben_Extremum(nummer)
        try:
            return regeln_obj.mi_contra_fa(self.letztesLokalesExtremum[1], self.neuesLokalesExtremum[1])
        except Exception:
            return False

    def una_nota_supra_la(self, extremum_tuple, lastMidipitch):
        (string, lokalesExtremum) = extremum_tuple
        if lokalesExtremum == lastMidipitch:
            if lastMidipitch == c_dur[7] and string == "lokalesMaximum":
                lastMidipitch = f_dur[7]  # semper est canenda fa
                return True, lastMidipitch
            else:
                return False

    def note_beginnt_gerade(self, position_im_stueck):
        notennummer = self.get_aktuelleNotenNummer(position_im_stueck)
        anzahl_zaehlzeiten = self.anzahl_zaehlzeiten_bis_zur_note(notennummer)
        if anzahl_zaehlzeiten == position_im_stueck:
            return True
        else:
            return False
