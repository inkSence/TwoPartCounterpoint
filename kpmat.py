#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import numpy
import fluidsynth
from random import randint
import copy
from pathlib import Path


def numpy_to_bytes(samples):
    """Convert FluidSynth/Numpy samples to PCM16 bytes for PyAudio under Python 3.
    Tries the legacy fluidsynth.raw_audio_string first, then falls back to manual conversion.
    """
    try:
        return fluidsynth.raw_audio_string(samples)
    except Exception:
        pass
    s = numpy.asarray(samples, dtype=numpy.float32)
    s = numpy.clip(s, -1.0, 1.0)
    return (s * 32767).astype(numpy.int16).tobytes()

#Die folgende Liste umfasst die kleine und die eingestrichene Oktave. Genauer gesagt, sind es die Grenzen 
#für einen Tenor mit großem Umfang. (vgl. T. Daniel S.35)
c_dur = [0, 48, 50, 52, 53, 55, 57, 59, 60, 62, 64, 65, 67, 69] 
#In der folgenden Liste ist das h erniedrigt.
f_dur = [0, 48, 50, 52, 53, 55, 57, 58, 60, 62, 64, 65, 67, 69] 

#Choral "Wenn wir in höchsten Noten sein" in "Listenschreibweise", 
#d.h. die erste Zahl im Tupel ist die Position in der Liste der Tonart:
#wWIHNS_1 = [(4,4),(4,2),(5,2),(6,4),(5,2),(7,4),(6,2),(5,4),(4,4),(6,4),(7,2),(6,2),(5,2),(4,2),
#(3,4),(4,4),(5,8),(8,4),(7,2),(6,2),(5,4),(6,4),(4,4),(2,4),(1,4),(6,4),(7,2),(6,2),(5,2),
#(4,2),(6,4),(5,4),(4,8)] 
#derselbe Choral, allerdings mit Midi-Darstellung, geht so:
wWIHNS_1 = [(53,4),(53,2),(55,2),(57,4),(55,2),(58,4),(57,2),(55,4),(53,4),(57,4),(58,2),(57,2),(55,2),(53,2), 
(52,4),(53,4),(55,8),(60,4),(58,2),(57,2),(55,4),(57,4),(53,4),(50,4),(48,4),(57,4),(58,2),(57,2),(55,2),
(53,2),(57,4),(55,4),(53, 8)]
#ein Kontrapunkt zum Choral-Anfang:
#wWIHNS_2 = [(11,4),(9,2),(9,2),(8,4),(9,2),(9,3),(10,1),(11,4),(10,2),(11,4)] 

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
			return 0 #Auch wenn die Liste noch leer ist, kann die Melodie eine Position haben.
		else:
			anzahl_zaehlzeiten = 0
			for i in range(0, len(self.notenliste), 1):
				anzahl_zaehlzeiten += self.notenliste[i][1]
				if anzahl_zaehlzeiten > position_im_stueck:
					return i
			return len(self.notenliste)
			print("Offensichtlich ist position_im_stueck >= anzahl zählzeiten.")
			print("Damit liegt die Position außerhalb der Notenliste.")
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
				lastMidipitch = f_dur[7] #semper est canenda fa
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
class HarmonischeStruktur(object):
	def __init__(self):
		self.interval_qualities = []
	def get_interval(self, note1, note2):
		#hier fehlen u.U. später Begriffe wie "vermindert" & "übermäßig"
		interval = abs(note2 - note1)
		if interval == 0:
			i_name = "Prime"
		elif interval == 1:
			i_name = "kl.Sekunde"
		elif interval == 2:
			i_name = "gr.Sekunde"
		elif interval == 3:
			i_name = "kl.Terz"
		elif interval == 4:
			i_name = "gr.Terz"
		elif interval == 5:
			i_name = "Quarte"
		elif interval == 6:
			i_name = "Tritonus"
		elif interval == 7:
			i_name = "Quinte"
		elif interval == 8:
			i_name = "kl.Sexte"
		elif interval == 9:
			i_name = "gr.Sexte"
		elif interval == 10:
			i_name = "kl.Septime"
		elif interval == 11:
			i_name = "gr.Septime"
		elif interval == 12:
			i_name = "Oktave"
		else:
			i_name = "mehr als Oktave"
		return interval#, i_name
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
		"""sähen die 8 Viertel in einem Takt aus wie folgt, dann:
		o o o o o o o o
		0 | | | 4 | | |
		  | | |   | | |
		  | +-|---|-+-|--- leichte Halbeposition
		  |   |   |   |
		  +---+---+---+--- leichte Viertelposition
		"""
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
		#d.h.:[Viertel, Halbe, punkt.Halbe, Ganze, punkt.Ganze, Brevis]
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
		#schaut, ob in genau einer Stimme der Ton gerade NICHT beginnt => also liegt der Ton in dieser Stimme.
		beginn1 = choral.note_beginnt_gerade(position_im_stueck)
		beginn2 = kontrapunkt.note_beginnt_gerade(position_im_stueck)
		if beginn1 == False and beginn2 == True:
			return 1 #1.Stimme hat liegenden Ton
		elif beginn1 == True and beginn2 == False:
			return 2 #2.Stimme hat liegenden Ton
		elif beginn1 == False and beginn2 == False:
			return "b" #beide Stimmen haben liegenden Ton
		elif beginn1 == True and beginn2 == True:
			return "k" #keine Stimme hat liegenden Ton, beide Töne beginnen gerade.
		else:
			print("error in genau_ein_ton_liegt")
	def wie_lange_liegt_liegender_ton(self, position_im_stueck, anzahl_zaehlzeiten1, anzahl_zaehlzeiten2):
		#Vielleicht braucht man diese Funktion gar nicht. 
		#Jede Tonlänge ist zulässig, um aus der Dissonanz wieder heraus zu gehen.
		#Diese Funktion sei nur ausgeführt, wenn überhaupt ein liegender Ton da ist.
		stimme = self.genau_ein_ton_liegt(position_im_stueck)
		differenz1 = anzahl_zaehlzeiten1 - position_im_stueck
		differenz2 = anzahl_zaehlzeiten2 - position_im_stueck
		if stimme == 1:
			return differenz1
		elif stimme == 2:
			return differenz2

