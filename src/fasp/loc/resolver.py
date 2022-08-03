import requests
import json

class resolver():
	def __init__(self, compactIdentifier):
		self.compactIdentifier = compactIdentifier
		self.drs_extension = "/ga4gh/drs/v1/objects/"
		self.guid = self.compactIdentifier.split("drs://")[1]
		self.prefix = self.guid.split(":")[0]

	def identifiers_resolution(self):
		# check the cache for our prefix. If it's not there then we must resolve and cache
		with open("./data/resolution_cache.json", "r") as c:
			cache = json.load(c)
			if self.prefix in cache:
				return cache[self.prefix]

		# make request to identifers.org to resolve prefix
		r = requests.get("https://resolver.api.identifiers.org/" + self.guid)

		if r.status_code == 200:
			resolved_home_URL = r.json()["payload"]["resolvedResources"][0]["resourceHomeUrl"]
			drs_resolution = resolved_home_URL + self.drs_extension
			cache[self.prefix] = drs_resolution

			with open("./data/resolution_cache.json", "w+") as c:
				print("we are caching the resolution to ./data/resolution_cache.json")
				json.dump(cache, c)

			return drs_resolution

		else:
			print(r.status_code)
			print(r.text)
			return r.text
