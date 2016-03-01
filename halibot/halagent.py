from .halobject import HalObject

class HalAgent(HalObject):

	def dispatch(self, msg):
		# TODO: Optimize this
		links = self._get_links("default") + self._get_links(self.config.get("name", None))
		self.send_to(msg, links)

	def connect(self, to):
		# FIXME Don't modify the config like this?
		if 'out' in self.config:
			self.config['out'].append(to.name)
		else:
			self.config['out'] = [ to.name ]
