#-*- coding: utf-8 -*-
#
# Airbatch - Fast flight data recognition framework
# Copyright (C) 2018 by Jan Max Meyer, Phorward Software Technologies
#

from recognizer import Result, Recognizer


class PilotRecognizer(Recognizer):
	"""
	Recognize a pilot, either by lastname, lastname+firstname or nickname.
	"""

	def __init__(self, pilots):
		super().__init__()
		self.pilots = pilots

		self.families = {}
		self.nicks = {}

		for pilot in self.pilots:
			familyName = pilot.lastName.lower()
			if familyName not in self.families:
				self.families[familyName] = []

			self.families[familyName].append(pilot)

			if pilot.nickName:
				nickName = pilot.nickName.lower()
				self.nicks[nickName] = pilot

	def _recognizePilots(self, s):
		ret = super().recognize(s)

		familyName = ret.token
		family = None

		if familyName not in self.families:
			if familyName not in self.nicks:
				for key in sorted(self.families.keys()):
					if key.startswith(familyName):
						family = self.families[key]
						break
			else:
				return ret.commit(self.nicks[familyName])
		else:
			family = self.families[familyName]

		if not family:
			return None

		try:
			ret2 = super().recognize(s[ret.count:])
			firstName = ret2.token
		except:
			firstName = None

		pilot = family[0]
		if len(family) == 1:
			if firstName and pilot.firstName.lower().startswith(firstName):
				return Result(ret.count + ret2.count, s[:ret.count + ret2.count], pilot)

		elif firstName:
			for p in family:
				if p.firstName.lower().startswith(firstName):
					return Result(ret.count + ret2.count, s[:ret.count + ret2.count], p)

		if len(family) == 1:
			return ret.commit(pilot)

		return ret.clone(family)

	def recognize(self, s):
		ret = self._recognizePilots(s)
		if not ret:
			return None

		if isinstance(ret, list):
			return ret[0]

		return ret

	def propose(self, s):
		return self._recognizePilots(s)


class Pilot:
	def __init__(self, key, lastName, firstName, nickName = None):
		super().__init__()

		self.key = key
		self.firstName = firstName
		self.lastName = lastName
		self.nickName = nickName

	def __str__(self):
		return "%s, %s" % (self.lastName, self.firstName)

demoPilots = [
	Pilot("1", "Meier", "Max", nickName="Pille"),
	Pilot("2", "Schmudel", "Rainer"),
	Pilot("3", "Schielmann", "Peter", nickName="Puddy"),
	Pilot("4", "Meier", "Horst"),
	Pilot("5", "Ruhm", "Hannah"),
	Pilot("6", "Starker", "Philipp")
]