class KpRegeln(object):
	def __init__(self):
		pass
	def mi_contra_fa(self, note_1, note_2):
		if ((note_1 == f_dur[3] and note_2 == f_dur[7]) or (note_1 == f_dur[7] and note_2 == f_dur[3]) or
		(note_1 == c_dur[4] and note_2 == c_dur[7]) or (note_1 == c_dur[7] and note_2 == c_dur[4]) or
		#dann noch mal dasselbe mit dem e eine Oktave höher:
		(note_1 == f_dur[10] and note_2 == f_dur[7]) or (note_1 == f_dur[7] and note_2 == f_dur[10]) or 
		#dann noch mal dasselbe mit dem f eine Oktave höher
		(note_1 == c_dur[11] and note_2 == c_dur[7]) or (note_1 == c_dur[7] and note_2 == c_dur[11]) or 
		(note_1 == c_dur[7] and note_2 == f_dur[7]) or (note_1 == f_dur[7] and note_2 == c_dur[7])):
			return True #diabolus in musica
		else:
			return False
	def halbe_Pausen_oder_groesser_erlaubt(self, taktposition):
		if taktposition == 0 or taktposition == 4:
			return True
		else:
			return False
	def melodie_intervall_erlaubt(self, intervall):#dies funktionert auch für negative Intervalle
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
		# In dieser vereinfachten Fassung ist Dissonanz dann möglich,
		# wenn genau eine Stimme liegt und das letzte Intervall konsonant war.
		stimme = harmonie.genau_ein_ton_liegt(position_im_stueck)
		return (stimme in (1, 2)) and (last_interval_quality == "Konsonanz")
	def welche_stimme_darf_dissonieren(self, last_interval_quality, position_im_stueck):
		if self.dissonanz_moeglich(last_interval_quality, position_im_stueck):
			stimme = harmonie.genau_ein_ton_liegt(position_im_stueck)
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
	"""
	def VorbereitungDissonanzAufloesung(self, last_interval_quality, midipitch_1, midipitch_2):
		#Das Konzept "Vorbereitung, Dissonanz, Auflösung" habe ich von Andreas übernommen. 
		#In dieser Funktion sind die Vorbereitung und die Dissonanz schon geschehen. 
		#Nur die Auflösung, also das schrittweise Verlassen muss noch angewiesen werden.
		if last_interval_quality == "Dissonanz":
			midipitch_1, midipitch_2 = schrittweises_verlassen(midipitch_1, midipitch_2)
		else:
			print "last_interval_quality in VorbereitungDissonanzAuflösung ist keine Dissonanz."
		return midipitch_1, midipitch_2
	"""
	def get_contra(self, position_im_stueck):
		#Herzfunktion get_contra sucht nach einem Ton, der im Kontrapunkt passt.
		midipitch_1 = choral.aktuelleNote(position_im_stueck)[0]
		lastMidipitch_2 = kontrapunkt.notenliste[-1][0]
		testlist = f_dur[:]
		contra = 0
		for i in range(1, len(testlist), 1):
			test_note = testlist.pop(randint(1, len(testlist) - 1))
			intervalQuality = harmonie.interval_quality(harmonie.get_interval(midipitch_1, test_note))	
			if (self.mi_contra_fa(midipitch_1, test_note) == False 
			and self.melodie_intervall_erlaubt(test_note - lastMidipitch_2) == True
			and intervalQuality == "Konsonanz"):
				if(harmonie.interval_qualities[-1][2] == "Konsonanz"
				or (harmonie.interval_qualities[-1][2] == "Dissonanz"
				and (lastMidipitch_2 - test_note == 1
				or lastMidipitch_2 - test_note == 2))):
					if len(harmonie.interval_qualities) > 1:
						#Wenn der letzte Ton Konsonanz bildete, oder zumindest der neue Ton nicht aus der Dissonanz herausspringt, wird dieser Block ausgeführt.
						if (((harmonie.interval_qualities[-2][1] == 0 and harmonie.interval_qualities[-1][1] == 0) == False)
						and ((harmonie.interval_qualities[-2][1] == 7 and harmonie.interval_qualities[-1][1] == 7) == False)
						and ((harmonie.interval_qualities[-2][1] == 12 and harmonie.interval_qualities[-1][1] == 12) == False)):
							#Wenn die Parallelführungs-Verbote eingehalten werden, wird dieser Block ausgeführt.

							""" Dieser if-Ausdruck gewährleistet, dass falls die 1. Stimme "zwischenzeitlich" dissoniert hat, 
	der Schritt der 2. Simme mit der ausgewählten Note eine Sekunde abwärts geht. Ob die Sekunde groß oder klein ist, 
	ist abhängig von der absoluten Höhe des letzten Tons und hier egal. - Das kann nur ein Provisorium sein, 
	denn es könnte durch die Bewegung der 1. Stimme z. B. mi_contra_fa verletzt werden, 
	oder bei einem besonders langen Ton in der 2. Stimme die 1. Stimme aus einer Dissonanz springen. 
	Mit anderen Worten: Es liegt ein besonderes Augenmerk auf der zweiten, der veränderlichen Stimme.""" 
							contra = test_note
							break
					else:
						contra = test_note
						break
		notenlaenge = harmonie.notenlaenge_waehlen(harmonie.get_erlaubte_notenlaenge(
			harmonie.get_taktposition(position_im_stueck)))		
		if position_im_stueck >= choral.laenge() - choral.notenliste[-2][1] - choral.notenliste[-1][1]:
			#Das hier ist die Gestaltung der vorletzten Note
			if (choral.notenliste[-2][0] - choral.notenliste[-1][0]) == 2:
				vorletztes_intervall = 11
			elif (choral.notenliste[-2][0] - choral.notenliste[1][0]) == -1:
				vorletztes_intervall = 14
			else:
				print("Der Choral endet weder mit einer Tenor- noch mit einer Sopran-Klausel.")
			contra = choral.notenliste[-1][0] + vorletztes_intervall
			notenlaenge = choral.laenge() - choral.notenliste[-1][1] - position_im_stueck
		if position_im_stueck == choral.laenge() - choral.notenliste[-1][1]:
			#Das hier ist die Gestaltung der letzten Note.
			contra = midipitch_1 + 12
			notenlaenge = choral.notenliste[-1][1]
		if contra == 0:
			print("get_contra konnte keine mögliche Note finden")
			subtract = kontrapunkt.notenliste.pop(-1)[1]
			#löscht gleichzeitig das letzte Element & ergibt, wann position_im_stueck nochmal ansetzen muss.
			if len(harmonie.interval_qualities) > 0:
				harmonie.interval_qualities.pop(-1)
			position_im_stueck = position_im_stueck - subtract
			return False, contra, notenlaenge, position_im_stueck
		else:
			return True, contra, notenlaenge, position_im_stueck


