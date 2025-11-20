#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

"""Anwendungsfall: Kontrapunkt aus Choral erzeugen (Application-Schicht).

Diese Use-Case-Implementierung kapselt die bisher im Controller liegende
Algorithmik und hängt ausschließlich von der Domänelogik (a_domain) ab.
"""

from a_domain.Melodie import Melodie
from a_domain.HarmonischeStruktur import HarmonischeStruktur
from a_domain.KpRegeln import KpRegeln
from a_domain.Tonleitern import f_dur


class GenerateCounterpointUseCase:
    """Erzeugt zu einem gegebenen Choral einen zweistimmigen Kontrapunkt.

    Eingabe: Melodie (Choral)
    Ausgabe: Melodie (Kontrapunkt)
    Abhängigkeiten: ausschließlich a_domain
    """

    def execute(self, choral: Melodie) -> Melodie:
        kontrapunkt = Melodie([], f_dur)
        harmonie = HarmonischeStruktur(choral, kontrapunkt)
        regeln = KpRegeln(harmonie, choral, kontrapunkt)

        position_im_stueck = 0
        anzahl_zaehlzeiten_1, anzahl_zaehlzeiten_2 = 0, 0

        laenge_des_stuecks = choral.laenge()

        while position_im_stueck < laenge_des_stuecks:
            ton_2 = [True]
            if position_im_stueck == anzahl_zaehlzeiten_1:
                notenNummer_1 = choral.get_aktuelleNotenNummer(position_im_stueck)
                midipitch_1 = choral.notenliste[notenNummer_1][0]
                anzahl_zaehlzeiten_1 = choral.laenge()
                choral.letzte_drei_haben_Extremum(notenNummer_1)

            if position_im_stueck == anzahl_zaehlzeiten_2:
                if position_im_stueck == 0:
                    midipitch_2 = midipitch_1 + 12  # type: ignore[name-defined]
                    notenlaenge = harmonie.notenlaenge_waehlen(
                        harmonie.get_erlaubte_notenlaenge(harmonie.get_taktposition(position_im_stueck))
                    )
                    kontrapunkt.notenliste.append((midipitch_2, notenlaenge))
                    anzahl_zaehlzeiten_2 = notenlaenge
                else:
                    ton_2 = regeln.get_contra(position_im_stueck)
                    midipitch_2 = ton_2[1]
                    notenlaenge = ton_2[2]
                    if ton_2[0] == True:
                        kontrapunkt.notenliste.append((midipitch_2, notenlaenge))
                    else:
                        position_im_stueck = ton_2[3] - 1
                    anzahl_zaehlzeiten_2 = kontrapunkt.laenge()

            if ton_2[0] == True:
                if choral.note_beginnt_gerade(position_im_stueck) == True or kontrapunkt.note_beginnt_gerade(position_im_stueck) == True:
                    interval = harmonie.get_interval(
                        choral.notenliste[choral.get_aktuelleNotenNummer(position_im_stueck)][0],
                        kontrapunkt.notenliste[kontrapunkt.get_aktuelleNotenNummer(position_im_stueck)][0],
                    )
                    harmonie.interval_qualities.append(
                        (position_im_stueck, interval, harmonie.interval_quality(interval))
                    )
            position_im_stueck += 1
        return kontrapunkt
