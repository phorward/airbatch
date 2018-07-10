#-*- coding: utf-8 -*-
import datetime


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
		return ">%s< => %s" % (self.token, self.obj or "None")


class Recognizer:
	"""
	Basic recognizer. It recognizes a token from the input stream and disregards whitespace
	and other delimiters.
	"""
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




