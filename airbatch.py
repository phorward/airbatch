# -*- coding: utf-8 -*-
import datetime

class Result:
	def __init__(self, count, token, obj=None):
		self.count = count
		self.token = token
		self.obj = obj

	def commit(self, obj):
		self.obj = obj
		return self


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

		return Result(count, token.lower())

R = Recognizer()

class TimeRecognizer(Recognizer):

	def recognize(self, s):
		ret = super().recognize(s)
		token = ret.token.replace(":", "")

		if len(token) not in [3, 4, 5] or not all([ch.isdigit() for ch in token]):
			return None

		try:
			res = datetime.datetime.now()
			res = res.replace(hour=int(token[:-2]), minute=int(token[-2:]), second=0, microsecond=0)
		except ValueError:
			return None

		ret.obj = res
		return ret

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
		ret = super().recognize(s)

		for aircraft in self.aircrafts:
			if ret.token == aircraft.regNo.lower():
				return ret.commit(aircraft)
			elif aircraft.compNo and ret.token.lower() == aircraft.compNo.lower():
				return ret.commit(aircraft)
			elif "-" in ret.token and "-" in aircraft.regNo:
				if ret.token.replace("-", "") == aircraft.regNo.lower().replace("-", ""):
					return ret.commit(aircraft)
				elif ret.token.split("-", 1)[1] == aircraft.regNo.lower().split("-", 1)[1]:
					return ret.commit(aircraft)
			elif ret.token[-2:] == aircraft.regNo[-2:].lower():
				return ret.commit(aircraft)

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

		return ret.commit(pilot)

pr = PilotRecognizer([
	Pilot("1", "Meier", "Max"),
	Pilot("2", "Schmudel", "Rainer"),
	Pilot("3", "Schielmann", "Peter", nickName="Puddy"),
	Pilot("4", "Meier", "Horst"),
	Pilot("5", "Ruhm", "Hannah"),
	Pilot("6", "Starker", "Philipp")
])


class Airfield():
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

class AirfieldRecognizer(Recognizer):

	def __init__(self, airfields):
		super().__init__()
		self.airfields = airfields

		self.icaos = {}
		self.shorts = {}

		for a in airfields:
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

		for a in self.airfields:
			if ret.token in a.longName.lower():
				return ret.commit(a)

		return None


fr = AirfieldRecognizer([
	Airfield("1", "Iserlohn-Rheinermark", "rhmk"),
	Airfield("2", "Iserlohn-Sümmern"),
	Airfield("3", "Dortmund", "DTM", "EDLW"),
	Airfield("4", "Meierberg"),
	Airfield("5", "Altena-Hegenscheid")
])


txt = """
MK YX meier schmu  1029  1218 rhkm süm
MK YL puddy 1035 1049 rhmk rhmk
D-KYYA meier, horst  ruhm   1145 1213   edlw rhmk
DMRMK meier sta 1150 1230 süm hegenscheid
"""

class Activity():
	def __init__(self, aircraft = None, takeoff = None, touchdown = None,
	                pilot = None, copilot = None, ltakeoff = None, ltouchdown = None):

		self.aircraft = aircraft
		self.takeoff = takeoff
		self.touchdown = touchdown
		self.pilot = pilot
		self.copilot = copilot

		self.ltakeoff = ltakeoff
		self.ltouchdown = ltouchdown

		super().__init__()

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
		allow = [tr, ar, pr, fr]
		for r in allow:
			res = r.recognize(s)
			if res:
				break

		if res is None:
			res = R.recognize(s)
			s = s[res.count:]
			unknown.append(res.token)
			continue

		print("%s = %s" % (res.token, res.obj))
		s = s[res.count:]

	if unknown:
		print("Unknown:", unknown)