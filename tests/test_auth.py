# Test core halibot functionality

import time
import util
import halibot
import unittest
import os

class StubModuleFunc(halibot.HalModule):

	def init(self):
		self.called = False

	def function(self, msg):
		self.called = True

	def receive(self, msg):
		if self.hasPermission(msg, "Foo"):
			self.function(msg)

class StubModuleDec(halibot.HalModule):

	def init(self):
		self.called = False

	@halibot.halauth.hasPermission("Foo", reply=True, argnum=0)
	def function(self, msg):
		self.called = True

	def receive(self, msg):
		self.function(msg)

class StubModuleDecFail(halibot.HalModule):

	def init(self):
		self.called = False
		self.tmp = None # fill in during tests

	@halibot.halauth.hasPermission("Foo", reply=True, key="foo")
	def no_msg_key(self, msg):
		self.called = True

	@halibot.halauth.hasPermission("Foo", reply=True, key="msg")
	def not_msg_helper(self, msg=None):
		self.called = True

	def not_msg_entry(self, msg):
		class t:
			origin = "test"
		self.not_msg_helper(msg=t())

	@halibot.halauth.hasPermission("Foo", reply=True, argnum=0)
	def valid(self, msg):
		self.called = True

	def receive(self, msg):
		self.temp(msg)

