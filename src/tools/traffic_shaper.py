import select, socket, threading

def encode_len(bytes_obj):
	return len(bytes_obj).to_bytes(2, "big")

def decode_len(length):
	return int.from_bytes(length, "big")

def traffic_shaper_listen(traffic_shaper):
	traffic_shaper.listen()

class TrafficShaper:
	"""TrafficShaper: shape UDP traffic into TCP traffic"""
	def __init__(self, udp_host="127.0.0.1", udp_port=51820):
		self.udp_host=udp_host
		self.udp_port=udp_port
		self.tcp_host=glob.CONTROLLER_IP
		self.tcp_port=glob.TRAFFIC_PORT
		self.listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.listen_sock.bind((self.tcp_host, self.tcp_port))

	def __del__(self):
		if self.tcp_sock is not None:
			self.tcp_sock.close()
		if self.udp_sock is not None:
			self.udp_sock.close()
		self.listen_sock.close()

	def start(self):
		self.keep_running = True
		self.listen_thread = threading.Thread(target=traffic_shaper_listen, args=(self,), daemon=True)
		self.listen_thread.start()

	def stop(self):
		self.keep_running = False
		self.listen_thread.join()
		
	def listen(self):
		self.listen_sock.listen(1)
		while self.keep_running:
			try:
				self.tcp_sock, addr = self.listen_sock.accept()
				self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
				self.run()
			except:
				log.info("traffic shaper lost connection to controller")
		log.info("door socket listening thread was interrupted")

	def run(self):
		sel_list = [self.udp_sock, self.tcp_sock]
		try:
			while self.keep_running:
				rready, _, _ = select.select(sel_list, [], [])
				for ready in rready:
					if ready is self.udp_sock:
						if not self.recv_udp():
							break
					else:
						if not self.recv_tcp():
							break
		except ConnectionResetError:
			log.info("traffic shaper connection reset")

	def recv_udp(self):
		msg, addr = self.udp_sock.recvfrom(1024)
		if not msg:
			return False

		msg = encode_len(msg) + msg
		self.tcp_sock.sendall(msg)
		
		return True

	def recv_tcp(self):
		msg = self.tcp_sock.recv(1024)
		if not msg:
			return False
		
		while msg:
			blen, msg = msg[0:2], msg[2:]
			length = decode_len(blen)
			to_send, msg = msg[:length], msg[length:]
			self.udp_sock.sendto(to_send, (self.udp_host, self.udp_port))
		
		return True