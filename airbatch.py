# -*- coding: utf-8 -*-
#
# Airbatch - Fast flight data recognition framework
# Copyright (C) 2018, 2019 by Jan Max Meyer, Phorward Software Technologies
#

import datetime, json

try:
	from browser import ajax
except ModuleNotFoundError:
	ajax = None


# --- RECOGNIZER-----------------------------------------------------------------------------------

class Result:
	"""
	Defines a recognizer result.
	"""
	def __init__(self, count, token, obj=None):
		self.count = count
		self.token = token
		self.obj = obj

	def commit(self, obj):
		self.obj = obj
		return self

	def clone(self, obj = None):
		if isinstance(obj, list):
			ret = []

			for x in obj:
				ret.append(self.clone(x))

			return ret

		return Result(self.count, self.token, obj or self.obj)

	def __str__(self):
		return "'%s' => %s" % (self.token, str(self.obj) or "None")


class Recognizer:
	"""
	Basic recognizer. It recognizes a token from the input stream and disregards whitespace
	and other delimiters.
	"""
	factory = None

	def __init__(self):
		super().__init__()

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

	def propose(self, s):
		return self.recognize(s)


class TimeRecognizer(Recognizer):
	"""
	Recognize a time.
	"""
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


class DurationRecognizer(Recognizer):
	"""
	Recognize a duration.
	"""

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


class ItemRecognizer(Recognizer):
	"""
	Basic item recognizer.
	"""
	itemFactory = None

	def __init__(self, data, callback = None):
		super().__init__()

		if isinstance(data, str):
			assert ajax
			self.fetch(url=data, callback=callback)
			data = None

		self.items = data or []
		if self.items:
			self.prepare()

			if callback:
				callback(self)

	def fetch(self, url, data = None, callback = None):
		assert self.itemFactory

		req = ajax.ajax()
		req.bind("complete", self._fetchCallback)
		req.callback = callback

		# pass the arguments in the query string
		req.open("POST", url, True)
		req.set_header("content-type", "application/x-www-form-urlencoded")

		req.send(data or {})

	def prepare(self):
		"""
		Function to prepare the recognizer based on its loaded items.
		:return:
		"""
		pass

	def _fetchCallback(self, req):
		assert req.status in [0, 200]
		answ = json.loads(req.text)

		for entry in answ["skellist"]:
			self.items.append(self.itemFactory(entry))

		self.prepare()

		print("%s: %d items loaded" % (self.__class__.__name__, len(self.items)))

		if req.callback:
			req.callback(self)


# --- AIRCRAFT-------------------------------------------------------------------------------------

class Aircraft:
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

	@staticmethod
	def fromServer(cls, entry):
		return Aircraft(entry["key"], entry["reg"], entry["name"], entry["seats"], entry["compreg"],
					entry["aircraftkind"], entry["is_launcher"], entry["is_selfstarter"])


class AircraftRecognizer(ItemRecognizer):
	"""
	Recognize an aircraft by registration-no, competition-no or short reg no.
	"""
	itemFactory = Aircraft.fromServer

	def recognize(self, s):
		ret = super().recognize(s)

		for aircraft in self.items:
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

	def propose(self, s):
		ret = super().recognize(s)
		res = []

		for aircraft in self.items:
			if aircraft.regNo.lower().startswith(ret.token):
				res.append(aircraft)
			elif aircraft.compNo and aircraft.compNo.lower().startswith(ret.token):
				res.append(aircraft)
			elif ret.token.replace("-", "") == aircraft.regNo.lower().replace("-", ""):
				res.append(aircraft)
			elif len(ret.token) == 2 and ret.token == aircraft.regNo[-2:].lower():
				res.append(aircraft)
			elif ret.token in aircraft.type.lower():
				res.append(aircraft)

		return ret.clone(res)


demoAircrafts = [
	Aircraft("1", "D-1234", "Libelle", compNo="YL"),
	Aircraft("2", "D-2074", "ASK 13", seats=2),
	Aircraft("3", "D-8984", "ASK 13", seats=2),
	Aircraft("4", "D-5014", "Duo Discus", compNo="YX", seats=2),
	Aircraft("5", "D-KYYA", "Arcus M", compNo="YA", seats=2, selfstart=True),
	Aircraft("6", "D-MRMK", "Turbo Savage", seats=2, kind="microlight", launcher=True)
]

# --- PILOT ---------------------------------------------------------------------------------------

class Pilot:
	def __init__(self, key, lastName, firstName, nickName = None):
		super().__init__()

		self.key = key
		self.firstName = firstName
		self.lastName = lastName
		self.nickName = nickName

	def __str__(self):
		return "%s, %s" % (self.lastName, self.firstName)

	@staticmethod
	def fromServer(cls, entry):
		return Pilot(entry["key"], entry["lastname"], entry["firstname"], entry["nickname"])


