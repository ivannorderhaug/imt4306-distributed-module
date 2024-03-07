import json
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from twisted.internet.task import LoopingCall
from random import randint
import netifaces
import time


class Peer(DatagramProtocol):
    def __init__(self):
        """
        Initialize the client with the given address and port for the discovery server. If no address and port are given, the client will not connect to a discovery server.
        """
        self.peers = set()
        self.handlers = {
            "hello": self.handle_hello,
            "bye": self.handle_bye,
            "ping": self.handle_ping,
            "pong": self.handle_pong,
        }
        self.addr = next((netifaces.ifaddresses(interface)[netifaces.AF_INET][0]['addr'] for interface in netifaces.interfaces()[1:] if netifaces.AF_INET in netifaces.ifaddresses(interface)), None)
        #self.port = randint(49152, 65535)
        self.port = randint(1200, 1299)
        self.lc_ping = LoopingCall(self.send_ping)
        reactor.callInThread(self.lc_ping.start, 1)
        self.last_pings = {}
        self.start_time = time.time()
        self.current_time = 0
        self.messages_count = 0
        self.latency_sum = 0
        self.throughput = 0

    def datagramReceived(self, data, addr):
        """
        Method called when a datagram is received.
        """
        data = data.decode('utf-8')
        if not data:
            return
        
        try:
            for line in data.splitlines():
                line = line.strip()
                print(line)
                msgtype = json.loads(line)['msgtype']
                if msgtype in self.handlers:
                    self.handlers[msgtype](line)
        except json.JSONDecodeError:
            print(data)
        except KeyError:
            print("Invalid message type received.")

    def handle_hello(self, line):
        """
        Method to handle a hello message received from a peer.
        """
        hello = json.loads(line)
        peer = (hello['addr'], hello['port'])
        self.messages_count += 1
        if peer not in self.peers:
            self.peers.add(peer)
            self.send_hello(peer, include_peers=True)
            self.messages_count = 0
            self.latency_sum = 0
            self.start_time = time.time()
        if 'peers' in hello:
            for peer in hello['peers']:
                if (peer['addr'], peer['port']) != (self.addr, self.port):
                    self.send_hello((peer['addr'], peer['port']))
    
    def send_hello(self, addr, include_peers=False):
        """
        Method to send a hello message to a peer.
        """
        if addr == (self.addr, self.port):
            return

        hello = {
            'addr': self.addr,
            'port': self.port,
            'msgtype': 'hello',
        }
        
        if include_peers:
            peers = []
            for peer in self.peers:
                if peer != addr:
                    peers.append({'addr': peer[0], 'port': peer[1]})
            hello['peers'] = peers

        hello = json.dumps(hello)
        hello = hello.encode('utf-8')
        self.transport.write(hello, addr)

    def send_bye(self, addr):
        """
        Method to send a bye message to a peer.
        """
        bye = json.dumps({'addr': self.addr, 'port': self.port, 'msgtype': 'bye'})
        bye = bye.encode('utf-8')
        self.transport.write(bye, addr)
    
    def handle_bye(self, line):
        """
        Method to handle a bye message from a peer.
        """
        bye = json.loads(line)
        self.peers.remove((bye['addr'], bye['port']))

    def send_ping(self):
        """
        Method to send a ping message to all online peers.
        """
        self.current_time = time.time()
        ping = json.dumps({'addr': self.addr, 'port': self.port, 'msgtype': 'ping', 'timestamp': self.current_time})
        ping = ping.encode('utf-8')
        for peer in self.peers.copy():
            self.transport.write(ping, peer)
            if peer in self.last_pings and time.time() - self.last_pings[peer] > 10:
                print(f"No response from {peer}. It appears to have gone offline.")
                self.peers.remove(peer)
                del self.last_pings[peer]
    
    def handle_ping(self, line):
        """
        Method to handle a ping message from a peer.
        """
        ping = json.loads(line)
        pong_timestamp = time.time()
        latency = pong_timestamp - ping['timestamp']
        self.latency_sum += latency
        self.messages_count += 1
        self.get_throughput()
        self.send_pong((ping['addr'], ping['port']), pong_timestamp)
    
    def send_pong(self, addr, pong_timestamp):
        """
        Method to send a pong message to a peer.
        """
        pong = json.dumps({'addr': self.addr, 'port': self.port, 'msgtype': 'pong', 'timestamp': pong_timestamp})
        pong = pong.encode('utf-8')
        self.transport.write(pong, addr)

    def handle_pong(self, line):
        """
        Method to handle a pong message from a peer.
        """
        pong = json.loads(line)
        timestamp = pong['timestamp']
        latency = time.time() - timestamp
        self.latency_sum += latency
        self.messages_count += 1
        self.get_throughput()
        self.last_pings[(pong['addr'], pong['port'])] = timestamp

    def get_throughput(self):
        """
        Method to get the throughput of the client.
        """
        if self.start_time is not None:
            current_time = time.time()
            elapsed_time = current_time - self.start_time
            self.throughput = self.messages_count / elapsed_time
        
    def stop(self):
        """
        Method to stop the client.
        """
        for peer in self.peers:
            self.send_bye(peer)

        self.lc_ping.stop()
        self.transport.stopListening()
        reactor.stop()
    
    def add_handler(self, command, callback):
        """
        Method to add a new command to the client.
        """
        self.handlers[command] = callback
    
    def remove_handler(self, command):
        """
        Method to remove a command from the client.
        """
        del self.handlers[command]
