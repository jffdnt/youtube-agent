import requests
import re

channels = ["@MSFTMechanics", "@NateBJones", "@MicrosoftCommunityLearning"]
for c in channels:
    r = requests.get(f"https://www.youtube.com/{c}")
    match = re.search(r'(UC[\w-]{22})', r.text)
    print(f"{c}: {match.group(1) if match else 'Not found'}")
