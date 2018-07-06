#-*- coding: utf-8 -*-
from recognizer import Recognizer


class AircraftRecognizer(Recognizer):
	"""
	Recognize an aircraft by registration-no, competition-no or short reg no.
	"""

	def __init__(self, aircrafts):
		super().__init__()
		self.aircrafts = aircrafts

	def recognize(self, s):
		ret = super().recognize(s)

		for aircraft in self.aircrafts:
			if ret.token == aircraft.regNo.lower():
				return ret.commit(aircraft)
			elif aircraft.compNo and ret.token.lower() == aircraft.compNo.lower():
				return ret.commit(aircraft)
			elif ret.token.replace("-", "") == aircraft.regNo.lower().replace("-", ""):
				return ret.commit(aircraft)
			#elif ret.token.split("-", 1)[1] == aircraft.regNo.lower().split("-", 1)[1]:
			#	return ret.commit(aircraft)
			elif len(ret.token) == 2 and ret.token == aircraft.regNo[-2:].lower():
				return ret.commit(aircraft)

		return None


class Aircraft():
	def __init__(self, key, regNo, type, seats = 1, compNo = None, kind = "glider", launcher = False, selfstart = False):
		super().__init__()

		self.key = key
		self.regNo = regNo
		self.compNo = compNo
		self.type = type
		self.seats = seats
		assert kind in ["glider", "microlight", "motorglider"]
		self.kind = kind
		self.launcher = launcher
		self.selfstart = selfstart

	def __str__(self):
		return "%s - %s" % (self.regNo, self.type)


demoAircrafts = [
	Aircraft("1", "D-1234", "Libelle", compNo="YL"),
	Aircraft("2", "D-2074", "ASK 13", seats=2),
	Aircraft("3", "D-8984", "ASK 13", seats=2),
	Aircraft("4", "D-5014", "Duo Discus", compNo="YX", seats=2),
	Aircraft("5", "D-KYYA", "Arcus M", compNo="YA", seats=2, selfstart=True),
	Aircraft("6", "D-MRMK", "Turbo Savage", seats=2, kind="microlight", launcher=True)
]
