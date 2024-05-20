# get-token.py
# By Scott C. Hibbard
# 13-May-2024
# Fetches Enphase token
# pass data in command line as json:
# python3 get-token.py '{"email":"<email_address>", "pw":"<password>", "sn":"<serial number>"}'

import json, requests, sys

args = sys.argv[1:]
if len(args) != 1:
    print(f"expecting only 1 argument (got {len(args)})")
    sys.exit(1)
paras = json.loads(args[0])
data = {'user[email]': paras["email"], 'user[password]': paras["pw"]}
response = requests.post('https://enlighten.enphaseenergy.com/login/login.json?', data=data)
response_data = json.loads(response.text)
data = {'session_id': response_data['session_id'], 'serial_num': paras["sn"], 'username': paras["email"]}
response = requests.post('https://entrez.enphaseenergy.com/tokens', json=data)
print(response.text)

