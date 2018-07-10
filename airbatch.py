# -*- coding: utf-8 -*-
import datetime
from recognizer import Recognizer, Result, TimeRecognizer, DurationRecognizer
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

			if self.duration:
				self.touchdown = self.takeoff + self.duration

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
	def __init__(self, tokens, row = None):
		super().__init__()

		self.row = row
		self.tokens = tokens

	def __str__(self):
		return ", ".join([(str(res.obj) if res.obj else res.token + "?") for res in self.tokens])

class Processor():
	def __init__(self):
		super().__init__()

		self.presetLauncher = None
		self.presetDate = None
		self.presetAircraft = None
		self.presetPilot = None
		self.presetCopilot = None

		self.unknown = []
		self.clarify = []
		self.tokens = []

		self.activities = []
		self.current = None

	def reset(self, hard = True):
		if hard:
			self.presetLauncher = None
			self.presetDate = None
			self.presetAircraft = None
			self.presetPilot = None
			self.presetCopilot = None

		self.unknown = []
		self.clarify = []
		self.tokens = []

		self.activities = []
		self.current = None
		
	def extend(self, res):
		if not isinstance(res, Result):
			res = Result(len(str(res)), str(res), res)

		self.tokens.append(res)

		if isinstance(res.obj, Aircraft):
			if not self.current:
				self.current = Activity(res.obj)
			else:
				self.current = Activity(res.obj, link=self.current)

			self.activities.append(self.current)

			for cres in self.clarify[:]:
				if self.current.set(cres.obj):
					self.clarify.remove(cres)

		elif (self.current and not self.current.set(res.obj)) or not self.current:
			self.clarify.append(res)

	def commit(self):
		results = []

		print(len(self.activities), [(str(res.obj) if res.obj else res.token) for res in self.clarify])

		if len(self.activities) == 0 and self.clarify:
			if self.presetAircraft:
				self.current = self.presetAircraft.clone()

				for cres in self.clarify[:]:
					if self.current.set(cres.obj):
						self.clarify.remove(cres)

				self.current.complete()
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

		if len(self.activities) == 1:
			launch = self.activities[0]

			if not launch.complete():
				if not launch.cloneof:
					if self.presetAircraft and launch.aircraft is self.presetAircraft.aircraft:
						launch.cloneof = self.presetAircraft
						launch.complete()
					elif self.presetLauncher and launch.aircraft is self.presetLauncher.aircraft:
						launch.cloneof = self.presetLauncher
						launch.complete()

				if launch.takeoff:
					if not launch.pilot:
						launch.pilot = self.presetPilot
					if not launch.copilot:
						launch.copilot = self.presetCopilot

					if launch.complete():
						results.append(launch)
					else:
						self.clarify.extend(self.tokens)

				if launch.aircraft.launcher:
					self.presetAircraft = self.presetLauncher = launch
				else:
					self.presetAircraft = launch

			else:
				if launch.aircraft.kind == "glider" and not launch.aircraft.selfstart:
					if self.presetLauncher:
						llaunch = self.presetLauncher.clone(launch)
						self.activities.insert(0, llaunch)
						llaunch.complete()

						for cres in self.clarify[:]:
							if isinstance(cres.obj, datetime.datetime) and cres.obj >= launch.touchdown:
								launch.touchdown = cres.obj
								self.clarify.remove(cres)
								launch.complete()

					else:
						print(launch)
						results.append(launch)

						self.presetAircraft = launch
				else:
					print(launch)
					results.append(launch)

					self.presetAircraft = launch

		# No else!
		if len(self.activities) > 1:
			if len(self.activities) > 2:
				print("Too many launches per row, please spicify only two aircraft in total per row")

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

		self.unknown.extend(self.clarify)

		if self.unknown:
			print("Unknown:", [(str(res.obj) if res.obj else res.token) for res in self.unknown])
			results.append(Error(self.unknown))

		self.reset(False)

		return results

	def parse(self, txt):
		results = []
		print(txt)

		idx = 0
		row = 0
		for s in txt.split("\n"):
			row += 1
			s = s.strip()
			if not s:
				self.presetAircraft = None
				self.presetLauncher = None
				self.presetPilot = None
				self.presetCopilot = None
				continue

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
					self.unknown.append(res)
					self.tokens.append(res)
					continue

				self.extend(res)

				#print("%s = %s" % (res.token, res.obj))
				s = s[res.count:]

			rowResults = self.commit()

			if rowResults:
				print("--- %d ---" % idx)
				idx += 1

				for res in rowResults:
					res.row = row

				results.extend(rowResults)

		return results