class TestAuth(util.HalibotTestCase):

	def test_grantperm(self):
		self.bot.auth.perms = []
		self.bot.auth.enabled = False
		self.bot.auth.grantPermission("foo", "bar", "baz")

		self.assertEqual(len(self.bot.auth.perms), 0)

		self.bot.auth.enabled = True

		self.bot.auth.grantPermission("foo", "bar", "baz")
		self.assertEqual(len(self.bot.auth.perms), 1)
		self.assertEqual(self.bot.auth.perms[0][0], "foo")
		self.assertEqual(self.bot.auth.perms[0][1], "bar")
		self.assertEqual(self.bot.auth.perms[0][2], "baz")

	def test_revokeperm(self):
		self.bot.auth.perms = [("foo", "bar", "baz")]
		self.bot.auth.enabled = False

		self.bot.auth.revokePermission("foo", "bar", "baz")
		# Permissions aren't enabled, so we should ignore revocations
		self.assertEqual(len(self.bot.auth.perms), 1)

		self.bot.auth.enabled = True

		self.bot.auth.revokePermission("foo", "bar", "baz")
		self.assertEqual(len(self.bot.auth.perms), 0)

		# This should remain empty, and fail to find the perm to revoke
		self.bot.auth.revokePermission("foo", "bar", "baz")
		self.assertEqual(len(self.bot.auth.perms), 0)

	def test_hasperm_func(self):
		self.bot.auth.enabled = True
		stub = StubModuleFunc(self.bot)
		self.bot.add_instance('stub_mod', stub)

		ri = "test/foobar"
		user = "tester"
		perm = "Foo"
		msg = halibot.Message(body="", origin=ri, identity=user)

		stub.receive(msg)
		self.assertFalse(stub.called)

		self.bot.auth.grantPermission(ri, user, perm)
		stub.receive(msg)
		self.assertTrue(stub.called)

		stub.called = False
		self.bot.auth.revokePermission(ri, user, perm)
		stub.receive(msg)
		self.assertFalse(stub.called)

		# NOTE: This assumes that enabled = allow all perms.
		# Is this really expected behavior?
		stub.called = False
		self.bot.auth.enabled = False
		self.bot.auth.revokePermission(ri, user, perm)
		stub.receive(msg)
		self.assertTrue(stub.called)

	def test_hasperm_dec(self):
		self.bot.auth.enabled = True
		stub = StubModuleDec(self.bot)
		self.bot.add_instance('stub_mod', stub)

		ri = "test/foobar"
		user = "tester"
		perm = "Foo"
		msg = halibot.Message(body="", origin=ri, identity=user)

		stub.receive(msg)
		self.assertFalse(stub.called)

		self.bot.auth.grantPermission(ri, user, perm)
		stub.receive(msg)
		self.assertTrue(stub.called)

		stub.called = False
		self.bot.auth.revokePermission(ri, user, perm)
		stub.receive(msg)
		self.assertFalse(stub.called)

	def test_hasperm_dec_fail(self):
		self.bot.auth.enabled = True
		stub = StubModuleDecFail(self.bot)
		self.bot.add_instance('stub_mod', stub)

		ri = "test/foobar"
		user = "tester"
		perm = "Foo"
		msg_bad = halibot.Message(body="", origin="", identity=user)
		msg_good = halibot.Message(body="", origin=ri, identity=user)

		# Empty origin
		stub.temp = stub.valid
		try:
			stub.receive(msg_bad)
			self.assertTrue(False) # We should catch an Exception here
		except halibot.message.MalformedMsgException:
			pass
		self.assertFalse(stub.called)

		self.bot.auth.grantPermission(ri, user, perm)
		try:
			stub.receive(msg_bad)
			self.assertTrue(False) # We should catch an Exception here
		except halibot.message.MalformedMsgException:
			pass
		self.assertFalse(stub.called)

		stub.called = False
		self.bot.auth.revokePermission(ri, user, perm)
		try:
			stub.receive(msg_bad)
			self.assertTrue(False) # We should catch an Exception here
		except halibot.message.MalformedMsgException:
			pass
		self.assertFalse(stub.called)


		# Not actually a message object, missing identity
		stub.temp = stub.not_msg_entry
		stub.called = False
		try:
			stub.receive(msg_good)
			self.assertTrue(False) # We should catch an Exception here
		except halibot.message.MalformedMsgException:
			pass
		self.assertFalse(stub.called)

		# Bad arg key
		stub.temp = stub.no_msg_key
		stub.called = False
		try:
			stub.receive(msg_good)
			self.assertTrue(False) # We should catch an Exception here
		except KeyError:
			pass
		self.assertFalse(stub.called)


	def test_hasperm_regex(self):
		self.bot.auth.enabled = True
		stub = StubModuleDec(self.bot)
		self.bot.add_instance('stub_mod', stub)

		ri = "test/foobar"
		user = "tester"
		perm = "Foo"
		msg = halibot.Message(body="", origin=ri, identity=user)

		self.bot.auth.grantPermission(".*", user, ".*")
		stub.receive(msg)
		self.assertTrue(stub.called)

	def test_load_perms(self):
		# A bad JSON string should give the user no permissions
		with open("testperms.json", "w") as f:
			f.write("[(\"foo\", \"bar\", \"baz\")]")

		self.bot.auth.load_perms("testperms.json")
		self.assertEqual(len(self.bot.auth.perms), 0)
		self.assertTrue(self.bot.auth.enabled)

		with open("testperms.json", "w") as f:
			f.write("[]")

		self.bot.auth.load_perms("testperms.json")
		self.assertEqual(len(self.bot.auth.perms), 0)

		os.remove("testperms.json")
		self.bot.auth.enabled = False
		self.bot.auth.load_perms("testperms.json")
		self.assertTrue(self.bot.auth.enabled)

	def test_write_perms(self):
		self.bot.auth.enabled = True
		self.bot.auth.path = "testperms.json"
		self.bot.auth.perms = [("foo", "bar", "baz")]
		self.bot.auth.write_perms()

		self.bot.auth.enabled = False
		self.bot.auth.perms = []

		self.bot.auth.load_perms("testperms.json")
		self.assertTrue(self.bot.auth.enabled)
		p = self.bot.auth.perms[0]
		self.assertEqual(p[0], "foo")
		self.assertEqual(p[1], "bar")
		self.assertEqual(p[2], "baz")

		os.remove("testperms.json")



if __name__ == '__main__':
	unittest.main()
