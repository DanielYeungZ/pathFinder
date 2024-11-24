def printMsg(obj):
    print(obj.to_mongo().to_dict())
    return obj