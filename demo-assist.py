# -*- coding: utf-8 -*-
import airbatch
from browser import document, window, html

editorTimeout = None

editor = document["editor"]
editorCol = document["editor-col"]
editorRow = document["editor-row"]
editorProposal = document["editor-proposal"]

allowedRecognizers = [airbatch.ar, airbatch.pr, airbatch.lr, airbatch.tr, airbatch.dr]

def extendLine(obj):
	global editor, editorRow, editorCol

	if isinstance(obj, html.LI):
		li = obj
	else:
		li = html.LI(str(obj))
		li.obj = obj

	editorRow.insertBefore(li, editorCol)

	editor.value = ""
	editor.focus()


def clearProposals():
	global editorProposal

	while editorProposal.firstChild:
		editorProposal.removeChild(editorProposal.firstChild)

	editorProposal.style.display = "none"

def checkInput():
	global editor, editorProposal, allowedRecognizers

	editor.disabled = True

	matches = []

	s = editor.value.strip()

	editor.classList.remove("unknown")
	clearProposals()

	if not s:
		return

	for r in allowedRecognizers:
		res = r.recognize(s)
		if res:
			matches.append(res)

	print(matches)

	if matches:
		if len(matches) > 1:
			for res in matches:
				li = html.LI(str(res.obj))
				li.obj = res.obj

				editorProposal.appendChild(li)

			editorProposal.style.display = "block"
		else:
			extendLine(matches[0].obj)
	else:
		editor.classList.add("unknown")

	editor.disabled = False


def selectProposal(e):
	print(e.target.obj)

	extendLine(e.target.obj)
	clearProposals()

editorProposal.bind("click", selectProposal)


def setTimeout(e):
	global editorTimeout

	e.preventDefault()
	e.stopPropagation()

	if editorTimeout:
		window.clearTimeout(editorTimeout)
		editorTimeout = None

	if editor.value[-1] == " ":
		checkInput()
	else:
		editorTimeout = window.setTimeout(checkInput, 500)

editor.bind("keyup", setTimeout)

window.setTimeout(editor.focus, 500)

