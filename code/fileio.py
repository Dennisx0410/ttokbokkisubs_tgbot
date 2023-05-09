import sys
import json

# read json file
def readJson(fileName):
    print('loading: ' + fileName)
    try:
        with open(fileName, 'r', encoding='utf-8') as file:
            jsonFile = json.load(file)
    except Exception:
        print(fileName + ' not found, program terminated')
        sys.exit()

    print('>> ' + fileName + ' successfully loaded\n')
    return jsonFile


# write json file
def writeJson(fileName, data):
    try:
        with open(fileName, 'w', encoding="utf-8") as file:
            json.dump(data, file, indent=4)
    except Exception:
        print(' failed to write' + fileName + 'file, program terminated')
        sys.exit()