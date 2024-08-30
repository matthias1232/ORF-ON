#!/usr/bin/env python3

import json
from urllib.parse import urljoin
import urllib.request
import base64
import requests
import xmlschema
import time
import os
import stat
from pywidevine.cdm import Cdm
from pywidevine.device import Device
from pywidevine.pssh import PSSH
from pssh import *

#####config part of script#####

device_wvd = "/opt/device.wvd"
playpath = "/var/www/html"
player = "/opt/N_m3u8DL-RE_Beta_linux-arm64/N_m3u8DL-RE"
licence_url = "https://drm.ors.at/acquire-license/widevine?BrandGuid=XXXXXXXXXX&userToken="

######



playlist=[]
playlist.append("#EXTM3U")


##EXTINF:0001 tvg-id="SRF1.ch" tvg-chno="1" group-title="German" tvg-logo="https://www.teleboy.ch/assets/stations/303/icon320_dark.png", SRF 1

#xsd = 'http://standards.iso.org/ittf/PubliclyAvailableStandards/MPEG-DASH_schema_files/DASH-MPD.xsd'
#schema = xmlschema.XMLSchema(xsd)
user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'

channels=[]

channels.append({'url': 'https://api-tvthek.orf.at/api/v4.3/timeshift/channel/1180/sources' , 'name': 'ORF1'})
channels.append({'url': 'https://api-tvthek.orf.at/api/v4.3/timeshift/channel/1181/sources', 'name': 'ORF2'})
channels.append({'url': 'https://api-tvthek.orf.at/api/v4.3/timeshift/channel/3026625/sources', 'name': 'ORF3'})
channels.append({'url': 'https://api-tvthek.orf.at/api/v4.3/timeshift/channel/76464/sources', 'name': 'ORF Sport +'})
channels.append({'url': 'https://api-tvthek.orf.at/api/v4.3/timeshift/channel/8089706/sources', 'name': 'ORF Kids'})
channels.append({'url': 'https://api-tvthek.orf.at/api/v4.3/timeshift/channel/5274879/sources', 'name': 'ORF2 O'})
channels.append({'url': 'https://api-tvthek.orf.at/api/v4.3/timeshift/channel/76473/sources', 'name': 'ORF2 B'})
channels.append({'url': 'https://api-tvthek.orf.at/api/v4.3/timeshift/channel/80555/sources', 'name': 'ORF2 K'})
channels.append({'url': 'https://api-tvthek.orf.at/api/v4.3/timeshift/channel/5274647/sources', 'name': 'ORF2 N'})
channels.append({'url': 'https://api-tvthek.orf.at/api/v4.3/timeshift/channel/5274881/sources', 'name': 'ORF2 S'})
channels.append({'url': 'https://api-tvthek.orf.at/api/v4.3/timeshift/channel/3299907/sources', 'name': 'ORF2 STMK'})
channels.append({'url': 'https://api-tvthek.orf.at/api/v4.3/timeshift/channel/4631653/sources', 'name': 'ORF2 T'})
channels.append({'url': 'https://api-tvthek.orf.at/api/v4.3/timeshift/channel/5274895/sources', 'name': 'ORF2 V'})
channels.append({'url': 'https://api-tvthek.orf.at/api/v4.3/timeshift/channel/3299861/sources', 'name': 'ORF2 W'})

