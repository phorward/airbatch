# -*- coding: utf-8 -*-
import datetime
from recognizer import Recognizer, TimeRecognizer, DurationRecognizer
from aircraft import AircraftRecognizer, Aircraft, demoAircrafts
from pilot import PilotRecognizer, Pilot, demoPilots
from location import LocationRecognizer, Location, demoLocations

R = Recognizer()
tr = TimeRecognizer()
dr = DurationRecognizer()

ar = AircraftRecognizer(demoAircrafts)
pr = PilotRecognizer(demoPilots)
lr = LocationRecognizer(demoLocations)
defaultLocation = demoLocations[0]


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
		if self.takeoff and not self.touchdown:
			if self.link and self.link.takeoff < self.takeoff:
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

		self.duration = (self.touchdown or 0) - (self.takeoff or 0)

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

	def clone(self, link = None):
		return Activity(aircraft = self.aircraft, pilot = self.pilot, copilot=self.copilot, link = link)


txt = """
MK pille
1029 1035 1218 YX meier, horst schmu  rhkm süm
MK pille 1035 +7 YL puddy +30 rhmk rhmk
D-KYYA meier, horst  ruhm   1145 1213   edlw rhmk
DMRMK meier sta 1150 1230 süm hegenscheid
"""

#txt = "MK YL puddy 1035 +10"

print(txt)

presetLauncher = None
presetDate = None
presetAircraft = None
presetPilot = None
presetCopilot = None

idx = 0
for s in txt.split("\n"):
	s = s.strip()
	if not s:
		continue

	unknown = []
	clarify = []

	activities = []
	current = None

	while s:
		res = None

		for r in [tr, dr, pr, ar, lr]:
			res = r.recognize(s)
			if res:
				break

		#print(res)

		if res is None:
			res = R.recognize(s)
			s = s[res.count:]
			unknown.append(res)
			continue

		if isinstance(res.obj, Aircraft):
			if not current:
				current = Activity(res.obj)
			else:
				current = Activity(res.obj, link=current)

			activities.append(current)

			for cres in clarify[:]:
				if current.set(cres.obj):
					clarify.remove(cres)

		elif (current and not current.set(res.obj)) or not current:
			clarify.append(res)

		#print("%s = %s" % (res.token, res.obj))
		s = s[res.count:]

	if len(activities) == 0 and clarify:
		if presetAircraft:
			current = presetAircraft.clone()
			for cres in clarify[:]:
				if current.set(cres.obj):
					clarify.remove(cres)

			activities.append(current)
		else:
			first = True
			for c in clarify[:]:
				if isinstance(c.obj, Pilot):
					if first:
						first = False
						presetCopilot = None
						presetPilot = None

					if not presetPilot:
						presetPilot = c.obj
						clarify.remove(c)
					elif not presetCopilot:
						presetCopilot = c.obj
						clarify.remove(c)

	if len(activities) == 1:
		launch = activities[0]

		if not launch.complete():
			if launch.aircraft.launcher:
				presetLauncher = launch
			else:
				presetAircraft = launch
		else:
			if launch.aircraft.kind == "glider" and not launch.aircraft.selfstart:
				if presetLauncher:
					llaunch = presetLauncher.clone(launch)
					activities.insert(0, llaunch)
					llaunch.complete()

					for cres in clarify[:]:
						if isinstance(cres.obj, datetime.datetime) and cres.obj >= launch.touchdown:
							launch.touchdown = cres.obj
							clarify.remove(cres)
							launch.complete()

				else:
					print("--- %d ---" % idx)
					print(launch)
					idx += 1
			else:
				print("--- %d ---" % idx)
				print(launch)
				idx += 1

	# No else!
	if len(activities) > 1:
		if len(activities) > 2:
			print("Too many launches per row, please spicify only two aircraft in total per row")

		print("--- %d ---" % idx)
		idx += 1
		for launch in activities:
			launch.complete()
			print(launch)

	unknown.extend(clarify)

	if unknown:
		print("Unknown:", [(res.obj or res.token) for res in unknown])