position_im_stueck = 0
anzahl_zaehlzeiten_1, anzahl_zaehlzeiten_2 = 0, 0

regeln = KpRegeln()
choral = Melodie(wWIHNS_1, f_dur)
kontrapunkt = Melodie([], f_dur)
harmonie = HarmonischeStruktur()

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
			midipitch_2 = midipitch_1 + 12
			notenlaenge = harmonie.notenlaenge_waehlen(harmonie.get_erlaubte_notenlaenge(
					harmonie.get_taktposition(position_im_stueck)))
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
		"""notenNummer_2 = kontrapunkt.get_aktuelleNotenNummer(position_im_stueck)
		if kontrapunkt.letzte_drei_haben_Extremum(notenNummer_2) == True:
			if regeln.mi_contra_fa(kontrapunkt.letztesLokalesExtremum, kontrapunkt.neuesLokalesExtremum) == True:
				print "diabolus in musica", kontrapunkt.letztesLokalesExtremum, kontrapunkt.neuesLokalesExtremum
				print "notenNummer_2", notenNummer_2"""
	if ton_2[0] == True:
		if choral.note_beginnt_gerade(position_im_stueck) == True or kontrapunkt.note_beginnt_gerade(position_im_stueck) == True:
			interval = harmonie.get_interval(choral.notenliste[choral.get_aktuelleNotenNummer(position_im_stueck)][0], 
					kontrapunkt.notenliste[kontrapunkt.get_aktuelleNotenNummer(position_im_stueck)][0])
			harmonie.interval_qualities.append((position_im_stueck, interval, harmonie.interval_quality(interval)))
	position_im_stueck += 1



