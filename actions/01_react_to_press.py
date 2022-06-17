from reactive_leds import AsyncController
if not AsyncController.instances: exit()
ac = list(AsyncController.instances.values())[0]


import asyncio, random
from colour import Color


@ac.call_on( keys_up = set(ac.keys) - set(range(83, 89)) )
async def a_key_was_pressed( key ):
	#Each LED and KEY object has an asyncio.Lock property.
	#These can be used to make cooporation between multiple callback functions easier!

	#In this case, the lock prevents animation conflicts between multiple calls of this function, making it spam-proof.
	lock = key.leds[0].lock
	if not lock.locked():
		async with lock:

			src = [Color("red"), Color("blue")][random.randint(0,1)]
			dst = Color("white")
			was = key.leds[0].current_rgb or Color("black")

			for led in key.leds: led.current_rgb = src
			await asyncio.sleep( 0.3 )

			for c in src.range_to( dst, 10 ):
				for led in key.leds: led.current_rgb = c
				await asyncio.sleep( 0.01 )

			for c in dst.range_to(was, 10):
				for led in key.leds:
					led.current_rgb = c
				await asyncio.sleep( 0.01 )
