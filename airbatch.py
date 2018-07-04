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

class DurationRecognizer(Recognizer):

	def recognize(self, s):
		ret = super().recognize(s)

		token = ret.token
		if not token.startswith("+"):
			return None

		token = token[1:]

		if token.count(":") == 1:
			token = token.split(":", 1)
			try:
				mins = int(token[0]) * 60 + int(token[1])
			except ValueError:
				return None
		else:
			try:
				mins = int(token)
			except ValueError:
				return None

		return ret.commit(datetime.timedelta(minutes=mins))

dr = DurationRecognizer()

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
			elif ret.token.replace("-", "") == aircraft.regNo.lower().replace("-", ""):
				return ret.commit(aircraft)
			#elif ret.token.split("-", 1)[1] == aircraft.regNo.lower().split("-", 1)[1]:
			#	return ret.commit(aircraft)
			elif len(ret.token) == 2 and ret.token == aircraft.regNo[-2:].lower():
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
	Pilot("1", "Meier", "Max", nickName="Pille"),
	Pilot("2", "Schmudel", "Rainer"),
	Pilot("3", "Schielmann", "Peter", nickName="Puddy"),
	Pilot("4", "Meier", "Horst"),
	Pilot("5", "Ruhm", "Hannah"),
	Pilot("6", "Starker", "Philipp")
])


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

class LocationRecognizer(Recognizer):

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


defaultLocation = Location("1", "Iserlohn-Rheinermark", "rhmk")

lr = LocationRecognizer([
	defaultLocation,
	Location("2", "Iserlohn-Sümmern"),
	Location("3", "Dortmund", "DTM", "EDLW"),
	Location("4", "Meierberg"),
	Location("5", "Altena-Hegenscheid")
])


txt = """
MK  pille 1029 1035 1218 YX meier schmu  rhkm süm
MK YL puddy 1035 +10 rhmk rhmk
D-KYYA meier, horst  ruhm   1145 1213   edlw rhmk
DMRMK meier sta 1150 1230 süm hegenscheid
"""

txt = "MK YL puddy 1035 +10"

class Activity():
	def __init__(self, aircraft = None, takeoff = None, touchdown = None, duration = None,
					pilot = None, copilot = None, ltakeoff = None, ltouchdown = None,
	                    note = None, link = None):

		self.aircraft = aircraft
		self.takeoff = takeoff
		self.touchdown = touchdown
		self.duration = duration
		self.pilot = pilot
		self.copilot = copilot

		self.ltakeoff = ltakeoff
		self.ltouchdown = ltouchdown

		self.note = note

		self.link = link
		if link and not link.link:
			link.link = self

		super().__init__()

	def setAircraft(self, aircraft):
		assert isinstance(aircraft, Aircraft)

		if not self.aircraft:
			self.aircraft = aircraft
			return True

		return False

	def setPilot(self, pilot):
		assert isinstance(pilot, Pilot)
		assert self.aircraft

		if self.aircraft.seats >= 1 and self.pilot is None:
			self.pilot = pilot
			return True
		elif self.aircraft.seats == 2 and self.copilot is None:
			self.copilot = pilot
			return True

		return False

	def setTime(self, time):
		assert isinstance(time, datetime.datetime)

		if not self.takeoff:
			self.takeoff = time
			if self.duration:
				self.touchdown = self.takeoff + self.duration

			return True

		elif not self.touchdown or self.link and self.touchdown == self.link.touchdown:
			self.touchdown = time

			if self.touchdown < self.takeoff:
				time = self.takeoff
				self.takeoff = self.touchdown
				self.touchdown = time

			self.duration = self.touchdown - self.takeoff
			return True

		return False

	def setDuration(self, duration):
		assert isinstance(duration, datetime.timedelta)

		if self.duration:
			return False

		self.duration = duration
		if self.takeoff:
			self.touchdown = self.takeoff + self.duration

	def setLocation(self, location):
		assert isinstance(location, Location)
		if not self.ltakeoff:
			self.ltakeoff = location
			return True

		elif not self.ltouchdown:
			self.ltouchdown = location
			return True

		return False

	def set(self, attr):
		if isinstance(attr, Aircraft):
			return self.setAircraft(attr)
		elif isinstance(attr, Pilot):
			return self.setPilot(attr)
		elif isinstance(attr, datetime.datetime):
			return self.setTime(attr)
		elif isinstance(attr, datetime.timedelta):
			return self.setDuration(attr)
		elif isinstance(attr, Location):
			return self.setLocation(attr)

		return False

	def complete(self):
		if self.takeoff and not self.touchdown:
			self.setTime(self.takeoff)
		elif not self.takeoff and self.link and self.link.takeoff:
			self.takeoff = self.link.takeoff
			if self.link.touchdown:
				self.touchdown = self.link.touchdown

		if self.ltakeoff and not self.ltouchdown:
			self.setLocation(self.ltakeoff)
		elif not self.ltakeoff:
			if self.link and self.link.ltakeoff:
				self.setLocation(self.link.ltakeoff)
				self.setLocation(self.link.ltouchdown or self.ltakeoff)

			self.setLocation(defaultLocation)
			self.setLocation(defaultLocation)

		return self.aircraft and self.pilot and self.takeoff and self.touchdown and self.ltakeoff and self.ltouchdown

	def __str__(self):
		txt = ""
		if not self.complete():
			txt += "!INCOMPLETE! "

		txt += "%s   %s   %s   %s   %s   %s   %s   %s" % (self.aircraft, self.pilot, self.copilot or "",
		                                                self.takeoff, self.ltakeoff, self.touchdown, self.ltouchdown,
		                                                    self.duration)
		return txt

print(txt)

idx = 0
for s in txt.split("\n"):
	s = s.strip()
	if not s:
		continue

	unknown = []

	print("--- %d ---" % idx)
	idx += 1

	recognizers = [tr, dr, ar, pr, lr]
	launches = []
	clarify = []
	activity = None

	while s:
		res = None

		for r in recognizers:
			res = r.recognize(s)
			if res:
				break

		if res is None:
			res = R.recognize(s)
			s = s[res.count:]
			unknown.append(res.token)
			continue

		if isinstance(res.obj, Aircraft):
			if activity:
				activity = Activity(res.obj, takeoff=activity.takeoff, touchdown=activity.touchdown,
				                                ltakeoff=activity.ltakeoff, ltouchdown=activity.ltouchdown,
				                                    link=activity)
			else:
				activity = Activity(res.obj)

			launches.append(activity)

			if len(launches) == 2:
				recognizers.remove(ar)

			while clarify:
				obj = clarify.pop()
				if not activity.set(obj):
					clarify.append(obj)
					break

		elif (activity and not activity.set(res.obj)) or not activity:
			clarify.append(res.obj)

		#print("%s = %s" % (res.token, res.obj))
		s = s[res.count:]


	for launch in launches:
		print(launch)

	if unknown:
		print("Unknown:", unknown)