#-*-python-*-
from BaseAI import BaseAI
from GameObject import *
from heapq import *

def distance(point1, point2):
    return abs(point1[0]-point2[0])+abs(point1[1]-point2[1])
    
def o2tuple(objlist):
    return [ (o.x, o.y) for o in objlist ]

class Pathfinder(object):
    def __init__(self,mapwidth,mapheight):
        self.mapheight = mapheight
        self.mapwdith = mapwidth
        self.obstacles = {}
        self.adj = {}
        for i in range(mapwidth):
            for j in range(mapheight):
                adj = [ (i+1,j) , (i-1,j) , (i,j+1), (i, j-1) ]
                adj = [ c for c in adj if c[0] >= 0 and c[0] < mapwidth and c[1] >= 0 and c[1] < mapheight ]
                self.adj[(i,j)] = adj
    def astar(self, ai, starts, ends):
        #TODO: Penalize Water
        openset = []
        closedset = {}
        if len(ends) == 0:
            return []
        for start in starts:
            bestend = min( [ distance(start, e) for e in ends ] )
            heappush(openset,(bestend,start))
        path = []
        reverse = {}
        consider = None
        self.obstacles = {}
        for unit in ai.units:
            if unit.healthLeft > 0:
                self.obstacles[(unit.x,unit.y)] = unit
        #for (k,v) in self.obstacles.iteritems():
        #    print "{} -> {}".format(k,v.owner)
        for tile in ai.tiles:
            if ( tile.owner == ai.enemyID
                    or tile.owner == 3
                    or tile.owner == ai.playerID
                    or tile.waterAmount > 0):
                self.obstacles[(tile.x,tile.y)] = tile  
        while consider not in ends and len(openset):
            (_,consider) = heappop(openset)
            for cell in self.adj[consider]:
                if cell in closedset:
                    continue
                else:
                    closedset[cell] = True
                if cell in self.obstacles and cell not in ends:
                    continue
                heappush(openset,(min([distance(cell,e) for e in ends]),cell))
                reverse[cell] = consider
        if consider not in ends:
            return []
        r = consider
        while r not in starts:
            path.append(r)
            r = reverse[r]
        path.reverse()
        return path
        
        
class AI(BaseAI):
    """The class implementing gameplay logic."""

    WORKER, SCOUT, TANK = range(3)
    CANALDEPTH = 2

    @staticmethod
    def username():
        return "Red Rover"

    @staticmethod
    def password():
        return "dickwalls"

    ##This function is called once, before your first turn
    def init(self):
        self.enemyID = 1 if self.playerID == 0 else 0
        self.pf = Pathfinder(self.mapWidth, self.mapHeight)
        pass

    ##This function is called once, after your last turn
    def end(self):
        pass
        

  ##This function is called each time it is your turn
  ##Return true to end your turn, return false to ask the server for updated information
    def run(self):
    
        print "Turn {}".format(self.turnNumber)
        
        path = self.pf.astar(self,[ (0,0) ], [ (5,5) ])
        
        myunits = [ u for u in self.units if u.owner == self.playerID ]
        enemyunits = [ u for u in self.units if u.owner == self.enemyID ]
        
        myworkers = [ u for u in myunits if u.type == self.WORKER ]
        myscouts = [ u for u in myunits if u.type == self.SCOUT ]
        mytanks = [ u for u in  myunits if u.type == self.TANK ]
        
        enemyworkers = [ u for u in enemyunits if u.type == self.WORKER ]
        enemyscouts = [ u for u in enemyunits if u.type == self.SCOUT ]
        enemytanks = [ u for u in  enemyunits if u.type == self.TANK ]
        
        myspawns = [ t for t in self.tiles if t.owner == self.playerID and t.pumpID == -1]
        enemyspawns = [ t for t in self.tiles if t.owner == self.enemyID and t.pumpID == -1 ]
        
        mypumptiles = [ t for t in self.tiles if t.owner == self.playerID and t.pumpID != -1 ]
        enemypumptiles = [ t for t in self.tiles if t.owner == self.enemyID and t.pumpID != -1 ]
        
        mypumps = [ p for p in self.pumpStations if t.owner == self.playerID ]
        enemypumps = [ p for p in self.pumpStations if t.owner == self.enemyID ]
      
        glaciers = [ t for t in self.tiles if t.owner == 3 ]
        
        tilemap = {}
        for t in self.tiles:
            tilemap[(t.x,t.y)] = t
        
        def expandglaciers(icecubes):
            flow = set()
            openset = set()
            closedset = set()
            for ice in icecubes:
                c = (ice.x,ice.y)
                flow.add( c )
                openset.add( c )       
            while len(openset) > 0:
                consider = openset.pop()
                if consider in closedset:
                    continue
                closedset.add(consider)
                adjtiles = [ tilemap[ t ] for t in self.pf.adj[ consider ] ]
                for adj in adjtiles:
                    if adj.depth > 0 :
                        c = (adj.x, adj.y)
                        flow.add( c )
                        openset.add( c)
            return flow
        
        for tile in myspawns + mypumptiles:
            #if this tile is my spawn tile or my pump station
            cost = 0
            for u in self.unitTypes:
              if u.type == self.WORKER:
                cost = u.cost
            #if there is enough oxygen to spawn the unit
            if self.players[self.playerID].oxygen >= cost and len(myunits) < self.maxUnits:
                #if nothing is spawning on the tile
                if tile.isSpawning == 0:
                  canSpawn = True
                  #if it is a pump station and it's not being sieged
                  if tile.pumpID != -1:
                    #find the pump in the vector
                    for pump in self.pumpStations:
                      if pump.id == tile.pumpID and pump.siegeAmount > 0:
                        canSpawn = False
                  #if there is someone else on the tile, don't spawn
                  for other in self.units:
                    if tile.x == other.x and tile.y == other.y:
                      canSpawn = False
                  if canSpawn:
                    #spawn the unit
                    tile.spawn(self.WORKER)

        digdests = set()
        for icecube in glaciers:
            expandedpumps = list(expandglaciers(mypumptiles))
            expandedice = list(expandglaciers([ icecube ]))
            r = self.pf.astar( self, expandedpumps, expandedice)
            if len(r) > 15:
                continue
            for step in r:
                if tilemap[step].depth < self.CANALDEPTH:
                    digdests.add(step)
                    break
            
        for worker in myworkers:
            path = self.pf.astar(self, o2tuple([worker]), list(digdests))
            if len(path) == 0 and (worker.x,worker.y) in digdests:
                worker.dig(tilemap[ (worker.x,worker.y) ])
            while worker.movementLeft > 0 and len(path) > 0:
                (x,y) = path.pop(0)
                if (x,y) not in digdests:
                    worker.move(x,y)
                elif not worker.hasDug:
                    worker.dig(tilemap[(x,y)])
                    digdests.remove( (x,y) )
                else: 
                    break
        
        return 1

    def __init__(self, conn):
        BaseAI.__init__(self, conn)
