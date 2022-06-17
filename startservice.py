###
##
## Start Service
##
###

import asyncio
loop = asyncio.new_event_loop()
asyncio.set_event_loop( loop )


from reactive_leds import AsyncController
ac = AsyncController( vid = 0x048D, pid = 0xC968, loop = loop )


import pathlib, importlib, types
for action in sorted(pathlib.Path('actions').iterdir()):
	if action.name.endswith(".py"):
		package = action.name.rsplit(".",1)[0]

		loader = importlib.machinery.SourceFileLoader( package, str(action) )
		loader.exec_module( types.ModuleType(loader.name) )


loop.run_forever()