class PilotRecognizer(ItemRecognizer):
	"""
	Recognize a pilot, either by lastname, lastname+firstname or nickname.
	"""
	itemFactory = Pilot.fromServer

	def prepare(self):
		self.families = {}
		self.nicks = {}

		for pilot in self.items:
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

				for key in sorted(self.nicks.keys()):
					if key.startswith(familyName):
						return ret.commit(self.nicks[key])
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


demoPilots = [
	Pilot("1", "Meier", "Max", nickName="Pille"),
	Pilot("2", "Schmudel", "Rainer"),
	Pilot("3", "Schielmann", "Peter", nickName="Puddy"),
	Pilot("4", "Meier", "Horst"),
	Pilot("5", "Ruhm", "Hannah"),
	Pilot("6", "Starker", "Philipp")
]

# --- LOCATION ------------------------------------------------------------------------------------

defaultLocation = None

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

	@staticmethod
	def fromServer(cls, entry):
		return Location(entry["key"], entry["name"], entry["shortname"], entry["icao"])


class LocationRecognizer(ItemRecognizer):
	"""
	Recognize a location, either by name, ICAO name or abbreviation.
	"""
	itemFactory = Location.fromServer

	def prepare(self):
		global defaultLocation
		defaultLocation = self.items[0]

		self.icaos = {}
		self.shorts = {}

		for a in self.items:
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

		for a in self.items:
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

		for a in self.items:
			if ret.token in a.longName.lower():
				res.append(a)

		return ret.clone(res)


demoLocations = [
	Location("1", "Iserlohn-Rheinermark", "rhmk"),
	Location("2", "Iserlohn-Sümmern"),
	Location("3", "Dortmund", "DTM", "EDLW"),
	Location("4", "Meierberg"),
	Location("5", "Altena-Hegenscheid")
]

# --- ACTIVITY ------------------------------------------------------------------------------------

class Activity():
	def __init__(self, aircraft = None, takeoff = None, touchdown = None, duration = None,
					pilot = None, copilot = None, ltakeoff = None, ltouchdown = None,
	                    note = None, link = None, cloneof = None):

		self.row = 0

		self.aircraft = aircraft
		self.takeoff = takeoff
		self.touchdown = touchdown
		self.duration = duration
		self.pilot = pilot
		self.copilot = copilot

		self.ltakeoff = ltakeoff
		self.ltouchdown = ltouchdown

		self.note = note
		self.cloneof = cloneof

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
		print("setTime", time)
		assert isinstance(time, datetime.datetime)

		print("---")
		print(self)
		print("---")

		ok = False

		if not self.takeoff:
			self.takeoff = time
			if self.duration:
				self.touchdown = self.takeoff + self.duration

			ok = True

		if (not self.touchdown
			or self.touchdown == self.takeoff
			or (self.link and self.link.touchdown == self.touchdown)):
			self.touchdown = time

			# flip takeoff and touchdown time
			if self.touchdown < self.takeoff:
				time = self.takeoff
				self.takeoff = self.touchdown
				self.touchdown = time

			self.duration = self.touchdown - self.takeoff
			ok = True

		if self.link and (
			not self.link.takeoff
			or not self.link.touchdown
			or self.link.takeoff == self.link.touchdown
			or (self.link.takeoff == self.takeoff and self.link.touchdown == self.touchdown)):

			self.link.link = None
			ok = self.link.setTime(time)
			self.link.link = self

		return ok

	def setDuration(self, duration):
		print("setDuration", duration)
		assert isinstance(duration, datetime.timedelta)

		if self.link and not self.link.duration:
			self.link.link = None
			ret = self.link.setDuration(duration)
			self.link.link = self
			return ret

		if self.duration:
			return False

		self.duration = duration

		if not self.takeoff and self.cloneof:
			self.takeoff = self.cloneof.touchdown

		if self.takeoff:
			self.touchdown = self.takeoff + self.duration

		return True

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
		if self.link:
			if not self.takeoff:
				self.takeoff = self.link.takeoff
			if not self.ltakeoff:
				self.ltakeoff = self.link.ltakeoff
			if self.duration:
				self.touchdown = self.takeoff + self.duration

		if self.cloneof:
			if not self.pilot:
				self.pilot = self.cloneof.pilot
			if not self.copilot and self.cloneof.copilot:
				self.copilot = self.cloneof.copilot
			if not self.takeoff:
				self.takeoff = self.cloneof.touchdown
			if not self.ltakeoff:
				self.ltakeoff = self.cloneof.ltakeoff

			if self.duration:
				self.touchdown = self.takeoff + self.duration

		if self.takeoff and not self.touchdown:
			if self.link and self.link.takeoff and self.link.takeoff < self.takeoff:
				self.touchdown = self.takeoff
				self.takeoff = self.link.takeoff
			else:
				self.setTime(self.takeoff)
		elif not self.takeoff and self.link and self.link.takeoff:
			self.takeoff = self.link.takeoff
			if self.duration:
				self.touchdown = self.takeoff + self.duration
			elif self.link.touchdown:
				self.touchdown = self.link.touchdown

		if self.takeoff and self.touchdown:
			self.duration = self.touchdown - self.takeoff

		if self.ltakeoff and not self.ltouchdown:
			self.setLocation(self.ltakeoff)
		elif not self.ltakeoff:
			if self.link and self.link.ltakeoff:
				self.setLocation(self.link.ltakeoff)
				self.setLocation(self.link.ltouchdown or self.ltakeoff)

			self.setLocation(defaultLocation)
			self.setLocation(defaultLocation)

		return self.aircraft and self.pilot and self.takeoff and self.touchdown and self.ltakeoff and self.ltouchdown

	def __contains__(self, obj):
		return (self.aircraft is obj
				or self.pilot is obj
				or self.copilot is obj
				or self.takeoff is obj
				or self.touchdown is obj
				or self.ltakeoff is obj
				or self.ltouchdown is obj
		        or (self.duration is obj or self.duration == obj))

	def __str__(self):
		#self.complete()
		txt = str(self.aircraft)

		txt += " (%s)" % "   ".join(
			[str(i) for i in [
				self.pilot, self.copilot or "",
				self.takeoff, self.ltakeoff, self.touchdown, self.ltouchdown]
			 		if i
		])

		if self.link:
			self.link.link = None
			txt += " linked to " + str(self.link)
			self.link.link = self

		if self.cloneof:
			txt += " was cloned by " + str(self.cloneof)

		return txt

	def __repr__(self):
		if not self.complete():
			return ""

		return "%s %s %s %s %s %s %s" % (
			self.aircraft.regNo,
			str(self.pilot),
			str(self.copilot) if self.copilot else "",
			self.takeoff.strftime("%H%M") if self.takeoff else None,
			str(self.ltakeoff),
			self.touchdown.strftime("%H%M") if self.touchdown else None,
			str(self.ltouchdown)
		)

	def clone(self, link = None):
		if link is None and self.link:
			self.link.link = None
			link = self.link.clone()
			self.link.link = self

		return Activity(aircraft = self.aircraft, link = link, cloneof = self)

