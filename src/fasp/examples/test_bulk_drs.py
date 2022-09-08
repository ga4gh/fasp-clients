from fasp.loc import DRSClient
import json

# reuires the StarerKit DRS running 

drsClient = DRSClient("http://localhost:5000")

drs_ids = [
"8e18bfb64168994489bc9e7fda0acd4f",
"ba094cae0da59f27ea82a8a802be34cd",
"01b0fe13b5c4de28a4ff5a7ee3c15773",
"156f8e135472a6bc7f481c11da6a9372",
"336854e9e2cd32476efed80508e522ab",
"4db2e371cf5f5b4257120f26736f6a1d",
"77b0f3d65271c4a0064ff7760828dd92", 
"07d36706f15c3af1f1ad1dd595eca188",
"b60e59cc6b46ed04a3ede78d8c75a6ce",
"e2d03ee77bc4a7786bf6855da96dcb86",
"2405a382375763292ea903a6a658ce95",
"00be9e467ed3986cb2b2b1e2d157a2df",
"ba094cae0da59f27ea82a8a802be34cd",
"d5d4dc9bc29d993e5cc057c6c5a05939",
"9c6ad5209da53a3eeab831445b3c7dc2",
"f4e33a5535b43f8d3c3baf9ce05893ad",
"90dc98385d4523b6967299d0b3d0d1e2",
"f684f723102fc3b20a70ce132ec51ab7",
"c2ddf71411a1afa4e68a132258d70be7"
]

print (f"Sending {len(drs_ids)} ids to server")
resp = drsClient.get_objects(drs_ids)
print ("Response summary")
print(json.dumps(resp['summary'], indent=3))

for r in resp['resolved_drs_object']:
	print(r['mime_type'])
	for a in r['access_methods']:
		print(a['type'], a['region'])
	
triplicate_drs_ids = [
"8e18bfb64168994489bc9e7fda0acd4f",
"8e18bfb64168994489bc9e7fda0acd4f",
"8e18bfb64168994489bc9e7fda0acd4f"]


print (f"\nTesting same drs id multiple times in same request")
print (f"Sending {len(triplicate_drs_ids)} ids to server")
resp = drsClient.get_objects(triplicate_drs_ids)
print ("Response summary")
print(json.dumps(resp['summary'], indent=3))
print(f"Count of items in response: {len(resp['resolved_drs_object'])}")