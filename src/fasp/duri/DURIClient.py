import requests
import json
import sys
import getopt
import datetime

class DURIClient:
	'''Basic DRS functions, no bundle handling'''    

	def __init__ (self, clearing_house_url, debug=False):
		self.clearing_house_url = clearing_house_url
		self.debug = debug
	
	def resolveTST(self, passport_path, list_max_consents=5):
		'''print details of a Passport ot Task Specific Token'''
		with open (passport_path) as pfile:
			passport = pfile.read()
		body ={"ga4gh_passport":passport,
			"tracking":"IMF: checking my tokens for validity"}
		if self.debug:
			print(body)

	
		resp = requests.post(self.clearing_house_url, json=body)
		ch_resp = resp.json()
		if 'msg' in ch_resp:
			if self.debug:
				print(ch_resp['msg'])
			return False
		else:
			effective = ch_resp['info']['eff']
			expiration = ch_resp['info']['exp']
			effective = ch_resp['info']['eff']
			expString = datetime.datetime.fromtimestamp(expiration)
			print(f"Consents available in valid TST {passport_path}")
			if self.debug:
				print(f"Effective: {datetime.datetime.fromtimestamp(effective)}")
				print(f"Expires: {datetime.datetime.fromtimestamp(expiration)}")


			assertions = ch_resp['dbgap-consents']
			listed_consents = 0
			for a in assertions:
				print(a['phs_id'], a['consent_group'])
				listed_consents +=1
				if listed_consents >= list_max_consents:
					print(f"first {list_max_consents} of {len(ch_resp['dbgap-consents'])} consents listed")
					break
			return expString
			
def main(argv):

	clearing_house = DURIClient('https://auth.ncbi.nlm.nih.gov/clr/v1/dbgap/consents/')
	tok = '/Users/forei/Downloads/task-specific-token.txt'
	clearing_house.resolveTST(tok)
	
	try:
		opts, args = getopt.getopt(argv, "ht", ["help", "token"])
	except getopt.GetoptError:
		usage()
		sys.exit(2)
	for opt, arg in opts:
	    if opt in ("-h", "--help"):
	        usage()
	        sys.exit()
	    elif opt in ("-t", "--token"):
	        tok = arg
	        print(f"token argument was {tok}")
	        
	clearing_house.resolveTST(tok)


			
if __name__ == "__main__":
    main(sys.argv[1:])