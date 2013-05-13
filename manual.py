#!/usr/bin/python

# This is derived from OpenSprinkler Pi's manual_buttons web server.
# I've modified it to suit my needs.

import sys
import os

# RPi.GPIO requires access to /dev/kmem.
# FIXME: check if device is readable first.
if not os.environ.get('SUDO_USER'):
    sudo = '/usr/bin/sudo'
    os.execvp(sudo, [sudo] + sys.argv)

import urlparse
import BaseHTTPServer
import atexit
import RPi.GPIO as gpio

ADDRESS = ''
PORT = 8080

# gpio PIN DEFINES
pin_sr_clk =  4
pin_sr_noe = 17
pin_sr_dat = 21 # NOTE: if you have a RPi rev.2, need to change this to 27
pin_sr_lat = 22

# Stations
stations = {
	'1':"Front Left and Sidewalk",
	'2':"Front Right",
	'3':"Front and Back drip",
	'4':"Back"
}
num_stations = len(stations)

# STATION BITS 
STATIONS_OFF = [0]*num_stations
values = STATIONS_OFF

def setShiftRegister(values):
	print 'D: setShiftRegister: ' + str(values)
	gpio.output(pin_sr_clk, False)
	gpio.output(pin_sr_lat, False)
	for s in range(0, num_stations):
		gpio.output(pin_sr_clk, False)
		gpio.output(pin_sr_dat, values[num_stations-1-s])
		gpio.output(pin_sr_clk, True)
	gpio.output(pin_sr_lat, True)

class SprinklerHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	def do_GET(self):
		global values
		send = self.wfile.write
		self.send_response(200)
		self.send_header('Content-type', 'text/html')
		self.end_headers()
		gohome = '<script>window.location=".";</script>'
		if '?' in self.path:
			parsed = urlparse.parse_qs(urlparse.urlparse(self.path).query)
			s = int(parsed['s'][0])
			v  = int(parsed['v'][0])						
			if s < 0 or s > (num_stations-1):
				send('<script>alert("Wrong value: %s");</script>' % s);
			else:
				if v == 0:
					values[s] = 0
				else:
					values[s] = 1
				setShiftRegister(values)

			send(gohome)
		else:
			send('''<html><head>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=2.0, user-scalable=yes" />
<style><!--
* { font-family: sans; }
.on { background-color: lightgreen; }
.off { background-color: lightgray; }
ul { list-style: none; margin: 0; padding: 0; } li { padding: 0.5em; }
input { width: 6em; height: 4em; font-size: 80%; margin-right: 1em; }
@media handheld, only screen and (max-width: 480px), only screen and (max-device-width: 480px) 
{ 
body { width: auto; min-width: 0px; }
h1 { font-size: 1em; }
}
--></style>
<script>
function go(s,v) { window.location.assign('?s=' + s + '&v=' + v); }
</script></head><body><h1>OpenSprinkler Pi</h1>''')

			send('<ul>\n')
			for i in range(num_stations):
				label = stations.get(str(i+1), 'Station %d' % i)
				if values[i] == 1:
					params = ('on', i, 0, 'Off', label)
				else:
					params = ('off', i, 1, 'On', label)
				b = '<li><input type="button" class="%s" onclick=go(%d,%d) value="Turn %s" /> %s</li>\n' % params
				send(b)
			send('<ul>\n')

def run():
	gpio.cleanup()
	# setup gpio pins to interface with shift register
	gpio.setmode(gpio.BCM)
	gpio.setup(pin_sr_clk, gpio.OUT)
	gpio.setup(pin_sr_noe, gpio.OUT)

	# Disable shift register output
	gpio.output(pin_sr_noe, True)

	gpio.setup(pin_sr_dat, gpio.OUT)
	gpio.setup(pin_sr_lat, gpio.OUT)

	setShiftRegister(values)

	# Enable shift register output
	gpio.output(pin_sr_noe, False)

	# Start web server
	server_address = (ADDRESS, PORT)
	httpd = BaseHTTPServer.HTTPServer(server_address, SprinklerHandler)
	print('OpenSprinkler Pi is running...')
	while True: httpd.handle_request()

def progexit():
	setShiftRegister(STATIONS_OFF)
	gpio.cleanup()

if __name__ == '__main__':
	atexit.register(progexit)
	run()
