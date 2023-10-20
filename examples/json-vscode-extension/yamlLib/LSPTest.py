from lsprotocol import converters,types
import json
position = types.Position(line=10, character=3)
print(position)

converter = converters.get_converter()
print(json.dumps(converter.unstructure(position, unstructure_as=types.Position)))