# -*- coding: utf-8 -*-
#
# Airbatch - Fast flight data recognition framework
# Copyright (C) 2018 by Jan Max Meyer, Phorward Software Technologies
#

import airbatch
from browser import document, window, html

editorTimeout = None

editor = document["editor"]
editorCol = document["editor-col"]
editorRow = document["editor-row"]
editorProposal = document["editor-proposal"]
final = document["final"]
construction = document["construction"]
constructionRow = document["construction-row"]

processor = airbatch.Processor()

allowedRecognizers = [airbatch.ar, airbatch.pr, airbatch.lr, airbatch.tr, airbatch.dr]

def rebuildBatch():
	global construction, final, editorRow, constructionRow, processor

	def clearTokens(act):
		for token in [x for x in editorRow.children][:-1]:
			if token.result.obj in act:
				token.parent.removeChild(token)

	def doClose1(e):
		global construction
		row = e.target.parent.parent

		print(row.parent)
		print(construction)
		print(row.parent.id)
		if row.parent.id == "construction":
			clearTokens(row.activity)

		row.parent.removeChild(row)

	def doCommit(e):
		row = e.target.parent.parent
		rowparent = row.parent

		row.commit.style.display = "none"
		final.appendChild(row)

		acts = [row.activity]

		if row.activity.link:
			for x in [x for x in rowparent.children][:-1]:
				if x.activity is row.activity.link:
					x.commit.style.display = "none"

					final.appendChild(x)
					acts.append(x.activity)
					break

		for act in acts:
			clearTokens(act)

	for c in [x for x in construction.children][:-1]:
		construction.removeChild(c)

	processor.reset(False)

	for token in [x for x in editorRow.children][:-1]:
		processor.extend(token.result)

	lastRow = constructionRow

	res = processor.commit()
	for entry in res:
		row = html.TR()
		row.activity = entry

		if isinstance(entry, airbatch.Activity):
			for txt in [
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

			commit = html.SPAN("✓", Class="commit")
			commit.bind("click", doCommit)

			close = html.SPAN("⨉", Class="close")
			close.bind("click", doClose1)

			col = row.insertCell()
			col.appendChild(commit)
			col.appendChild(close)

			row.commit = commit
			row.close = close

		else:
			row.classList.add("error")

			col = row.insertCell()
			col.colSpan = "10"
			col.innerHTML = str(entry)

		construction.insertBefore(row, lastRow)
		#lastRow = row


def createMatchLi(result):
	def doClose(e):
		e.target.parent.parent.removeChild(e.target.parent)
		print("REMOVED", [str(x.result) for x in [x for x in editorRow.children][:-1]])

		rebuildBatch()

	token = html.SPAN(result.token, Class="token")
	label = html.SPAN(str(result.obj), Class="label")

	close = html.SPAN("⨉", Class="close")
	close.bind("click", doClose)
	close.style.display = "none"

	li = html.LI([token, label, close])
	li.result = result
	li.close = close
	return li

def extendLine(result):
	global editor, editorRow, editorCol

	if isinstance(result, html.LI):
		li = result
	else:
		li = createMatchLi(result)

	li.close.style.display = "initial"

	editorRow.insertBefore(li, editorCol)

	print([str(x.result) for x in [x for x in editorRow.children][:-1]])

	editor.value = editor.value[li.result.count:].strip()
	editor.focus()

	if editor.value:
		checkInput()
	else:
		rebuildBatch()

def clearProposals():
	global editorProposal

	while editorProposal.firstChild:
		editorProposal.removeChild(editorProposal.firstChild)

	editorProposal.style.display = "none"

def checkInput(*args, **kwargs):
	global editor, editorRow, editorProposal, allowedRecognizers

	s = editor.value.strip()

	editor.classList.remove("unknown")
	clearProposals()

	if not s:
		return

	matches = []
	editor.disabled = True

	for r in allowedRecognizers:
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
			print(editorRow.children)
			for c in editorRow.children:
				if c is editorRow.children[-1]:
					break

				if c.result.obj is res.obj:
					matches.remove(res)
	'''

	if matches:
		if len(matches) > 1:
			for res in matches:
				editorProposal.appendChild(createMatchLi(res))

			editorProposal.style.display = "block"
		else:
			extendLine(matches[0])
	else:
		editor.classList.add("unknown")

	editor.disabled = False


def selectProposal(e):
	elem = e.target
	while not isinstance(elem, html.LI):
		elem = elem.parent

	extendLine(elem)
	clearProposals()

editorProposal.bind("click", selectProposal)


def setTimeout(e):
	global editorTimeout

	e.preventDefault()
	e.stopPropagation()

	if editorTimeout:
		window.clearTimeout(editorTimeout)
		editorTimeout = None

	editorTimeout = window.setTimeout(checkInput, 1000)

editor.bind("keyup", setTimeout)
editor.bind("change", checkInput)

window.setTimeout(editor.focus, 500)