# ########## ab hier wird der Kontrapunkt als body-Teil einer MuseScore-Datei ausgegeben.

base_path = Path(__file__).parent
vorlage_pfad = base_path / "wWIHNS_Choral.mscx"
with open(vorlage_pfad, "r", encoding="utf-8") as vorlage:
    anfang = vorlage.read(5116)
    x = vorlage.read()
ende = x[-3251:]

museScore = ""
for i in range(0, len(kontrapunkt.notenliste), 1):
    laenge = kontrapunkt.notenliste[i][1]
    if laenge == 1:
        dots = ""
        durationType = "eighth"
    elif laenge == 2:
        dots = ""
        durationType = "quarter"
    elif laenge == 3:
        dots = "<dots>1</dots>"
        durationType = "quarter"
    elif laenge == 4:
        dots = ""
        durationType = "half"
    elif laenge == 6:
        dots = "<dots>1</dots>"
        durationType = "half"
    elif laenge == 8:
        dots = ""
        durationType = "whole"
    museScore = (
        museScore
        + "<Chord>"
        + str(dots)
        + "<durationType>"
        + str(durationType)
        + "</durationType><Note><pitch>"
        + str(kontrapunkt.notenliste[i][0])
        + "</pitch></Note></Chord>\n"
    )

out_pfad = base_path / f"wWIHNS_mitKontrapunkt_{time.strftime('%b%d.%H-%M-%S')}.mscx"
with open(out_pfad, "w", encoding="utf-8") as ausgabe:
    ausgabe.write(anfang)
    ausgabe.write(museScore)
    ausgabe.write(ende)

"""
Realtime-Wiedergabe direkt über FluidSynth mit dem PulseAudio-Treiber.
Dies vermeidet ALSA-Warnungen und nutzt unter PipeWire den pulse-Compat-Layer.
"""

