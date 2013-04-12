from json.encoder import JSONEncoder
from json.decoder import JSONDecoder
import redis
import re
#import pprint

encoder = JSONEncoder()
decoder = JSONDecoder()
r_server = redis.Redis('localhost')

def buildDBMain(pth):
    import os.path

    parseTypes = {'#ROOMS': parseRooms, 
                  '#MOBILES': parseMobiles,
                  '#OBJECTS': parseArticles,
                  '#RESETS': None,
                  '#HELPS': None,
                  '#SPECIALS': None
                  }
    
    #Input file format is something like the following:
    #    #AREA  area data
    #    #MOBILES
    #    #nnn1 (vnum of first mobile)
    #    data for mobile number nnn1
    #    #nnn2 (vnum of second mobile)
    #    data for mobile number nnn2
    #    #0   (signifies end of MOBILES)
    #    #ROOMS, #OBJECTS formatted similar to #MOBILES
    #    #HELPS, #SPECIALS, #RESETS followed by various data lines
    #    #$ (end of file)
   
    # Pattern says # followed by 1-n uppercase letters followed by
    # everything else up until a newline is reached.
            
    pattern = re.compile('#+[A-Z]+.*') 
            
    for flname in os.listdir(pth)[:1]:
        if flname.endswith('.are'):
            areaName = flname[:-4]
            
            with open(os.path.join(pth, flname)) as txtFile:
                fileText = txtFile.read()
                        
                # itemList contains all lines (new line stops the match) that
                # contain the pattern #AAAAA where AAAA is some number of
                # uppercase alpha characters.  For the file format described 
                # above, the output is a list containing the #AREA line along 
                # with the area data, and the individual lines with
                # #MOBILES, #OBJECTS, etc.
            
                itemList = re.findall(pattern, fileText)
        
            
                # Next, use split to get a set of itemText strings that do 
                # NOT include the actual pattern but use the pattern to split the
                # object data.  Note that for our data we are ignoring all the new
                # line separators at this point.  The parser for each item will
                # need these separators to find its data.
            
                itemText = re.split(pattern, fileText)
            
                # Note that the first itemText in the "split" output is empty.  
                # This is actually the matching "thing" that we found with 
                # the "findall", in this case the #AREA and the remainder of 
                # its line.
            
                for itemName in itemList:
                    
                    # The #AREA types gets special processing, since all
                    # its data is within the line that starts with #AREA.
                    
                    if itemName.startswith('#AREA'):
                        itemNum = 1
                        areaDict = createAreaDict(itemName)
                        
                    # For the other data types, match the data with the 
                    # keyword (#MOBILES, #ROOMS, etc.) and pass the data to
                    # the appropriate parsing function based on the data type.
                    
                    else:
                        itemNum = itemNum + 1
                        if itemName in parseTypes:
                            itemParser = parseTypes.get(itemName)
                            
                            # If this is an item type that requires additional
                            # parsing, it has a function name to do the
                            # parsing.  Otherwise, it is skipped. 
                            # Later code will need to handle some of these
                            # "other" types.
                            
                            if itemParser:
                                itemDict = itemParser(areaName,
                                                      itemText[itemNum])
                                
                                areaDict.update(itemDict)
                            
                            else:
                                if debugMode:
                                    print "Item", 
                                    itemName,
                                    itemNum, 
                                    itemText[itemNum]
            
                # The areaDict consists of area data plus lists of the
                # various other types (mobiles, rooms, articles).
                
                areaKey = ':'.join(['area', areaName])
                encodeDict(areaKey, areaDict)
                r_server.sadd('areas', areaKey)
                
        for areaKey in r_server.smembers('areas'):
            json_area = r_server.get(areaKey)
            
            areaDict = decoder.decode(json_area)
            if debugMode:
                print "area", areaKey, areaDict
            
            roomList = areaDict.get('rooms')
                            
            for roomKey in roomList:
                updateExitKeys(roomKey)
            
    return

def updateExitKeys(roomKey):
    roomDBKey = ':'.join(['room', roomKey])
    json_room = r_server.get(roomDBKey)
    
    roomDict = decoder.decode(json_room)
    
    exitList = roomDict.get('exits')
    updatedExitList = []
    
    for exitWithVnum in exitList:
    
        updatedExitEntry = convertVnumToKey(exitWithVnum)
                
        updatedExitList.append(updatedExitEntry)
    
    roomDict.update({'exits': updatedExitList})
    
    if debugMode:
        print "Updated roomDict", roomKey, roomDict
    
    encodeDict(roomDBKey, roomDict)
    
    return   

def convertVnumToKey(exitWithVnum):
    
    exitVnum = exitWithVnum.get('vnum')
    
    updatedExit = exitWithVnum.copy()
    del updatedExit['vnum']
        
    exitRoomKey = ':'.join(['room', exitVnum])
    actualExitRoom = vnumDict.get(exitRoomKey)
    
    updatedExit.update({'destination': actualExitRoom})
        
    return updatedExit

    return 
    
def encodeDict(dbKey, dbDict):
    my_json_obj = encoder.encode(dbDict)
    r_server.set(dbKey, my_json_obj)
    