chno = 1
for channel in channels:
    #time.sleep(5)
    #print(channel['url'])#
    with urllib.request.urlopen(channel['url']) as url:
        channeldata = json.load(url)
    #print(channeldata)
    try:
        mpdfile = channeldata['sources']['dash']['src']
        mpdfile, sep, tail = mpdfile.partition('.mpd')
        mpdfile = mpdfile + sep
        #print(mpdfile)
        psshs = get_pssh_from_url('http://standards.iso.org/ittf/PubliclyAvailableStandards/MPEG-DASH_schema_files/DASH-MPD.xsd', mpdfile, {
          'User-Agent': user_agent,
        })
    except:
        psshs = []
    #print(psshs)
    keys=[]
    for pssh in psshs:



        # prepare pssh
        pssh = PSSH(pssh)
        # load device
        device = Device.load(device_wvd)

        # load cdm
        cdm = Cdm.from_device(device)

        # open cdm session
        session_id = cdm.open()

        # get license challenge
        challenge = cdm.get_license_challenge(session_id, pssh)

        # send license challenge (assuming a generic license server SDK with no API front)
        licence = requests.post(licence_url + channeldata['drm_token'], data=challenge)
        licence.raise_for_status()

        # parse license challenge
        cdm.parse_license(session_id, licence.content)

        # print keys
        count = 0
        for key in cdm.get_keys(session_id):
            if count == 1:
                keys.append(f"{key.kid.hex}:{key.key.hex()}")
                count = count + 1
            else:
               count = count + 1
               continue
        # close session, disposes of session data
        cdm.close(session_id)

    #print(channel['name'])
    #print(psshs)
    #print(keys)
    keystring=""
    for key in keys:
        keystring = keystring + " --key " + key
    playlist.append(f'#EXTINF:0001 tvg-id="{channel["name"]}" tvg-name="{channel["name"]}" tvg-chno="{chno}" group-title="Austria" tvg-logo="", {channel["name"]}')
    playlist.append(f'pipe://{playpath}/orfon-{chno}.sh')


    stream_sh = []
    stream_sh.append(f'#!/bin/sh')
    stream_sh.append(f'#rm {playpath}/temp/{chno}/*.ts')
    stream_sh.append(f'#rm {playpath}/temp/{chno}/*.m3u8')
    stream_sh.append(f'rm {playpath}/temp/{chno} -rf')
    stream_sh.append(f'mkdir {playpath}/temp/{chno} -p')
    stream_sh.append(f'export RE_LIVE_PIPE_OPTIONS="-loglevel fatal -c:a copy -c:v copy -preset ultrafast -tune zerolatency -mpegts_flags system_b -f mpegts pipe:2"')
    stream_sh.append(f'{player} -mt --thread-count 5 --download-retry-count 2 --binary-merge --header "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36" --header "Referer: https://on.orf.at/" --log-level off --no-date-info --no-log True{keystring} {mpdfile} --del-after-done true --mp4-real-time-decryption true --live-keep-segments false --live-real-time-merge true --live-pipe-mux true --auto-select --tmp-dir {playpath}/temp/{chno}/temp --save-dir {playpath}/temp/{chno} --save-name temp --live-take-count 3 2>&1 >/dev/null')
    stream_sh.append(f'pid=$!')
    stream_sh.append(f'# If this script is killed, kill the process.')
    stream_sh.append(f'#trap "kill $pid 2> /dev/null" EXIT')
    stream_sh.append(f'# While process is running...')
    stream_sh.append(f'while kill -0 $pid 2> /dev/null; do')
    stream_sh.append('     #find ' + playpath + '/temp/' + str(chno) + ' -mmin +3 -type f -exec rm -fv {} \;')
    stream_sh.append(f'     sleep 20')
    stream_sh.append(f'done')
    stream_sh.append(f'# Disable the trap on a normal exit.')

    stream_sh_filename=f'{playpath}/orfon-{chno}.sh'
    with open(stream_sh_filename, 'w') as f:
        for line in stream_sh:
            f.write(f"{line}\n")

    st = os.stat(stream_sh_filename)
    os.chmod(stream_sh_filename, st.st_mode | stat.S_IEXEC)

    chno = chno + 1

#print(playlist)

with open(f'{playpath}/orfon.m3u8', 'w') as f:
    for line in playlist:
        f.write(f"{line}\n")


os.system(f'chown -R 777 {playpath}')
os.system(f'chmod +x {playpath}/orfon-*.sh')
print(f"Playlist Exported to {playpath}/orfon.m3u8")
