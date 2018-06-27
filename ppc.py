#-*- coding: utf-8 -*-
# Python Parser Combinators

def LIT(c):
	return lambda s: (c, s[len(c):]) if s.startswith(c) else None

def CCL(r):
	return lambda s: (s[0], s[1:]) if s[0] in r else None

def OR(a, b):
	return lambda s: a(s) or b(s) or None

def AND(a, b):
	def fn(a, b, s):
		res1 = a(s)
		if res1 is None:
			return None

		res2 = b(res1[1])
		if res2 is None:
			return None

		return [res1[0], res2[0]], res2[1]

	return lambda s: fn(a, b, s)

def SEQ(*args):
	assert len(args) > 0

	def fn(pl, s):
		ret = []
		for p in pl:
			res = p(s)
			if res is None:
				return None

			ret.append(res[0])
			s = res[1]

		return ret, s

	return lambda s: fn(args, s)

def POS(p):
	def fn(p, s):
		ret = []

		while s:
			res = p(s)
			if res is None:
				break

			ret.append(res[0])
			s = res[1]

		if not ret:
			return None

		return ret, s

	return lambda s: fn(p, s)

def JOIN(p):
	def fn(p, s):
		res = p(s)
		if res is None:
			return None

		return "".join(res[0]), res[1]

	return lambda s: fn(p, s)

par = {}

def CALL(n):
	global par
	return lambda s: par[n](s)

def SYM(n, p):
	global par
	par[n] = p
	return p

num = SYM("num", JOIN(POS(CCL("0123456789"))))
factor = SYM("factor", OR(num, SEQ(LIT("("), CALL("expr"), LIT(")"))))
term = SYM("term", OR(SEQ(factor, LIT("*"), CALL("term")), factor))
expr = SYM("expr", OR(SEQ(term, LIT("+"), CALL("expr")), term))

s = "1337+42*23+5"
print("> %s" % s)

while True:
	s = s or raw_input("> ")
	if not s:
		break

	r = expr(s)
	print("< %r" % r[0] if r else "(parse error)")
	s = None
