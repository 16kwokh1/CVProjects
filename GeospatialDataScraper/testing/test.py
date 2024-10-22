from email.headerregistry import Address
from cv2 import add
from numpy import outer
import geojson
import os
import json

db = []

for file in os.listdir():
    if file.endswith(".geojson"):
        with open(file, encoding="utf8") as f:
            gj = geojson.load(f)
            listofGeojson = gj['features']
            for i in listofGeojson:
                
                coords = i["geometry"]["coordinates"]
                data = i["properties"]
                data["YCoords"] = str(coords[0])
                data["XCoords"] = str(coords[1])

                dataset = data["Dataset"]
                if dataset == "Monthly Digests - Buildings Department - Table 5.3 New buildings for which plans have been approved":
                    data["Dataset"] = "Table 1"
                elif dataset == "Monthly Digests - Buildings Department - Table 5.4 New buildings for which consent to commence works has been given":
                    data["Dataset"] = "Table 2"
                elif dataset == "Monthly Digests - Buildings Department - Table 5.5 New buildings for which notification of commencement of general building and superstructure works has been received":
                    data["Dataset"] = "Table 3"
                elif dataset == "Monthly Digests - Buildings Department - Table 5.6 Completed new buildings for which occupation permits have been issued":
                    data["Dataset"] = "Table 4"

                

                db.append(data)

roadsuffixes = ["road", "street", "way", "avenue", "drive", "lane", "grove", "gardens", "place", "circus", "crescent", "bypass", "close", "square", "hill", "rise", "row", "wharf", "terrace", "Runway", "District", "Bay", "Facilities", "EXTENSION", "Runway", "Path", "School", "Area", "site", "RACECOURSE", "Airport", "PARK", ]
roadsuffixesupper = [x.upper() for x in roadsuffixes]

for i in db:
    address = i["Address"]
    firstAddress = address.split("(")[0].split(",")[0].strip()

    string = firstAddress.upper()
    if not any(substring in string for substring in roadsuffixesupper):
        print(string)


# with open('database.json', 'w', encoding='utf-8') as f:
#     json.dump(db, f, ensure_ascii=False, indent=4)

print(f"total entries: {len(db)}")


import pandas as pd
pdData = pd.DataFrame(db, index=list(range(len(db))))
pdData.to_csv("test.csv")