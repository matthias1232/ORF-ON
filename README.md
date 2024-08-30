# ORF ON Austria for Kodi/TVHeadend
 ORF ON for TVHeadend and any other Players supporting ffmpeg pipes

This Tool creates a m3u8 Playlist for ORF ON, working with TVHeadend, tvheadend will execute the script and get an pipe as return to play the Stream.
You need a working device.wvd file for the Decryption, otherwhise you wont see any Stream!

Note that ORF also uses GeoBlocking. If you request the file with an IP Address from outsite Austria or an VPN it could probably not work because of that reason.

You need the following Python Packages:

	json
	urllib
	base64
	requests
	xmlschema
	time
	os
	stat
	pywidevine

 Also ffmpeg needs to be installed on your System

Before the first Run of the Script you need to edit the stream.py file and change the Settings:

	#####config part of script#####
	
	device_wvd = "/opt/device.wvd" #(I cannot give any support how to obtain this wvd file")
	playpath = "/var/www/html" #(The Location, where the playlist and stream files will be exported for Tvheadend, TVHeadend needs write Permissions to the temp Folder, in this example to /var/www/html/temp)
	player = "/opt/N_m3u8DL-RE_Beta_linux-arm64/N_m3u8DL-RE" #(x64 or arm64 CPU, also dont forget to run the Command "chmod +x" command for the player)
	licence_url = "https://drm.ors.at/acquire-license/widevine?BrandGuid=XXXXXXXXXXXXX&userToken="
	
	######

Obtaining the License URL with BrandGuid:
Open ORF ON with Google Chrome and Login with your User and while starting a Livestream, log the Network Traffic with google Chrome and search for "wide", you will see the URL for the License Requests:
![image](https://github.com/user-attachments/assets/8d564d7b-e264-4f28-b423-359ee14602ec)


After you configured all settings run the Script:

	chmod +x /opt/stream.py
	/opt/stream.py

Create a Cronjob which executes this script every hour:

	*/59 * * * * /opt/stream.py >/dev/null 2>&1


In TVHeadend add the Playlist

	file:////var/www/html/orfon.m3u8
 
![image](https://github.com/user-attachments/assets/78fcc4d6-8555-4069-9e6d-62bac6b2a740)

After saving everything you should be able to see all Services in TVHeadend:
![image](https://github.com/user-attachments/assets/0ceea276-7cbc-4699-92dc-794bdd13f26f)

