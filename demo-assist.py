# -*- coding: utf-8 -*-
#
# Airbatch - Fast flight data recognition framework
# Copyright (C) 2018, 2019 by Jan Max Meyer, Phorward Software Technologies
#

import airbatch, datetime
from browser import document, window, html

class AssistantProcessor(airbatch.Processor):

	def __init__(self):
		super().__init__()

		self.allowedRecognizers = [
			self.aircraftRecognizer,
			self.pilotRecognizer,
			self.pilotRecognizer,
			self.locationRecognizer,
			self.timeRecognizer,
			self.durationRecognizer
		]

		self.editorTimeout = None

		self.editor = document["editor"]
		self.editorCol = document["editor-col"]
		self.editorRow = document["editor-row"]
		self.editorProposal = document["editor-proposal"]
		self.final = document["final"]
		self.construction = document["construction"]
		self.constructionRow = document["construction-row"]

		self.batch = document["batch"]
		self.batchSwitch = document["batch-switch"]
		self.batchEditor = document["batch-editor"]
		self.batchErrorRow = None

		self.editorProposal.bind("click", self.selectProposal)
		#editor.bind("keyup", setTimeout)
		self.editor.bind("change", self.checkInput)
		self.batchSwitch.bind("change", self.switchMode)
		document["btn-parse"].bind("click", self.doParse)

		window.setTimeout(self.editor.focus, 500)

		batch = window.localStorage.getItem(datetime.datetime.now().strftime("batch-%Y-%m-%d"))
		if batch:
			window.alert("%d Starts aus localStorage im Batch-Modus wiederhergestellt" % (batch.count("\n") + 1))
			self.batchEditor.value = batch

	# --- Pure batch mode

	def insertCode(self, txt):
		start = self.batchEditor.selectionStart
		txt = self.batchEditor.value[:start] + txt + " " + self.batchEditor.value[start:]
		self.batchEditor.value = txt

	def insertObject(self, event):
		opt = event.target
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
		self.makeList(document["batch-aircraft"], rec.items)
		document["batch-aircraft"].bind("dblclick", self.insertObject)

	def _pilotsAvailable(self, rec):
		self.makeList(document["batch-pilot"], rec.items)
		document["batch-pilot"].bind("dblclick", self.insertObject)

	def _locationsAvailable(self, rec):
		self.makeList(document["batch-location"], rec.items)
		document["batch-location"].bind("dblclick", self.insertObject)

	def doParse(self, event):
		self.reset()
		res = self.parse(self.batchEditor.value)

		lastRow = self.constructionRow

		if self.batchErrorRow:
			self.batchErrorRow.parent.removeChild(self.batchErrorRow)
			self.batchErrorRow = None

		for entry in res:
			row = html.TR()
			row.activity = entry

			if isinstance(entry, airbatch.Activity):
				for txt in [
					#str(entry.row),
					#entry.takeoff.strftime("%d.%m.%Y"),
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

				row.commit = html.SPAN("✓", Class="commit")
				row.commit.bind("click", self.commitRow)

				row.close = html.SPAN("⨉", Class="close")
				row.close.bind("click", self.removeRow)

				col = row.insertCell()
				col.appendChild(row.commit)
				col.appendChild(row.close)

			else:
				self.batchErrorRow = row
				row.classList.add("error")

				col = row.insertCell()
				col.colSpan = "10"
				col.innerHTML = str(entry)

			self.construction.insertBefore(row, lastRow)

	# --- Interactive mode

	def clearTokens(self, act):
		for token in [x for x in self.editorRow.children][:-1]:
			if token.result.obj in act:
				token.parent.removeChild(token)

	def removeRow(self, e):
		row = e.target.parent.parent

		print(row.parent)
		print(self.construction)
		print(row.parent.id)

		if row.parent.id == "construction":
			self.clearTokens(row.activity)

		row.parent.removeChild(row)
		self.updateTable()

	def commitRow(self, e):
		row = e.target.parent.parent
		rowparent = row.parent

		row.commit.style.display = "none"
		self.final.appendChild(row)

		acts = [row.activity]

		if row.activity.link:
			for x in [x for x in rowparent.children][:-1]:
				if x.activity is row.activity.link:
					x.commit.style.display = "none"

					self.final.appendChild(x)
					acts.append(x.activity)
					break

		for act in acts:
			self.clearTokens(act)

		self.updateTable()

	def updateTable(self):
		print("updateTable")

		while True:
			changes = False
			children = [x for x in self.final.children]

			for row, nextRow in zip(children, children[1:]):
				if nextRow.activity.takeoff < row.activity.takeoff:
					self.final.insertBefore(nextRow, row)
					changes = True
					break


			if changes:
				continue

			break

		batch = "\n".join([repr(c.activity) for c in children])
		window.localStorage.setItem(datetime.datetime.now().strftime("batch-%Y-%m-%d"), batch)

		if children:
			document["btn-download"].style.display = ""
		else:
			document["btn-download"].style.display = "none"

	def rebuildBatch(self):
		for c in [x for x in self.construction.children][:-1]:
			self.construction.removeChild(c)

		self.reset(False)

		for token in [x for x in self.editorRow.children][:-1]:
			self.extend(token.result)

		lastRow = self.constructionRow

		res = self.commit()
		for entry in res:
			row = html.TR()
			row.activity = entry

			if isinstance(entry, airbatch.Activity):
				for txt in [
					#entry.takeoff.strftime("%d.%m.%Y"),
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

				row.commit = html.SPAN("✓", Class="commit")
				row.commit.bind("click", self.commitRow)

				row.close = html.SPAN("⨉", Class="close")
				row.close.bind("click", self.removeRow)

				col = row.insertCell()
				col.appendChild(row.commit)
				col.appendChild(row.close)

			else:
				row.classList.add("error")

				col = row.insertCell()
				col.colSpan = "10"
				col.innerHTML = str(entry)

			self.construction.insertBefore(row, lastRow)
			#lastRow = row

	def createMatchLi(self, result):
		def doClose(e):
			e.target.parent.parent.removeChild(e.target.parent)
			print("REMOVED", [str(x.result) for x in [x for x in self.editorRow.children][:-1]])

			self.rebuildBatch()

		token = html.SPAN(result.token, Class="token")
		label = html.SPAN(str(result.obj), Class="label")

		close = html.SPAN("⨉", Class="close")
		close.bind("click", doClose)
		close.style.display = "none"

		li = html.LI([token, label, close])
		li.result = result
		li.close = close
		return li

	def extendLine(self, result):
		if isinstance(result, html.LI):
			li = result
		else:
			li = self.createMatchLi(result)

		li.close.style.display = "initial"

		self.editorRow.insertBefore(li, self.editorCol)

		print([str(x.result) for x in [x for x in self.editorRow.children][:-1]])

		self.editor.value = self.editor.value[li.result.count:].strip()
		self.editor.focus()

		if self.editor.value:
			self.checkInput()
		else:
			self.rebuildBatch()

	def clearProposals(self):
		while self.editorProposal.firstChild:
			self.editorProposal.removeChild(self.editorProposal.firstChild)

		self.editorProposal.style.display = "none"

	def checkInput(self, *args, **kwargs):
		s = self.editor.value.strip()

		self.editor.classList.remove("unknown")
		self.clearProposals()

		if not s:
			return

		matches = []
		self.editor.disabled = True

		for r in self.allowedRecognizers:
			res = r.propose(s)

			if res:
				if isinstance(res, list):
					matches.extend(res)
				else:
					matches.append(res)

					if len(matches) == 1 and res.token == s:
						break

		print(matches)

		'''
		for res in matches[:]:
			print(res)
			if isinstance(res.obj, (airbatch.Aircraft, airbatch.Pilot)):
				print(self.editorRow.children)
				for c in self.editorRow.children:
					if c is self.editorRow.children[-1]:
						break
	
					if c.result.obj is res.obj:
						matches.remove(res)
		'''

		if matches:
			if len(matches) > 1:
				for res in matches:
					self.editorProposal.appendChild(self.createMatchLi(res))

				self.editorProposal.style.display = "block"
			else:
				self.extendLine(matches[0])
		else:
			self.editor.classList.add("unknown")

		self.editor.disabled = False


	def selectProposal(self, e):
		elem = e.target
		while not isinstance(elem, html.LI):
			elem = elem.parent

		self.extendLine(elem)
		self.clearProposals()

	def setTimeout(self, e):
		e.preventDefault()
		e.stopPropagation()

		if self.editorTimeout:
			window.clearTimeout(self.editorTimeout)
			self.editorTimeout = None

		self.editorTimeout = window.setTimeout(self.checkInput, 1500)

	def switchMode(self, e):
		e.preventDefault()
		e.stopPropagation()

		if self.batch.style.display == "none":
			self.batch.style.display = ""
			self.constructionRow.style.display = "none"
		else:
			self.batch.style.display = "none"
			self.constructionRow.style.display = ""


AssistantProcessor()

print("AIRBATCH-ASSISTANT LOADED")
