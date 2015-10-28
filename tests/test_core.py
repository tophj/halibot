# Test core halibot functionality

import time
import util
import halibot
import unittest

class StubModule(halibot.HalModule):
	inited = False
	received = []

	def init(self):
		self.inited = True

	def receive(self, msg):
		self.received.append(msg)

class StubAgent(halibot.HalAgent):
	inited = False

	def init(self):
		self.inited = True

# TODO remove and use actual message builder/constructor
def make_test_msg(body):
	return {
		'body': body,
	}

class TestCore(util.HalibotTestCase):

	def test_add_module(self):
		stub = StubModule(self.bot)
		self.bot.add_module_instance('stub_mod', stub)

		self.assertTrue(stub.inited)
		self.assertEqual(stub, self.bot.get_object('stub_mod'))

	def test_add_agent(self):
		stub = StubAgent(self.bot)
		self.bot.add_agent_instance('stub_agent', stub)

		self.assertTrue(stub.inited)
		self.assertEqual(stub, self.bot.get_object('stub_agent'))

	def test_send_recv(self):
		agent = StubAgent(self.bot)
		mod = StubModule(self.bot)
		self.bot.add_agent_instance('stub_agent', agent)
		self.bot.add_module_instance('stub_mod', mod)

		foo = make_test_msg('foo')
		bar = make_test_msg('bar')
		baz = make_test_msg('baz')

		agent.connect(mod)
		agent.send(foo)
		agent.send_to(bar, [ 'stub_mod' ])
		agent.send(baz)

		# TODO do something sensible here
		timeout = 10
		increment = .1
		while timeout > 0 and len(mod.received) != 3:
			time.sleep(increment)
			timeout -= increment

		self.assertEqual(3, len(mod.received))
		self.assertEqual(foo, mod.received[0])
		self.assertEqual(bar, mod.received[1])
		self.assertEqual(baz, mod.received[2])

if __name__ == '__main__':
	unittest.main()
