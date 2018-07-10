# -*- coding: utf-8 -*-
import airbatch
from browser import document, window, html

editorTimeout = None

editor = document["editor"]
editorCol = document["editor-col"]
editorRow = document["editor-row"]
editorProposal = document["editor-proposal"]

allowedRecognizers = [airbatch.ar, airbatch.pr, airbatch.lr, airbatch.tr, airbatch.dr]

def extendLine(result):
	global editor, editorRow, editorCol

	if isinstance(result, html.LI):
		li = result
	else:
		li = html.LI(str(result))
		li.result = result

	editorRow.insertBefore(li, editorCol)

	editor.value = editor.value[li.result.count:].strip()
	editor.focus()

	if editor.value:
		checkInput()


def clearProposals():
	global editorProposal

	while editorProposal.firstChild:
		editorProposal.removeChild(editorProposal.firstChild)

	editorProposal.style.display = "none"

def checkInput(*args, **kwargs):
	global editor, editorProposal, allowedRecognizers

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

	if matches:
		if len(matches) > 1:
			for res in matches:
				if isinstance(res.obj, list):
					for obj in res.obj:
						li = html.LI(str(obj))
						li.result = res.clone(obj)

						editorProposal.appendChild(li)
				else:
					li = html.LI(str(res.obj))
					li.result = res

					editorProposal.appendChild(li)

			editorProposal.style.display = "block"
		else:
			extendLine(matches[0])
	else:
		editor.classList.add("unknown")

	editor.disabled = False


def selectProposal(e):
	print(e.target.result)

	extendLine(e.target.result)
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

