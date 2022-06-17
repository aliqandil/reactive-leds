from reactive_leds import AsyncController
if not AsyncController.instances: exit()
ac = list(AsyncController.instances.values())[0]

#Base Color
from colour import Color
for led in ac.leds.values(): led.current_rgb = Color('black') #Or "000000" if you don't want to use the `colour` module.
