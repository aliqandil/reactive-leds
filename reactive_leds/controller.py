import asyncio, importlib, logging
logger = logging.getLogger(__package__)

from collections import defaultdict
from .interface  import HIDInterface

class KeyboardKey( object ):
	def __init__( self, addr, desc ):
		self.addr = addr
		self.desc = desc
		self.leds = None
		self.lock = asyncio.Lock()

		self.is_pressed = None

	def __str__( self ): return f"<{'In' if self.is_pressed else 'Up'} Key Object {self.addr} ({self.desc})>"

	@staticmethod
	def get_key_desc_from_leds( leds ):

		try: return str(int(leds[1][1]))
		except (IndexError, ValueError): pass

		try:
			desc, dir = leds[0][1].rsplit(' ', 1)
			if dir in ("Right", "Middle", "Left"): return desc
		except ValueError: pass

		return leds[0][1]

class KeyboardLED( object ):
	instances = {}

	def __init__( self, addr, desc, keys ):
		self.addr = addr
		self.desc = desc
		self.keys = keys
		self.lock = asyncio.Lock()

		self.current_rgb = None
		KeyboardLED.instances[addr] = self

	@classmethod
	def update_or_create( cls, addr, desc, keys ):
		if addr in cls.instances:
			self = cls.instances[addr]
			self.keys.extend( keys )
			return self

		return KeyboardLED( addr, desc, keys )


