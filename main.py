import os
import subprocess, datetime, pytz, pymongo
from time import sleep

# define variables
DB_USER = os.environ['DB_USER']
DB_PASSWORD = os.environ['DB_PASSWORD']
loop_count = 0
device_connected = False
CST = pytz.timezone('US/Central')
dt = datetime.datetime.now(tz=CST).ctime()
BLACKLIST_IPS = ['', ['31', '13'], ['157', '240'], ['74', '201'], ['127', '0']]
client = pymongo.MongoClient(f"mongodb+srv://{DB_USER}:{DB_PASSWORD}3@cluster0.i31qn.mongodb.net/?retryWrites=true&w=majority")
db = client.Pinger.data

def is_blacklisted(ip_address):
    return ip_address.split('.')[:2] in BLACKLIST_IPS

# ask regular info
tester_name = input("Whats your name? ").upper()
location_info = input("is your headset NA / APJ / EU?").upper()


# check adb devices to see if the headset is connected
print(f'\n---\nOkay, connect the Quest wired and click Allow when it asks you.\n\n'
      f'Also also, make sure this computer is on the SAME network as the quest.')
while not device_connected:
    p = subprocess.Popen("adb devices", shell=True, stdout=subprocess.PIPE).stdout.readlines()[1]
    if b'\tdevice\n' in p:
        device_connected = True

print('I found it, thank you. wait a bit..')
# once it's connected do adb tcpip 5555
subprocess.Popen("adb tcpip 5555", shell=True)
sleep(3)

print('Figuring out your IP. This takes forever..')
# then get the ip addy adb connect
quest_ip = subprocess.Popen('adb shell ip a | grep "inet 192"', shell=True, stdout=subprocess.PIPE).stdout.readlines()[0]
quest_ip = quest_ip.split()[1].split(b'/')[0].decode('utf-8')

# connect wireless tell it to disconnect headset
subprocess.Popen(f'adb connect {quest_ip}:5555', shell=True)
print("Disconnect the quest now, I got it connected wirelessly.")

while True:
    whois = []
    pings = []

    # grab raw output from NETSTAT and cleanup raw
    connected_ips = subprocess.Popen("adb shell netstat -tn | grep ESTABLISHED",
                                     shell=True, stdout=subprocess.PIPE).stdout.readlines()
    # split all lines into columns, remove ipv6S and remove duplicates
    connected_ips = set([x[4].split(b':')[0].decode('utf-8') for x in [x for x in [x.split() for x in connected_ips] if x[0] == b'tcp']])

    # remove known IPs
    connected_ips = [x for x in connected_ips if not is_blacklisted(x)]

    # get all the Net Name for the whois data
    for ip in connected_ips:
        p = subprocess.Popen(f'whois {ip} | grep NetName', shell=True, stdout=subprocess.PIPE).stdout.readlines()[0]
        if p == b'\n':
            whois.append('NULL')
        else:
            whois.append(p.split()[-1].decode('utf-8'))

    print(f'found the following connections: {whois}')

    # ping all the IPs
    for ip in connected_ips:
        print(f'pinging ip {ip}')
        p = subprocess.Popen(f"adb shell ping -c 10 {ip}", shell=True, stdout=subprocess.PIPE).stdout.readlines()[-1]
        if p == b'\n':
            pings.append(0)
        else:
            pings.append(p.split(b'=')[-1].split(b'/')[1].decode('utf-8'))

    # build the dict
    db_data = []
    z = list(zip(connected_ips, whois, pings))
    for x in z:
        db_data.append({'tester_name':tester_name, 'location_info': location_info, 'loop_count': loop_count,
                        'ip': x[0], 'name': x[1], 'ping': float(x[2])})

    # write to the db
    if z:
        db.insert_many(db_data)
        print(f'dumped loop {loop_count} with payload: {db_data} into db')

    # take a break
    sleep(240)
    print(f'waiting 4 mintes to re-ping\n\n')
    loop_count += 1
