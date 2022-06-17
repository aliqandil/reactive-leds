import multiprocessing, threading, asyncio
import time
import hid

class HIDInterface( object ):

	def __init__( self, vid, pid ):
		self.vid = vid
		self.pid = pid
		self.device = None

		self.duplex = multiprocessing.Pipe( duplex = True )
		self.proc   = multiprocessing.Process( target = self.start_interfacing )
		self.proc.start()

		self.fragments_queue = asyncio.Queue()


	async def iter_device_reports( self ):
		loop = asyncio.get_event_loop()
		new_msg   = asyncio.Queue()
		read_pipe = self.duplex[0]

		def queue_msg(): new_msg.put_nowait( read_pipe.recv() )
		loop.add_reader( read_pipe.fileno(), queue_msg )

		while True:
			msg = await new_msg.get()
			if not msg: break
			yield msg

	async def dequeue_device_fragments( self ):
		loop = asyncio.get_event_loop()
		write_pipe  = self.duplex[0]

		while True:
			fragments = await self.fragments_queue.get()
			write_pipe.send( fragments )

	async def send_device_fragments( self, fragments ):
		await self.fragments_queue.put( fragments )


	def start_interfacing( self ):
		while True:
			try:
				self.device = hid.Device( vid = self.vid, pid = self.pid )
			except hid.HIDException as e : print(e, "Retrying in 0.2 seconds..."); time.sleep(0.2)
			else: break

		self.writer_thread = threading.Thread( target = self.hid_writer )
		self.writer_thread.start()

		self.reader_thread = threading.Thread( target = self.hid_reader )
		self.reader_thread.start()


	def hid_reader( self ):
		write_pipe  = self.duplex[1]
		last_report = 0
		while True:

			try:
				start     = time.time()
				keys_in   = self.device.read(64)
				lock_keys = self.device.get_feature_report(1, 2)
				animation = self.device.get_feature_report(204, 3)
				delta     = time.time() - start
			except hid.HIDException: continue # -> Interrupted system call

			write_pipe.send(
				(keys_in, lock_keys, animation, delta)
			)

	def hid_writer( self ):
		read_pipe = self.duplex[1]
		while True:

			fragments = read_pipe.recv()
			for fragment in fragments:
				self.device.send_feature_report( fragment )