def createAreaDict(areaLine):
    areaStuff = areaLine.rpartition('}')[2]
    author, notUsed, desc = areaStuff.lstrip().partition(' ')
    name = desc.strip().rstrip('~')
    areaDict = {'name': name, 
                'author': author, 
                'owner_id': 'nancy',
                'next_room_id': 0}
    
    return areaDict
       
# Functions that follow are selected based on the type of
# "group directive", i.e. #MOBILES, #ROOMS, #OBJECTS.

def parseMobiles(areaName,
                 itemText):
     
    mobileList = splitSingleObjects(itemText)
    
    mobileItemList = parseOneItem(areaName,
                                  'mobile', 
                                  mobileList,
                                  getMobileKey, 
                                  parseOneMobile) 
    
    mobileDict = {'mobiles': mobileItemList}
    return mobileDict
       
def parseRooms(areaName,
               itemText): 
    
    roomList = splitSingleObjects(itemText)
    
    roomItemList = parseOneItem(areaName,
                                'room', 
                                roomList,
                                None,
                                parseOneRoom)
    
    roomDict = {'rooms': roomItemList}
    return roomDict
    
def parseArticles(areaName,
                  itemText):
    
    articleList = splitSingleObjects(itemText)
    
    articleItemList = parseOneItem(areaName,
                                   'article', 
                                   articleList,
                                   None,
                                   parseOneArticle)
    
    articleDict = {'articles': articleItemList}
    return articleDict

# Split each object type into its individual components based on the
# vnums, identified as #nnnn within each type.
       
def splitSingleObjects(itemText):
    itemList = re.split(r'#', itemText.lstrip())
    return itemList

# Parse a single item within a type, that is, a single vnum group.  Each of
# these items becomes an individual database object with its own dictionary
# fields, and is parsed according to the merc doc.
# The name of the parse routine for each type is passed.

def parseOneItem(areaName,
                 itemType, 
                 itemList,
                 getItemKey, 
                 singleParseFunction):
    
    itemSeq = 0
    areaItems = []
    for line in itemList:
        if line:
            if re.search(r'^\d{4}', line):
                vnum, notUsed, itemData = line.partition('\n')
                if getItemKey:
                    itemBase = getItemKey(itemData, itemSeq)
                else:
                    itemBase = str(itemSeq)
                itemKey = ':'.join([areaName, itemBase])
                vnumKey = ':'.join([itemType, vnum])
                itemSeq = itemSeq + 1
                
                areaItems.append(itemKey)
                if debugMode:
                    print "vnum", vnumKey, itemKey
                
                vnumKeyString = str(vnumKey)
                
                vnumDict.update({vnumKeyString: itemKey})
                                
                singleParseFunction(areaName,
                                    itemKey,
                                    itemData)
    return areaItems
            
def getMobileKey(itemData, itemSeq):
    titleLine = itemData.partition('~')
    keyName = titleLine[0].partition(' ')
    itemKey = ''.join([keyName[0], str(itemSeq)])
    return itemKey
    
def parseOneMobile(areaName, 
                   itemKey, 
                   itemText):
         
    mobileKey = ':'.join(['mobile', itemKey])
    
    title, notUsed, remainder = itemText.partition('~')
    
    desc, notUsed, remainder = remainder.lstrip().partition('~')
    
    mobileDict = {'title': title, 
                  'desc': desc}
    
    encodeDict(mobileKey, mobileDict)
    
    return       
            
def parseOneArticle(areaName, 
                    itemKey, 
                    itemText): 
     
    return       
            
def parseOneRoom(areaName, 
                 itemKey, 
                 itemText): 
     
    exitList = []
    
    roomKey = ':'.join(['room', itemKey])
    
    title, notUsed, remainder = itemText.partition('~')
    
    desc, notUsed, remainder = remainder.lstrip().partition('~')
    
    desc = desc.rstrip()
    
    #pp = pprint.PrettyPrinter(indent=4)
    #print(pp.pprint(desc))
    
    roomInfo = remainder.lstrip()
    
    exitStringList = re.finditer(r'D+[0-5]', roomInfo)
    
    for exitString in exitStringList:
        oneExit = roomInfo[exitString.start():]
        exitDictEntry = createExitEntry(oneExit)
        exitList.append(exitDictEntry)
        
    roomDict = {'title': title, 
                'desc': desc,
                'exits': exitList}
    
    encodeDict(roomKey, roomDict)
    return    

def createExitEntry(exitString):
    
    dirLetters = 'neswud' 

    direction = exitString[1]
    remainder = exitString[2:]
    exitDesc, notUsed, remainder = remainder.lstrip().partition('~')
    exitDesc = exitDesc.rstrip()
    exitKeywords, notUsed, remainder = remainder.partition('~')
    exitInfo, notUsed, notUsed2 = remainder.lstrip().partition('\n')
    notUsed, notUsed2, exitVnum = exitInfo.rstrip().rpartition(' ')
    
    exitNum = int(direction)
    directionName = dirLetters[exitNum]
    
    exitDictEntry = {'dir_name': directionName,
                     'desc': exitDesc,
                     'vnum': exitVnum}
    
    return exitDictEntry
    
# What follows is __main__ which does nothing except invoke the real main
# function defined above.
 
vnumDict = {}
debugMode = True

if __name__ == '__main__':
    pth = 'C:\Users\Nancy\Documents\merc21/area/'
    buildDBMain(pth)
    
  
