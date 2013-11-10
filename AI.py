#-*-python-*-
from BaseAI import BaseAI
from GameObject import *
from heapq import *
from datetime import datetime

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
            if ( (tile.owner == ai.enemyID and tile.pumpID == -1)
                    or tile.owner == 3
                    or tile.isSpawning
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
        self.MAX_WORKERS = 0
        self.MAX_TANKS = 1
        self.MAX_SCOUTS = 5

        self.sw_dict = {}
        
        pass

    ##This function is called once, after your last turn
    def end(self):
        self.sw_summary()
        pass
        
    def sw_start(self):
        self.sw_run = datetime.today()
        self.last = datetime.today()
    
    def sw_lap(self,lapname):
        current = datetime.today()
        te = current - self.last
        try:
            self.sw_dict[lapname].append(te)
        except KeyError:
            self.sw_dict[lapname] = [te]
        self.last = current
    
    def sw_stop(self):
        te = datetime.today() - self.sw_run
        try:
            self.sw_dict["TurnTime"].append(te)
        except:
            self.sw_dict["TurnTime"] = [te]
            
    def sw_summary(self):
        try:
            print "SW\tAverage\tTotal\tLast"
            for k in self.sw_dict:
                last = self.sw_dict[k][-1].total_seconds()
                total = sum([ t.total_seconds() for t in self.sw_dict[k] ])
                average = total / len(self.sw_dict[k])
                print "{}\t{}\t{}\t{}".format(k, average, total, last)
        except AttributeError:
            print "sw_dict isn't ready"
            
  ##This function is called each time it is your turn
  ##Return true to end your turn, return false to ask the server for updated information
    def run(self):
        #if self.turnNumber > 200:
            #self.CANALDEPTH = 11
    
        print "Turn {} ({}s available)".format(self.turnNumber,self.players[self.playerID].time)
        self.sw_start()
        
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
        
        pumptilebyid = {}
        
        tilemap = {}
        for t in self.tiles:
            tilemap[(t.x,t.y)] = t
            if t.pumpID != -1:
                try:
                    pumptilebyid[t.pumpID].append(t)
                except KeyError:
                    pumptilebyid[t.pumpID] = [t]
            
        self.unitmap = {}
        def updateunitmap():
            for u in self.units:
                self.unitmap[(u.x,u.y)] = u
        updateunitmap()
        
        self.sw_lap("Dictionaries/Lists")
        
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
                closedset.add(consider)
                adjtiles = [ tilemap[ t ] for t in self.pf.adj[ consider ] if tilemap[ t ].owner != 3 ]
                for adj in adjtiles:
                    if adj.depth > 1 or (adj.depth == 1 and adj.turnsUntilDeposit > 3):
                        c = (adj.x, adj.y)
                        flow.add( c )
                        if c not in closedset:
                            openset.add(c)
            return flow
            
        self.sw_lap("GlacierExpansionFunc")
                
        connectedmypumps = []
        connectedenemypumps = []
        
        myconnectedstations = set()
        enemyconnectedstations = set()
        
        expandedice = expandglaciers(glaciers)
        
        for tile in expandedice:
            adj = self.pf.adj[ tile ]
            for cell in adj:
                consider = tilemap[cell]
                if consider.pumpID != -1 and consider.owner == self.playerID:
                    myconnectedstations.add(consider.pumpID)
                elif consider.pumpID != -1 and consider.owner == self.enemyID:
                    enemyconnectedstations.add(consider.pumpID)               
                    
        self.sw_lap("DetectingConnectedPumps")
        
        for c in myconnectedstations:
            connectedmypumps += pumptilebyid[c]
        for c in enemyconnectedstations:
            connectedenemypumps += pumptilebyid[c]
            
        print connectedmypumps
            
        self.sw_lap("FilteringConnectedPumps")
        
        self.MAX_TANKS = 1 #min(2, len(myconnectedstations))
        self.MAX_SCOUTS = 3 #(75 - self.MAX_TANKS * 15) / 12
        self.MAX_WORKERS = 2
            
        if len(connectedmypumps) + len(connectedenemypumps) == 0:
            self.MAX_SCOUTS = 4
            self.MAX_WORKERS = 2
            self.MAX_TANKS = 0
        
        spawned_workers = 0
        spawned_scouts = 0
        spawned_tanks = 0
        spawns = mypumptiles+myspawns
        spawns.sort(key=lambda ti: abs(ti.x- 20))
        
        def spawnunit(type, spawnlist):
            if len(spawnlist) == 0:
                return False
            for tile in spawnlist:
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
                        tile.spawn(type)
                        return True
            return False
        
        scoutspawns = mypumptiles + myspawns
        if connectedenemypumps and scoutspawns:
            scoutspawns.sort(key=lambda spwn: min( [ distance( (spwn.x, spwn.y), (ep.x,ep.y) ) for ep in connectedenemypumps ] ) )
            
        while spawned_scouts + len(myscouts) < self.MAX_SCOUTS and spawnunit( self.SCOUT, scoutspawns):
            spawned_scouts += 1
            
        #tankspawns = connectedmypumps
        #if connectedmypumps and mytanks:
            #tankspawns.sort(key=lambda spwn: max( [ distance( (spwn.x, spwn.y), (ep.x,ep.y) ) for ep in mytanks ] ) )
            
        while spawned_tanks + len(mytanks) < self.MAX_TANKS and spawnunit( self.TANK, scoutspawns):
            spawned_tanks += 1
        
        workerspawns = mypumptiles
        if glaciers and mypumptiles:
            workerspawns.sort(key=lambda spwn: min( [ distance( (spwn.x, spwn.y), (gc.x,gc.y) ) for gc in glaciers ] ) )
        
        while spawned_workers + len(myworkers) < self.MAX_WORKERS and spawnunit( self.WORKER, workerspawns):
            spawned_workers += 1
        
        self.sw_lap("SpawnUnits")
        
        if len(myworkers) > 0:
            MAX_CONNECT = 15
            digdests = set()
            expandedpumps = list(expandglaciers(mypumptiles))
            for icecube in glaciers:
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
        
        self.sw_lap("ProposeChannels")
        
        for worker in myworkers:
            donesomething = False
            updateunitmap()
            def connectchecker(tile):
                try:
                    occupy = self.unitmap[ (tile.x,tile.y) ]
                    return occupy.id == worker.id or occupy.owner != self.playerID
                except KeyError:
                    return True
            ctiles = [ c for c in connectedenemypumps if connectchecker(c) ] 
            path = self.pf.astar(self, o2tuple([worker]), list(digdests)+o2tuple(ctiles), fearwater=True)
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
        
        self.sw_lap("WorkerAI")
        
        for scout in myscouts:
            priority = [ t for t in enemyunits if t.healthLeft > 0 ]
            updateunitmap()
            def connectchecker(tile):
                try:
                    occupy = self.unitmap[ (tile.x,tile.y) ]
                    return occupy.id == scout.id or occupy.owner != self.playerID
                except KeyError:
                    return True
            ctiles = [ c for c in connectedenemypumps if connectchecker(c) ]  
            #ontiles = [ (c.x,c.y) for c in enemypumptiles if distance( (scout.x, scout.y), (c.x, c.y) ) == 0]
            attackingunit = False
            if len(ctiles) > 0:
                path = self.pf.astar(self, o2tuple([scout]), o2tuple(ctiles + enemyscouts + enemytanks) , fearwater=True)
            else:
                attackingunit = True
                path = self.pf.astar(self, o2tuple([scout]), o2tuple(priority) , fearwater=True)
            #if (scout.x, scout.y) in ontiles and len(path) > scout.movementLeft:
            #    path = []
            for (x,y) in path:
                #attackables = filter(lambda e: distance( (scout.x,scout.y), (e.x, e.y) ) == 1, priority)
                #if len(attackables) > 0 and not scout.hasAttacked:
                    #scout.attack(attackables[0])
                    #break
                if scout.movementLeft > 0 and (x,y) not in self.unitmap:
                    scout.move( x,y )
                else:
                    break
            attackables = filter(lambda e: distance( (scout.x,scout.y), (e.x, e.y) ) == 1, priority)
            if len(attackables) > 0 and not scout.hasAttacked:
                scout.attack(attackables[0])
                    
        self.sw_lap("ScoutAI")
        
        for priority in [ enemyscouts + enemytanks, enemyworkers ]:
            if len(priority) == 0:
                continue
            for tank in mytanks:
                priority = [ t for t in priority if t.healthLeft > 0 ]
                ctiles = [ c for c in mypumptiles if distance( (tank.x, tank.y), (c.x, c.y) ) != 0 and pumpdict[ c.pumpID ].siegeAmount > 0]
                ontiles = [ (c.x,c.y) for c in mypumptiles if distance( (tank.x, tank.y), (c.x, c.y) ) == 0 and pumpdict[ c.pumpID ].siegeAmount > 0]
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
                
        self.sw_lap("TankAI")
        self.sw_stop()
        self.sw_summary()
        
        return 1

    def __init__(self, conn):
        BaseAI.__init__(self, conn)