class Error():
	def __init__(self, content, row = None):
		super().__init__()

		self.row = row
		self.tokens = content if isinstance(content, list) else None
		self.txt = content if isinstance(content, str) else None

	def __str__(self):
		return self.txt or ", ".join([(str(res.obj) if res.obj else res.token + "?") for res in self.tokens])

class Processor():
	def __init__(self):
		super().__init__()

		self.defaultRecognizer = Recognizer()

		self.timeRecognizer = TimeRecognizer()
		self.durationRecognizer = DurationRecognizer()

		#self.aircraftRecognizer = AircraftRecognizer("/json/aircraft/list", self._aircraftsAvailable)
		#self.pilotRecognizer = PilotRecognizer("/json/pilot/list", self._pilotsAvailable)
		#self.locationRecognizer = LocationRecognizer("/json/place/list", self._locationsAvailable)

		self.aircraftRecognizer = AircraftRecognizer(demoAircrafts, self._aircraftsAvailable)
		self.pilotRecognizer = PilotRecognizer(demoPilots, self._pilotsAvailable)
		self.locationRecognizer = LocationRecognizer(demoLocations, self._locationsAvailable)

		self.presetLauncher = None
		self.presetDate = None
		self.presetAircraft = None
		self.presetPilot = None
		self.presetCopilot = None
		self.presetLocation = None

		self.unknown = []
		self.clarify = []
		self.tokens = []

		self.activities = []
		self.current = None

	def _aircraftsAvailable(self, rec):
		pass

	def _pilotsAvailable(self, rec):
		pass

	def _locationsAvailable(self, rec):
		pass

	def reset(self, hard = True):
		if hard:
			self.presetLauncher = None
			self.presetDate = None
			self.presetAircraft = None
			self.presetPilot = None
			self.presetCopilot = None
			self.presetLocation = None

		self.unknown = []
		self.clarify = []
		self.tokens = []

		self.activities = []
		self.current = None

	def canTowLaunch(self, a1, a2):
		return a1.kind == "glider" and a2.launcher or a2.kind == "glider" and a1.launcher
		
	def extend(self, res):
		print("extend", res)

		if not isinstance(res, Result):
			res = Result(len(str(res)), str(res), res)

		self.tokens.append(res)

		if isinstance(res.obj, Aircraft):
			# Create activity on new aircraft, check if it can be linked.
			if self.current and self.canTowLaunch(self.current.aircraft, res.obj):
				print("Linking current activity with %s to %s" % (self.current.aircraft, res.obj))
				self.current = Activity(res.obj, link=self.current)
			else:
				print("Creating new activity for %s" % res.obj)
				self.current = Activity(res.obj)

			self.activities.append(self.current)

			while self.clarify:
				cres = self.clarify.pop(0)
				if not self.current.set(cres.obj):
					self.clarify.insert(0, cres)
					break

		elif (self.current and not self.current.set(res.obj)) or not self.current:
			self.clarify.append(res)

	def commit(self):
		results = []

		print("commit", len(self.activities), [(str(res.obj) if res.obj else res.token) for res in self.clarify])

		if len(self.activities) == 0 and self.clarify:
			if self.presetAircraft:
				self.current = self.presetAircraft.clone()

				while self.clarify:
					cres = self.clarify.pop(0)
					if not self.current.set(cres.obj):
						self.clarify.insert(0, cres)
						break

				self.current.complete()

				if self.current.link:
					self.activities.append(self.current.link)

				self.activities.append(self.current)

			else:
				first = True
				for c in self.clarify[:]:
					if isinstance(c.obj, Pilot):
						if first:
							first = False
							self.presetCopilot = None
							self.presetPilot = None

						if not self.presetPilot:
							self.presetPilot = c.obj
							self.clarify.remove(c)
						elif not self.presetCopilot:
							self.presetCopilot = c.obj
							self.clarify.remove(c)

		if self.activities:
			if len(self.activities) > 2:
				print("Too many launches per row, please specify only two aircraft in total per row")

			for launch in self.activities:
				ok = launch.complete()

				if not ok:
					if not launch.cloneof:
						if self.presetAircraft and launch.aircraft is self.presetAircraft.aircraft:
							launch.cloneof = self.presetAircraft
							ok = launch.complete()
						elif self.presetLauncher and launch.aircraft is self.presetLauncher.aircraft:
							launch.cloneof = self.presetLauncher
							ok = launch.complete()

				if launch.aircraft.launcher:
					self.presetLauncher = launch
				else:
					self.presetAircraft = launch

				if not ok:
					continue

				print(launch)
				results.append(launch)

		# OK, now clarify the rest, if necessary
		if self.clarify:
			activity = None
			consumed = 0

			while self.clarify:
				cres = self.clarify.pop(0)

				if activity is None and results:
					print("Cloning %s" % results[-1].aircraft)
					activity = results[-1].clone()

					if activity.link:
						print("   Linked %s" % activity.link.aircraft)


				if not activity or not activity.set(cres.obj):
					self.clarify.insert(0, cres)

					if consumed == 0:
						break

					if activity.complete():
						if activity.link:
							results.append(activity.link)

						results.append(activity)
						self.presetAircraft = activity

						activity = None
						consumed = 0

				else:
					consumed += 1

			if activity and activity.complete():
				if activity.link:
					results.append(activity.link)

				results.append(activity)

				self.presetAircraft = activity

		# Extend unrecognized tokens
		self.unknown.extend(self.clarify)

		if self.unknown:
			print("Unknown:", [(str(res.obj) if res.obj else res.token) for res in self.unknown])
			results.append(Error(self.unknown))

		for act in results:
			if not act.complete():
				results.append(Error(str(act)))

		self.reset(False)

		return results

	def parse(self, txt):
		results = []
		print(txt)

		for row, s in enumerate(txt.split("\n")):
			print("--- %d ---" % row)
			s = s.strip()

			#if not s:
			#	self.presetAircraft = None
			#	self.presetLauncher = None
			#	self.presetPilot = None
			#	self.presetCopilot = None
			#	continue

			while s:
				res = None

				for r in [self.timeRecognizer, self.durationRecognizer,
						  	self.pilotRecognizer, self.aircraftRecognizer,
						  		self.locationRecognizer]:
					res = r.recognize(s)
					if res:
						break

				#print(res)

				if res is None:
					res = self.defaultRecognizer.recognize(s)
					s = s[res.count:]
					self.unknown.append(res)
					self.tokens.append(res)
					continue

				self.extend(res)

				#print("%s = %s" % (res.token, res.obj))
				s = s[res.count:]

			rowResults = self.commit()

			if rowResults:
				for res in rowResults:
					res.row = row

				results.extend(rowResults)

		return results

print("AIRBATCH LOADED")
