# -*- coding: utf-8 -*-
from browser import document
import airbatch

def insertCode(txt):
	editor = document["editor"]
	start = editor.selectionStart
	txt = editor.value[:start] + txt + " " + editor.value[start:]
	editor.value = txt

def insertObject(event):
	opt = event.target

	print(opt)
	txt = str(opt.obj)

	if " - " in txt:
		insertCode(txt.split(" - ", 1)[0].strip())
	elif " (" in txt:
		insertCode(txt.split(" (", 1)[0].strip())
	else:
		insertCode(txt)

for info in ["aircraft", "pilot", "location"]:
	lst = getattr(airbatch, "demo" + info[0].upper() + info[1:] + "s")

	for obj in lst:
		opt = document.createElement("option")
		opt["value"] = obj.key
		opt.obj = obj
		opt.appendChild(document.createTextNode(str(obj)))
		document[info].appendChild(opt)

	document[info].bind("dblclick", insertObject)

def doParse(event):
	res = airbatch.parse(document["editor"].value)

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

document["btn-parse"].bind("click", doParse)