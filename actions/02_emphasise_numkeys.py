from reactive_leds import AsyncController
if not AsyncController.instances: exit()
ac = list(AsyncController.instances.values())[0]


import asyncio
from colour import Color

@ac.call_on( keys_up = 83 )
async def numlock_key_released( key ):

	lock = key.lock
	if not lock.locked():
		async with lock:

			steps       = 30
			delta       = 0.01
			color_range = list(Color("white").range_to(Color("#000000"), steps))
			for i in range(len(color_range)):

				for addr in range(89, 100):
					for pos, led in enumerate(ac.keys[addr].leds):
						led.current_rgb = color_range[ i if bool(pos) == ac.numlocked else steps-1-i ]

				await asyncio.sleep(delta)

			for addr in range(83, 89):
				key = ac.keys[addr]
				for led in key.leds:
					led.current_rgb = Color("green") if ac.numlocked else Color("red")
