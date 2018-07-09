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
		if self.cloneof:
			if not self.pilot:
				self.pilot = self.cloneof.pilot
			if not self.takeoff:
				self.takeoff = self.cloneof.touchdown
			if not self.ltakeoff:
				self.ltakeoff = self.cloneof.ltakeoff

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
		return Activity(aircraft = self.aircraft, link = link, cloneof = self)

class Error():
	def __init__(self, row, tokens):
		self.row = row
		self.tokens = tokens

	def __str__(self):
		return ", ".join([(str(res.obj) if res.obj else res.token + "?") for res in self.tokens])


def parse(txt):
	print(txt)
	results = []

	presetLauncher = None
	presetDate = None
	presetAircraft = None
	presetPilot = None
	presetCopilot = None

	idx = 0
	row = 0
	for s in txt.split("\n"):
		row += 1
		s = s.strip()
		if not s:
			presetAircraft = None
			presetLauncher = None
			presetPilot = None
			presetCopilot = None
			continue

		unknown = []
		clarify = []
		tokens = []

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
				tokens.append(res)
				continue

			tokens.append(res)

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

		print(len(activities), [(str(res.obj) if res.obj else res.token) for res in clarify])

		if len(activities) == 0 and clarify:
			if presetAircraft:
				current = presetAircraft.clone()

				for cres in clarify[:]:
					if current.set(cres.obj):
						clarify.remove(cres)

				current.complete()
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
				if launch.takeoff:
					if not launch.pilot:
						launch.pilot = presetPilot
					if not launch.copilot:
						launch.copilot = presetCopilot

					if launch.complete():
						launch.row = row
						results.append(launch)
						idx += 1
					else:
						clarify.extend(tokens)

				if launch.aircraft.launcher:
					presetAircraft = presetLauncher = launch
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
						launch.row = row
						results.append(launch)
						idx += 1

						presetAircraft = launch
				else:
					print("--- %d ---" % idx)
					print(launch)
					launch.row = row
					results.append(launch)
					idx += 1

					presetAircraft = launch

		# No else!
		if len(activities) > 1:
			if len(activities) > 2:
				print("Too many launches per row, please spicify only two aircraft in total per row")

			print("--- %d ---" % idx)
			idx += 1
			for launch in activities:
				launch.complete()
				launch.row = row
				print(launch)
				results.append(launch)

		unknown.extend(clarify)

		if unknown:
			print("Unknown:", [(str(res.obj) if res.obj else res.token) for res in unknown])
			results.append(Error(row, unknown))

	return results