class AsyncController( object ):
	instances = {}
	def __init__( self, vid, pid, loop = None ):
		self.vid  = vid
		self.pid  = pid
		self.interface = HIDInterface( vid, pid )

		self.threaded_loop = False
		self.loop = loop

		if not self.loop:

			try:
				self.loop = asyncio.get_running_loop()
			except RuntimeError:
				self.loop = asyncio.new_event_loop()
				asyncio.set_event_loop( self.loop )
				self.threaded_loop = True
				import threading


		self.mappings = importlib.import_module(f".mappings.V{vid:X}P{pid:X}", __package__)

		self.capslocked = None
		self.numlocked  = None

		self.keys = {} # addr -> Key
		self.leds = {} # addr -> LED

		for key_addr, leds in self.mappings.KEY_TO_LEDS.items():
			key      = self.keys[key_addr] = KeyboardKey( key_addr, KeyboardKey.get_key_desc_from_leds(leds) )
			key.leds = [ KeyboardLED.update_or_create( led_addr, desc, [key] ) for led_addr, desc in leds ] #Order is Left to right, Right to bottom
			for led in key.leds: self.leds[led.addr] = led

		self.on_animation_active = asyncio.Event()
		self.animation_unlocked  = False
		self.refresh_interval    = 0.04
		self.callback_tuples     = {} # callback_id -> keys_down, keys_up, f
		self.filter_cmd_addrs    = {
			"a1": set(self.leds),
			"a2": set(range(1, 14)),
			"a3": set(range(1,107)),
			"a4": set(range(1,100)),
		}

		self.loop.create_task(
			self.listen_on_keystrokes()
		)
		self.loop.create_task(
			self.interface.dequeue_device_fragments()
		)
		self.loop.create_task(
			self.update_led_colors()
		)

		if self.threaded_loop:
			logger.warning("WARNING: AsyncController was created outside of a loop, so it's now running a seperate thread. Be aware of keyboard interrupts!")
			self.threaded_loop = threading.Thread( target = self.loop.run_forever )
			self.threaded_loop.start()

		self.instances[vid, pid] = self

	async def listen_on_keystrokes( self ):
		"""
			List of animations:
			- cc0aff -> 10: Off
			- cc0cff -> 12: Off
			- cc0dff -> 13: Rotating Rainbow
			- cc03ff -> 03: CUSTOMIZABLE
			- cc01ff -> 01: Droplets Waves
			- cc06ff -> 06: Random Twinkles
		"""

		last_addrs_in = set()
		async for keys_in, lock_keys, animation, time_delta in self.interface.iter_device_reports():
			self.capslocked, self.numlocked = [ bool(int(i)) for i in f"{lock_keys[1]:02b}" ]

			if animation[1] == 3:
				self.on_animation_active.set()
				if not self.animation_unlocked:
					await self.enable_custom_animation()
					self.animation_unlocked = True
			else:
				self.on_animation_active.clear()


			if keys_in[0] != 1: continue #Ignoring 02 set for now (fn+top row keys)

			addrs_in = {
				#Detect pressed Special Keys
				*( -addr for addr, state in enumerate(f"{keys_in[1]:07b}", 1) if state == '1' ),

				#Detect pressed Normal Keys
				*( int(i) for i in keys_in[3:9] if i ),

				#Detect overflown Normal keys (for when more than 6 keys are pressed at the same time)
				*( addr for addr, state in enumerate(''.join([ f"{i:08b}"[::-1] for i in keys_in[9:] ])) if state == '1' )
			}

			for addr in addrs_in - last_addrs_in: #Key In
				key = self.keys[addr]
				key.is_pressed = True
				for keys_down, keys_up, func in self.callback_tuples.values():
					if addr in keys_down:
						self.loop.create_task( func(key) )

			for addr in last_addrs_in - addrs_in: #Key Up
				key = self.keys[addr]
				key.is_pressed = False
				for keys_down, keys_up, func in self.callback_tuples.values():
					if addr in keys_up:
						self.loop.create_task( func(key) )

			last_addrs_in = addrs_in

	async def send_request( self, cmd, pairs = [] ):
		fragments = []

		if cmd in self.filter_cmd_addrs:
			filter = self.filter_cmd_addrs[cmd]
			pairs  = [ p for p in pairs if p[0] in filter ]

		while True:
			slice    = pairs[:47]; del pairs[:47]
			fragment = b'\x07' + bytes.fromhex(f'{cmd}{len(slice):02x}') + b'\x00' + b''.join(
				bytes.fromhex(f'{addr:02x}{rgb.hex_l[1:] if hasattr(rgb,"hex_l") else rgb.lower()}') for addr, rgb in slice
			)
			fragment = fragment + b'\x00' * (192 - len(fragment))
			fragments.append( fragment )
			if not pairs: break

		await self.interface.send_device_fragments( fragments )

	async def enable_custom_animation(  self ): await self.send_request('b2')
	async def disable_custom_animation( self ): await self.send_request('b1')

	async def update_led_colors( self ):

		last_request = defaultdict( lambda: None ) #addr -> rgb
		while True:
			if not self.on_animation_active.is_set():
				await self.on_animation_active.wait() #Keeping expensive loop hops minimal

			pairs = []
			for addr, led in self.leds.items():
				rgb = led.current_rgb
				if not rgb: continue

				#Not necessary since `send_request` will handle color objects this, but potentially more efficient.
				if hasattr(rgb,'hex_l'): rgb = rgb.hex_l[1:]

				if last_request[addr] != rgb:
					pairs.append( (addr, rgb) )
					last_request[addr] = rgb

			await asyncio.gather(
				*(
					[asyncio.sleep( self.refresh_interval )] +
					([self.send_request( 'a1', pairs )] if pairs else [])
				)
			)


	def call_on( self, keys_down = None, keys_up = None ):

		if isinstance(keys_up, int):   keys_up   = {keys_up}
		if isinstance(keys_down, int): keys_down = {keys_down}

		if keys_down is None and keys_up is None:
			keys_down = set(self.keys)
			keys_up   = set(self.keys)
		else:
			keys_down = set(keys_down or '')
			keys_up   = set(keys_up   or '')

		def decorator( f ):
			if not hasattr(f, '_listening_on_keystrokes'):
				f._listening_on_keystrokes = set()

			callback_id = max(self.callback_tuples or (0,0)) + 1
			self.callback_tuples[callback_id] = keys_down, keys_up, f
			f._listening_on_keystrokes.add( callback_id )
			return f

		return decorator



#
