#-*- coding: utf-8 -*-
from recognizer import Recognizer


class LocationRecognizer(Recognizer):
	"""
	Recognize a location, either by name, ICAO name or abbreviation.
	"""

	def __init__(self, locations):
		super().__init__()
		self.locations = locations

		self.icaos = {}
		self.shorts = {}

		for a in locations:
			if a.icao:
				self.icaos[a.icao.lower()] = a
			if a.shortName:
				self.shorts[a.shortName.lower()] = a

	def recognize(self, s):
		ret = super().recognize(s)

		if ret.token in self.icaos:
			return ret.commit(self.icaos[ret.token])

		if ret.token in self.shorts:
			return ret.commit(self.shorts[ret.token])

		for a in self.locations:
			if ret.token in a.longName.lower():
				return ret.commit(a)

		return None

	def propose(self, s):
		ret = super().recognize(s)
		res = []

		if ret.token in self.icaos:
			return ret.commit(self.icaos[ret.token])

		if ret.token in self.shorts:
			return ret.commit(self.shorts[ret.token])

		for a in self.locations:
			if ret.token in a.longName.lower():
				res.append(a)

		return ret.clone(res)

class Location():
	def __init__(self, key, longName, shortName = None, icao = None):
		super().__init__()

		self.key = key
		self.longName = longName
		self.shortName = shortName
		self.icao = icao

	def __str__(self):
		if self.icao:
			return "%s (%s)" % (self.longName, self.icao)

		return self.longName

demoLocations = [
	Location("1", "Iserlohn-Rheinermark", "rhmk"),
	Location("2", "Iserlohn-Sümmern"),
	Location("3", "Dortmund", "DTM", "EDLW"),
	Location("4", "Meierberg"),
	Location("5", "Altena-Hegenscheid")
]
