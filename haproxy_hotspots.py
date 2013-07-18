#/usr/bin/python

'''
  Look through your HAProxy (http) logs for hotspots.

  capture request header Host len 30
  capture request header X-Forwarded-For len 15
  capture request header Cache-Control len 50
  capture request header Pragma len 15
    
'''

import operator

DOMAIN_HITS_THRESHOLD = 5000
CLIENT_HITS_THRESHOLD = 1000

domain_hits = {}
client_hits = {}

log_fh = open('/var/log/haproxy/haproxy.log', 'r')
#log_fh = open('test.log', 'r')
for logline in log_fh:
    lineparts = logline.split()
    extras = logline.split()[17]
    if not extras.startswith("{"):
        continue
    extras = extras.lstrip("{").rstrip("}").split("|")
    domain = extras[0]
    client = extras[1] 
    if not domain in domain_hits.keys():
        domain_hits[domain] = 1
    else:
        domain_hits[domain] += 1
    if not client in client_hits.keys():
        client_hits[client] = 1
    else:
        client_hits[client] += 1

# Remove items below threshold

for domain in domain_hits.keys():
    if domain_hits[domain] < DOMAIN_HITS_THRESHOLD:
        del domain_hits[domain]
    
for client in client_hits.keys():
    if client_hits[client] < CLIENT_HITS_THRESHOLD:
        del client_hits[client]

print sorted(domain_hits.iteritems(), key=operator.itemgetter(1))

#print domain_hits
#print client_hits