position_im_stueck = 0
anzahl_zaehlzeiten_1, anzahl_zaehlzeiten_2 = 0, 0

# Dauer einer "Zählzeit" in Sekunden (bisher wurden 0.25 s Samples erzeugt)
tick_seconds = 0.25

fl = None
midipitch_1 = None
midipitch_2 = None

try:
    # Synth initialisieren und SoundFont laden
    fl = fluidsynth.Synth(samplerate=44100.0, gain=1.0)
    # Standard: lokaler SoundFont, sonst systemweiter FluidR3
    sf_local = (base_path / "soundFonts/1276-soft_tenor_sax.sf2").resolve()
    sf_path = str(sf_local) if sf_local.exists() else \
              "/usr/share/sounds/sf2/FluidR3_GM.sf2"
    sfid = fl.sfload(sf_path)
    # Preset wählen: zuerst Piano (0), wenn nicht vorhanden Tenor Sax (65)
    preset_selected = False
    try:
        fl.program_select(0, sfid, 0, 0)
        preset_selected = True
    except Exception:
        pass
    if not preset_selected:
        try:
            fl.program_select(0, sfid, 0, 65)
            preset_selected = True
        except Exception:
            pass

    # Audioausgabe starten: bevorzugt PulseAudio
    try:
        fl.start(driver="pulseaudio")
        print("FluidSynth: PulseAudio-Treiber aktiv.")
    except Exception as e:
        print("Warnung: PulseAudio konnte nicht gestartet werden (", e, ") – versuche PipeWire …")
        fl.start(driver="pipewire")
        print("FluidSynth: PipeWire-Treiber aktiv.")

    # Sicherheitshalber Lautstärke hochziehen
    try:
        fl.cc(0, 7, 127)   # Volume
        fl.cc(0, 11, 127)  # Expression
    except Exception:
        pass

    # Zeitgesteuerte Echtzeit-Schleife
    t0 = time.perf_counter()
    for i in range(0, laenge_des_stuecks, 1):
        if position_im_stueck == anzahl_zaehlzeiten_1:
            if position_im_stueck != 0 and midipitch_1 is not None:
                fl.noteoff(0, midipitch_1)
            notenNummer_1 = choral.get_aktuelleNotenNummer(position_im_stueck)
            midipitch_1 = choral.notenliste[notenNummer_1][0]
            fl.noteon(0, midipitch_1, 100)
            anzahl_zaehlzeiten_1 += choral.notenliste[notenNummer_1][1]

        if position_im_stueck == anzahl_zaehlzeiten_2:
            if position_im_stueck != 0 and midipitch_2 is not None:
                fl.noteoff(0, midipitch_2)
            notenNummer_2 = kontrapunkt.get_aktuelleNotenNummer(position_im_stueck)
            midipitch_2 = kontrapunkt.notenliste[notenNummer_2][0]
            fl.noteon(0, midipitch_2, 100)
            anzahl_zaehlzeiten_2 += kontrapunkt.notenliste[notenNummer_2][1]

        # Nächsten Tick terminieren und bis dahin schlafen
        position_im_stueck += 1
        next_time = t0 + position_im_stueck * tick_seconds
        now = time.perf_counter()
        sleep_time = next_time - now
        if sleep_time > 0:
            time.sleep(sleep_time)

    # Ausklang
    try:
        if midipitch_1 is not None:
            fl.noteoff(0, midipitch_1)
        if midipitch_2 is not None:
            fl.noteoff(0, midipitch_2)
    except Exception:
        pass
    time.sleep(1.0)

except KeyboardInterrupt:
    print("Abbruch per Strg+C während der Audioausgabe.")
finally:
    try:
        if fl is not None:
            fl.delete()
    except Exception:
        pass




"""
#Die Funktion für die Akzidentien, bleibt zuerst mal raus
def erhoehen_erlaubt(note1, note2): #Akzidentien
	interval = get_interval(note1, note2)
	if interval == "kl.Terz" or interval == "kl.Sexte":
		return True
	else:
		return False
"""
#in einem Durchgang, also auf einer leichtenViertelposition ist mi_contra_fa erlaubt. 

