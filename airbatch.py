# -*- coding: utf-8 -*-
import datetime

class Recognizer:
	def recognize(self, s):
		count = 0
		token = ""

		for ch in s:
			count += 1
			if ch in " ,;\t":
				if token:
					break

				continue

			token += ch

		return count, token.lower()

R = Recognizer()

class TimeRecognizer(Recognizer):

	def recognize(self, s):
		count, token = super().recognize(s)
		token = token.replace(":", "")

		if len(token) not in [3, 4, 5] or not all([ch.isdigit() for ch in token]):
			return None

		try:
			res = datetime.datetime.now()
			res = res.replace(hour=int(token[:-2]), minute=int(token[-2:]), second=0, microsecond=0)
		except ValueError:
			return None

		return count, res

tr = TimeRecognizer()

class Aircraft():
	def __init__(self, key, regNo, type, seats = 1, compNo = None, kind = "glider", launcher = False):
		super().__init__()

		self.key = key
		self.regNo = regNo
		self.compNo = compNo
		self.type = type
		self.seats = seats
		assert kind in ["glider", "microlight", "motorglider"]
		self.kind = kind
		self.launcher = launcher

	def __str__(self):
		return "%s - %s" % (self.regNo, self.type)

class AircraftRecognizer(Recognizer):
	def __init__(self, aircrafts):
		super().__init__()
		self.aircrafts = aircrafts

	def recognize(self, s):
		count, token = super().recognize(s)

		for aircraft in self.aircrafts:
			if token == aircraft.regNo.lower():
				return count, aircraft
			elif aircraft.compNo and token.lower() == aircraft.compNo.lower():
				return count, aircraft
			elif "-" in token and "-" in aircraft.regNo:
				if token.replace("-", "") == aircraft.regNo.lower().replace("-", ""):
					return count, aircraft
				elif token.split("-", 1)[1] == aircraft.regNo.lower().split("-", 1)[1]:
					return count, aircraft
			elif token[-2:] == aircraft.regNo[-2:].lower():
				return count, aircraft

		return None

ar = AircraftRecognizer([
	Aircraft("1", "D-1234", "Libelle", compNo="YL"),
	Aircraft("2", "D-2074", "ASK 13", seats=2),
	Aircraft("3", "D-8984", "ASK 13", seats=2),
	Aircraft("4", "D-5014", "Duo Discus", compNo="YX", seats=2),
	Aircraft("5", "D-KYYA", "Arcus M", compNo="YA", seats=2),
	Aircraft("6", "D-MRMK", "Turbo Savage", seats=2, kind="microlight", launcher=True)
])

class Pilot():
	def __init__(self, key, lastName, firstName, nickName = None):
		super().__init__()

		self.key = key
		self.firstName = firstName
		self.lastName = lastName
		self.nickName = nickName

	def __str__(self):
		return "%s, %s" % (self.lastName, self.firstName)

class PilotRecognizer(Recognizer):

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

	def recognize(self, s):
		count, token = super().recognize(s)

		familyName = token.lower()
		family = None

		if familyName not in self.families:
			if familyName not in self.nicks:
				for key in sorted(self.families.keys()):
					if key.startswith(familyName):
						family = self.families[key]
						break
			else:
				return count, self.nicks[familyName]
		else:
			family = self.families[familyName]

		if not family:
			return None

		try:
			count2, token = super().recognize(s[count:])
			firstName = token.lower()
		except:
			firstName = None

		pilot = family[0]
		if len(family) == 1:
			if firstName and pilot.firstName.lower().startswith(firstName):
				return count + count2, pilot

		elif firstName:
			for p in family:
				if p.firstName.lower().startswith(firstName):
					return count + count2, p

		return count, pilot

pr = PilotRecognizer([
	Pilot("1", "Meier", "Max"),
	Pilot("2", "Schmudel", "Rainer"),
	Pilot("3", "Schielmann", "Peter", nickName="Puddy"),
	Pilot("4", "Meier", "Horst"),
	Pilot("5", "Ruhm", "Hannah"),
	Pilot("6", "Starker", "Philipp")
])

txt = """
MK YX meier schmu  1029  1218
MK YL puddy 1035 1049
D-KYYA meier, horst  ruhm   1145 1213
DMRMK meier sta 1150 1230
"""

print(txt)

idx = 0
for s in txt.split("\n"):
	s = s.strip()
	if not s:
		continue

	unknown = []

	print("--- %d ---" % idx)
	idx += 1

	while s:
		for r in [tr, ar, pr]:
			res = r.recognize(s)
			if res:
				break

		if res is None:
			res = R.recognize(s)
			s = s[res[0]:]
			unknown.append(res[1])
			continue

		print("%s" % res[1])
		s = s[res[0]:]

	if unknown:
		print("Unknown:", unknown)