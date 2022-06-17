from reactive_leds import AsyncController
if not AsyncController.instances: exit()
ac = list(AsyncController.instances.values())[0]


import asyncio
from colour import Color
from random import randint

lock = asyncio.Lock()
rctrl, lctrl = ac.keys[-3], ac.keys[-7]
ralt,  lalt  = ac.keys[-1], ac.keys[-5]

@ac.call_on( keys_down = -3 ) #On Right CTRL down
async def left_ctrl_down_first( key ):
	if not lctrl.is_pressed: return
	if not lock.locked():
		async with lock:
			await shift_colors_around( "a3" ) #Vents


@ac.call_on( keys_down = -7 ) #On Left CTRL down
async def right_ctrl_down_first( key ):
	if not rctrl.is_pressed: return

	if not lock.locked():
		async with lock:
			await shift_colors_around( "a4" ) #Neon



async def shift_colors_around( group ):
	addrs = ac.filter_cmd_addrs[group]
	delta = 0.01 #for both time and color changes! why not!

	color = Color(f"#{randint(0,255):02X}{randint(0,255):02X}{randint(0,255):02X}")
	color.luminance = 0.5

	while rctrl.is_pressed or lctrl.is_pressed:

		await ac.send_request(group, [
			(addr, color) for addr in addrs
		])

		if not rctrl.is_pressed:
			color.luminance = max(delta, color.luminance - delta)

		if not lctrl.is_pressed:
			color.luminance = min(1,     color.luminance + delta)


		if ralt.is_pressed:
			color.saturation = max(delta, color.saturation - delta)

		if lalt.is_pressed:
			color.saturation = min(1,     color.saturation + delta)

		await asyncio.sleep( delta )












#
