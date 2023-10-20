import yaml
from yaml.loader import SafeLoader

def checkIfValidBasic(obj):
    return  type(obj) is dict and obj.get('resources')!=None and obj.get('perspectives')!= None


# Open the file and load the file
with open('./testFile.yaml') as f:
    data = yaml.load(f, Loader=SafeLoader)
print(data, type(data))
print( checkIfValidBasic(data))


data = yaml.safe_load(open('./testErrorFile.yaml'))
print(data, type(data))
print( checkIfValidBasic(data))

try:
    config = yaml.load('./testErrorFile.yaml', Loader=SafeLoader)
    print(">",config, type(config))
    print( checkIfValidBasic(config))
except yaml.YAMLError:
    print("Error in configuration file:")