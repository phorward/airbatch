# -*- coding: utf-8 -*-
#
# Airbatch - Fast flight data recognition framework
# Copyright (C) 2018, 2019 by Jan Max Meyer, Phorward Software Technologies
#

from browser import document
import airbatch

class BatchProcessor(airbatch.Processor):
	def __init__(self):
		super().__init__()

		document["result"].style.display = "none"
		document["btn-parse"].bind("click", self.doParse)

	def insertCode(self, txt):
		editor = document["editor"]
		start = editor.selectionStart
		txt = editor.value[:start] + txt + " " + editor.value[start:]
		editor.value = txt

	def insertObject(self, event):
		opt = event.target

		print(opt)
		txt = str(opt.obj)

		if " - " in txt:
			self.insertCode(txt.split(" - ", 1)[0].strip())
		elif " (" in txt:
			self.insertCode(txt.split(" (", 1)[0].strip())
		else:
			self.insertCode(txt)

	def makeList(self, element, items):
		for i in items:
			opt = document.createElement("option")
			opt["value"] = i.key
			opt.obj = i
			opt.appendChild(document.createTextNode(str(i)))
			element.appendChild(opt)

	def _aircraftsAvailable(self, rec):
		self.makeList(document["aircraft"], rec.items)
		document["aircraft"].bind("dblclick", self.insertObject)

	def _pilotsAvailable(self, rec):
		self.makeList(document["pilot"], rec.items)
		document["pilot"].bind("dblclick", self.insertObject)

	def _locationsAvailable(self, rec):
		self.makeList(document["location"], rec.items)
		document["location"].bind("dblclick", self.insertObject)

	def doParse(self, event):

		self.reset()
		res = self.parse(document["editor"].value)

		body = document["result"].tBodies[0]
		while body.firstChild:
			body.removeChild(body.firstChild)

		for entry in res:
			row = body.insertRow()

			if isinstance(entry, airbatch.Activity):
				for txt in [
					str(entry.row),
					entry.takeoff.strftime("%d.%m.%Y"),
					str(entry.aircraft),
					str(entry.pilot),
					str(entry.copilot) if entry.copilot else "-",
					entry.takeoff.strftime("%H:%M"),
					str(entry.ltakeoff),
					entry.touchdown.strftime("%H:%M"),
					str(entry.ltouchdown),
					str(entry.duration)]:

					col = row.insertCell()
					col.innerHTML = txt
			else:
				row.classList.add("error")

				col = row.insertCell()
				col.innerHTML = str(entry.row)

				col = row.insertCell()
				col.colSpan = "9"
				col.innerHTML = str(entry)

			document["result"].style.display = "table"


BatchProcessor()

print("AIRBATCH-BATCH LOADED")
