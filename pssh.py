from urllib.parse import urljoin
import base64
import json
import requests
import xmlschema

#!/usr/bin/python3 -uB

#xsd = 'http://standards.iso.org/ittf/PubliclyAvailableStandards/MPEG-DASH_schema_files/DASH-MPD.xsd'
#schema = xmlschema.XMLSchema(xsd)
#user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'

def get_pssh_from_data(data: bytes) -> list[bytes]:
  pssh_header = bytes([0x70, 0x73, 0x73, 0x68])
  #print(pssh_header)
  widevine_key_system = bytes([0xED, 0xEF, 0x8B, 0xA9, 0x79, 0xD6, 0x4A, 0xCE, 0xA3, 0xC8, 0x27, 0xDC, 0xD5, 0x1D, 0x21, 0xED])
  #print(widevine_key_system)
  psshs = []
  for count, each in enumerate(data):
    #print(count)
    if data[count:count+4] == pssh_header and \
       data[count+8:count+24] == widevine_key_system:
      size = int.from_bytes(data[count - 4:count], byteorder = 'big', signed = False)
      psshs.append(data[count-4:count+size-4])
  output = list(set(psshs))
  return output

# From https://github.com/axiomatic-systems/Bento4/blob/master/Source/Python/utils/mp4-dash-clone.py
def process_template(template: str, representation_id: str = None, bandwidth: str = None, time: str = None, number: str = None) -> str:
  if representation_id is not None: result = template.replace('$RepresentationID$', representation_id)
  if number is not None:
    nstart = result.find('$Number')
    if nstart >= 0:
      nend = result.find('$', nstart+1)
      if nend >= 0:
        var = result[nstart+1 : nend]
        if 'Number%' in var:
          value = var[6:] % (int(number))
        else:
          value = number
        result = result.replace('$'+var+'$', value)
  if bandwidth is not None:         result = result.replace('$Bandwidth$', bandwidth)
  if time is not None:              result = result.replace('$Time$', time)
  result = result.replace('$$', '$')
  return result

def get_mpd_from_url(xsd, url: str, headers: dict = {}) -> dict:
  body = requests.get(url, headers = headers).text
  #xsd = 'http://standards.iso.org/ittf/PubliclyAvailableStandards/MPEG-DASH_schema_files/DASH-MPD.xsd'
  schema = xmlschema.XMLSchema(xsd)
  return xmlschema.to_dict(body, schema = schema, validation = 'skip', encoding = 'utf-8')

def get_init_urls_from_mpd(url: str, mpd: dict) -> list[str]:
  output = []
  for period in mpd['Period']:
    for adaptation_set in period['AdaptationSet']:
      if 'BaseURL' in period:
        base_urls = [ urljoin(url, x) for x in period['BaseURL'] ]
      else:
        base_urls = [ url ]
      if 'SegmentTemplate' in adaptation_set:
        segment_template = adaptation_set['SegmentTemplate']
      else:
        segment_template = None
      for representation in adaptation_set['Representation']:
        if 'SegmentTemplate' in representation:
            segment_template = representation['SegmentTemplate']
        if segment_template:
          try:
              initialization = process_template(segment_template['@initialization'], representation_id = str(representation['@id']), bandwidth = str(representation['@bandwidth']))
          except:
              initialization = None
        if segment_template:
          for base_url in base_urls:
            output.append(urljoin(base_url, initialization))

        if 'BaseURL' in representation:
          for base_url in base_urls:
            for set_url in representation['BaseURL']:
              output.append(urljoin(base_url, set_url))
  return output

def get_pssh_from_inits_urls(input: list[str], headers) -> list[bytes]:
  return list({ y for x in input for y in get_pssh_from_data(requests.get(x, headers = {**headers, **{'range': 'bytes=0-32768'}}).content) })

def get_pssh_from_url(xsd, url, headers: dict = {}):
  #print(f'url = {url}')
  mpd = get_mpd_from_url(xsd, url, headers)
  #print(mpd)
  inits = get_init_urls_from_mpd(url, mpd)
  #print(inits)
  psshs = get_pssh_from_inits_urls(inits, headers)
  output=[]
  for pssh in psshs:
      pssh=json.dumps(base64.b64encode(pssh).decode(), indent = 2)
      output.append(pssh)
  #psshs = f'{json.dumps(base64.b64encode(pssh).decode() for pssh in psshs, indent = 2)}'
  #return [ base64.b64encode(pssh) for pssh in psshs ]
  return output

# Examples
#get_pssh_from_url('https://bitmovin-a.akamaihd.net/content/art-of-motion_drm/mpds/11331.mpd', {
#  'User-Agent': user_agent,
#})
#get_pssh_from_url('https://orf2ooe-247.mdn.ors.at/orf/orf2ooe/drmqxa-247/manifest.mpd', {
#  'User-Agent': user_agent,
#})
#get_pssh_from_url('https://orf1-247.mdn.ors.at/orf/orf1/drmqxa-247/manifest.mpd', {
#  'User-Agent': user_agent,
#})
