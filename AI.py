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
    def astar(self, ai, starts, ends, fearwater=False, avoidowned=False):
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
                    or (tile.waterAmount > 0 and fearwater == True)
                    or (tile.owner == ai.playerID and avoidowned == True) ):
                self.obstacles[(tile.x,tile.y)] = tile  
            """
            elif tile.owner == ai.enemyID or tile.owner == ai.playerID and tile.pumpID == -1 and bloomspawns and FAL:
                bloom = [ (tile.x+x, tile.y+y) for x in range(-1,2) for y in range(-1,2) ]
                for k in bloom:
                    self.obstacles[k] = tile
            """
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
    
    MAX_WORKERS = 3
    MAX_TANKS = 1
    MAX_SCOUTS = 2

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
        for u in self.unitTypes:
            if u.type == self.WORKER:
                self.WORKERCOST = u.cost
            elif u.type == self.SCOUT:
                self.SCOUTCOST = u.cost
            elif u.type == self.TANK:
                self.TANKCOST = u.cost
        self.CANALDEPTH = 6
        pass

    ##This function is called once, after your last turn
    def end(self):
        pass
        

  ##This function is called each time it is your turn
  ##Return true to end your turn, return false to ask the server for updated information
    def run(self):
        if self.turnNumber > 200:
            self.CANALDEPTH = 11
    
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
      
        glaciers = [ t for t in self.tiles if t.owner == 3  and t.waterAmount > 3 ]
        
        pumpdict = {}
        for pump in self.pumpStations:
            pumpdict[pump.id] = pump
 
        if len(glaciers) == 0:
            self.MAX_SCOUTS = 9999
            self.MAX_WORKERS = 0
        
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
                adjtiles = [ tilemap[ t ] for t in self.pf.adj[ consider ] if tilemap[ t ].owner != 3 ]
                for adj in adjtiles:
                    if adj.depth > 1 or (adj.depth == 1 and adj.turnsUntilDeposit > 3):
                        c = (adj.x, adj.y)
                        flow.add( c )
                        openset.add( c)
            return flow
        
        spawned_workers = 0
        spawned_scouts = 0
        spawned_tanks = 0
        spawns = mypumptiles+myspawns
        spawns.sort(key=lambda ti: abs(ti.x- 20))
        for tile in spawns:
            #if this tile is my spawn tile or my pump station
            #if there is enough oxygen to spawn the unit
            if len(myunits) < self.maxUnits:
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
                    if spawned_scouts + len(myscouts) < self.MAX_SCOUTS and self.players[self.playerID].oxygen >= self.WORKERCOST:
                        tile.spawn(self.SCOUT)
                        spawned_scouts += 1
                    elif spawned_workers + len(myworkers) < self.MAX_WORKERS and self.players[self.playerID].oxygen >= self.SCOUTCOST:
                        tile.spawn(self.WORKER)
                        spawned_workers += 1
                    elif spawned_tanks + len(mytanks) < self.MAX_TANKS and self.players[self.playerID].oxygen >= self.TANKCOST:
                        tile.spawn(self.TANK)
                        spawned_tanks += 1

        
        MAX_CONNECT = 15
        digdests = set()
        for _ in range(5):
            digdests = set()
            for icecube in glaciers:
                expandedpumps = list(expandglaciers(mypumptiles))
                expandedice = list(expandglaciers([ icecube ]))
                r = self.pf.astar( self, expandedpumps, expandedice, avoidowned= True)[:-1]
                if len(r) > MAX_CONNECT:
                    continue
                for step in r:
                    if tilemap[step].depth < self.CANALDEPTH:
                        digdests.add(step)
                        break
                r.reverse()
                for step in r:
                    if tilemap[step].depth < self.CANALDEPTH:
                        digdests.add(step)
                        break
            if len(digdests) < len(myworkers) * 2:
                MAX_CONNECT += 10
            else:
                break
            
        for worker in myworkers:
            donesomething = False
            path = self.pf.astar(self, o2tuple([worker]), list(digdests), fearwater=True)
            if len(path) == 0 and (worker.x,worker.y) in digdests:
                worker.dig(tilemap[ (worker.x,worker.y) ])
                donesomething = True
            while worker.movementLeft > 0 and len(path) > 0:        
                (x,y) = path.pop(0)
                if (x,y) not in digdests and worker.movementLeft > 0:
                    worker.move(x,y)
                    donesomething = True
                elif not worker.hasDug:
                    if worker.movementLeft:
                        d = [ coord for coord in self.pf.adj[ (x,y) ] if tilemap[coord].depth == 0 and tilemap[coord].owner != 3 and tilemap[coord].owner != self.enemyID ]
                        subp = self.pf.astar(self, o2tuple([worker]), d, fearwater = True)
                        if len(subp) <= worker.movementLeft:
                            for (xs,ys) in subp:
                                worker.move(xs,ys)
                    worker.dig(tilemap[(x,y)])
                    digdests.remove( (x,y) )
                    donesomething = True
                else: 
                    break
            attackables = filter(lambda e: distance( (worker.x,worker.y), (e.x, e.y) ) <= 3, enemyunits )
            if len(attackables) > 0 and not worker.hasAttacked:
                worker.attack(attackables[0])
            if donesomething == False:
                myscouts.append(worker)
            
            #if not worker.hasDug:
            #    worker.dig( tilemap[(worker.x,worker.y)] )
        
        for priority in [ enemyscouts + enemytanks, enemyworkers ]:
            if len(priority) == 0:
                continue
            for scout in myscouts:
                priority = [ t for t in priority if t.healthLeft > 0 ]
                ctiles = [ c for c in enemypumptiles if distance( (scout.x, scout.y), (c.x, c.y) ) != 0]
                ontiles = [ (c.x,c.y) for c in enemypumptiles if distance( (scout.x, scout.y), (c.x, c.y) ) == 0]
                path = self.pf.astar(self, o2tuple([scout]), o2tuple(priority + ctiles) , fearwater=True)
                if (scout.x, scout.y) in ontiles and len(path) > scout.movementLeft:
                    path = []
                for (x,y) in path:
                    attackables = filter(lambda e: distance( (scout.x,scout.y), (e.x, e.y) ) == 1, priority)
                    if len(attackables) > 0 and not scout.hasAttacked:
                        scout.attack(attackables[0])
                        break
                    if scout.movementLeft > 0:
                        scout.move( x,y )
                    else:
                        break
                attackables = filter(lambda e: distance( (scout.x,scout.y), (e.x, e.y) ) == 1, priority)
                if len(attackables) > 0 and not scout.hasAttacked:
                    scout.attack(attackables[0])
                    break
                    
        for priority in [ enemyscouts + enemytanks, enemyworkers ]:
            if len(priority) == 0:
                continue
            for tank in mytanks:
                priority = [ t for t in priority if t.healthLeft > 0 ]
                ctiles = [ c for c in mypumptiles if distance( (tank.x, tank.y), (c.x, c.y) ) != 0 and pumpdict[ c.pumpID ].siegeAmount > 0]
                ontiles = [ (c.x,c.y) for c in mypumptiles if distance( (tank.x, tank.y), (c.x, c.y) ) == 0]
                path = self.pf.astar(self, o2tuple([tank]), o2tuple(priority + ctiles) , fearwater=True)
                if (tank.x, tank.y) in ontiles and len(path) > tank.movementLeft:
                    path = []
                for (x,y) in path:
                    attackables = filter(lambda e: distance( (tank.x,tank.y), (e.x, e.y) ) == 1, priority)
                    if len(attackables) > 0 and not tank.hasAttacked:
                        tank.attack(attackables[0])
                        break
                    if tank.movementLeft > 0:
                        tank.move( x,y )
                    else:
                        break
                attackables = filter(lambda e: distance( (tank.x,tank.y), (e.x, e.y) ) == 1, priority)
                if len(attackables) > 0 and not tank.hasAttacked:
                    tank.attack(attackables[0])
                    break
        
        return 1

    def __init__(self, conn):
        BaseAI.__init__(self, conn)
