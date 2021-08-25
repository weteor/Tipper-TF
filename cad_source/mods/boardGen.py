import cadquery as cq
from dataclasses import dataclass

from .common import *
from copy import copy
import math

@dataclass
class keebConfig:
    height_plate: float
    height_pcb: float
    distance_pcb: float
    spacing: tuple 
    hSize : tuple
    rows : int
    cols : int
    keysPerCol: tuple
    stagger: tuple
    staggerX: tuple
    colRot: tuple
    tClusterRot: tuple
    tClusterPos: tuple
    tClusterSize: tuple
    tClusterSpacing: float
    handRotation: float
    handDistance: float
    holeToEdge: float
    filletSizeLarge: float
    filletSizeSmall: float
    upperEdgeIndent: bool = True
    upperEdgeOffset: float = 0
    lowerEdgeStraight: bool = False
    pass

@dataclass
class caseConfig:
    switchClearance: float
    clearanceSafety: float
    wallSafety: float
    wallThickness: float
    bottomThickness: float
    heightAbovePlate: float
    cutoutExtra: tuple
    thumbCutout : float
    hDiameter : float
    hDepth : float
    pass


def doFillet(obj, cfg):
    ret = obj
    if not cfg.lowerEdgeStraight:
        ret = ret.edges("|Z and >Y").fillet(cfg.filletSizeLarge)
    # ret = ret.edges("|Z").edges(">>X[-2] or <<X[-2]").fillet(cfg.filletSizeLarge)
        ret = ret.faces("#Z and |Y").faces(">>Y[-2]").edges("|Z").fillet(cfg.filletSizeSmall)
    ret = ret.edges("|Z").edges(">X or <X").fillet(cfg.filletSizeLarge)
    if cfg.upperEdgeIndent:
        ret = ret.edges("|Z and <Y").fillet(cfg.filletSizeSmall)
    return ret
    
    return ret


def GeneratePlate(cfg, withCaseHoles=None):
    
    baseLength=cfg.rows*cfg.cols*cfg.hSize[0]*4
    base = cq.Workplane("XY").rect(baseLength, baseLength).extrude(cfg.height_plate)

    locs = []
    
    for i in range(cfg.cols):
        angle = cfg.colRot[i]
        angle_rad = math.radians(angle) 
        for j in range(cfg.keysPerCol[i]):
            x = (i*cfg.spacing[0] + cfg.staggerX[i] +
                 j*cfg.spacing[1] * math.sin(angle_rad) )
            y = (cfg.stagger[i] +
                 j*cfg.spacing[1] * math.cos(angle_rad) )
            loc = cq.Location(cq.Vector((x,y,0)), cq.Vector((0,0,1)), -angle)
            locs.append(loc)
        
    start = (-cfg.spacing[0] + cfg.tClusterPos[0],-cfg.spacing[1] - cfg.tClusterPos[1]  )
    thumbs = len(cfg.tClusterRot)
    for i in range(thumbs):
        angle = cfg.tClusterRot[i]
        angle_next = cfg.tClusterRot[(i+1)%thumbs]
        angle_rad = math.radians(angle)
        loc = cq.Location(cq.Vector((*start, 0)), cq.Vector((0,0,1)), angle)
        locs.append(loc)
        x = ( start[0] +
             (0.5 * cfg.hSize[1] * math.sin(math.radians(-angle+180))) +
             (0.5 * (cfg.spacing[0]*cfg.tClusterSize[i]+cfg.tClusterSpacing) * math.sin(math.radians(-angle+90))) +
             (0.5 * (cfg.spacing[0]*cfg.tClusterSize[(i+1)%thumbs]+cfg.tClusterSpacing) * math.sin(math.radians(-angle_next+90))) +
             (0.5 * cfg.hSize[1] * math.sin(math.radians(-angle_next)))
             )
        y = ( start[1] +
             (0.5 * cfg.hSize[1] * math.cos(math.radians(-angle+180))) +
             (0.5 * (cfg.spacing[0]*cfg.tClusterSize[i]+cfg.tClusterSpacing) * math.cos(math.radians(-angle+90))) +
             (0.5 * (cfg.spacing[0]*cfg.tClusterSize[(i+1)%thumbs]+cfg.tClusterSpacing) * math.cos(math.radians(-angle_next+90))) +
             (0.5 * cfg.hSize[1] * math.cos(math.radians(-angle_next)))
             )
        start = (x,y)
    
    base = base.pushPoints(locs).rect(*cfg.hSize).cutThruAll()
    
    if not cfg.lowerEdgeStraight:
        locs = []
        
        start = (-cfg.spacing[0] + cfg.tClusterPos[0],-cfg.spacing[1] - cfg.tClusterPos[1]  )
        angle = cfg.tClusterRot[0]
        
        x = ( start[0] +
              (0.5 * cfg.hSize[1] * math.sin(math.radians(-angle+180))) +
              (0.5 * (cfg.spacing[0]*cfg.tClusterSize[0]+cfg.tClusterSpacing) * math.sin(math.radians(-angle+90))) +
              (cfg.holeToEdge * math.sin(math.radians(180+(cfg.tClusterRot[1]-cfg.tClusterRot[0])/2)))
             )
        
        y = ( start[1] +
              (0.5 * cfg.hSize[1] * math.cos(math.radians(-angle+180))) +
              (0.5 * (cfg.spacing[0]*cfg.tClusterSize[0]+cfg.tClusterSpacing) * math.cos(math.radians(-angle+90))) +
              (cfg.holeToEdge * math.cos(math.radians(180+(cfg.tClusterRot[1]-cfg.tClusterRot[0])/2)))
             )
    
        loc = cq.Location(cq.Vector((x,y, 0)), cq.Vector((0,0,1)), 180+angle)
        locs.append(loc) 
    
        loc = cq.Location(cq.Vector((x,y, 0)), cq.Vector((0,0,1)), 270+cfg.tClusterRot[1])
        locs.append(loc)
        start = (x,y)
        
        base = base.pushPoints(locs).rect(baseLength*2,baseLength*2,(False,False)).cutThruAll()
    
    base = base.rotate((0,0,0), (0,0,1), cfg.handRotation)

    locs = []
    
    start =  base.faces(">Z").vertices(">>X[-3]").val().toTuple()
    x = start[0] + cfg.holeToEdge*1.5 * math.sin(math.radians(cfg.handRotation-cfg.colRot[-1]+90))
    y = start[1] + cfg.holeToEdge*1.5 * math.cos(math.radians(cfg.handRotation-cfg.colRot[-1]+90))
    loc = cq.Location(cq.Vector((x,y,0)),cq.Vector((0,0,1)), cfg.handRotation-cfg.colRot[-1]+270)
    locs.append(loc)
    

    start =  base.faces(">Z").vertices("<<X[-3]").val().toTuple()
        
    x = start[0] -cfg.handDistance/2
    y = start[1]
    loc = cq.Location(cq.Vector((x,y,0)), cq.Vector((0,0,1)), 90)
    locs.append(loc)
    
    base = base.pushPoints(locs).rect(baseLength*3,baseLength*3, (True,False)).cutThruAll()

    locs = []

    if cfg.lowerEdgeStraight:
        start = base.faces(">Z").vertices("<<Y[-3]").val().toTuple()
    else:
        start =  base.faces(">Z").vertices("<<Y[-2]").val().toTuple()
    x = start[0]
    y = start[1] - cfg.holeToEdge*1.1
    loc = cq.Location(cq.Vector((x,y,0)), cq.Vector(0,0,1), 180)
    locs.append(loc)
    
    start =  base.faces(">Z").vertices(">>Y[-3]").val().toTuple()
    x = start[0]
    y = start[1] + cfg.holeToEdge
    loc = cq.Location(cq.Vector((x,y,0)))
    locs.append(loc)    
    
    base = base.pushPoints(locs).rect(baseLength*3,baseLength*3, (True,False)).cutThruAll()

    pointLow = base.faces(">Z").edges("<<Y[-2]").vals()[0].Vertices()[0].Center().toTuple()
    pointHigh = base.faces(">Z").edges("<<Y[-2]").vals()[0].Vertices()[1].Center().toTuple()
    yHigh = base.faces(">Z").vertices(">Y").val().Center().toTuple()[1]+cfg.upperEdgeOffset
    
    height = pointHigh[1] - pointLow[1]
    
    plstt = [ (pointLow[0], yHigh-height),
              (pointHigh[0], yHigh),
              (pointHigh[0], yHigh+height),
              (-baseLength, yHigh+height),
              (-baseLength, yHigh-height),
              (pointLow[0], yHigh-height)]
    
    # base = base.faces(">Z").workplane()
    
    # base = base.center(base.plane.toLocalCoords(cq.Vector(0,0,0)).x, base.plane.toLocalCoords(cq.Vector(0,0,0)).y)
    if cfg.upperEdgeIndent:
        base = base.polyline(plstt).close().cutThruAll()
    
    plate = base.mirror(base.faces("<X"), union=True)
    
    tmp = plate.faces(">Z").workplane(centerOption="CenterOfMass")
    
    plate = plate.translate(tmp.plane.toLocalCoords(cq.Vector(0,0,0)))
    
    pOutline = plate.faces(">Z").wires().first().val()
    pOutline_verts = pOutline.Vertices()
    pOutline = pOutline.fillet2D(cfg.filletSizeLarge, pOutline_verts)
    
    plate = plate.intersect(cq.Workplane().add(pOutline).toPending().extrude(-cfg.height_plate))
    
    # ---------
    locs = []
    rot = cfg.handRotation+cfg.tClusterRot[0];

    pos = plate.faces(">Z").vertices("<<X[-2]").val().toTuple()
    locs.append((pos[0] + 15*math.sin(math.radians(90+cfg.handRotation)),
                 pos[1] + 15*math.cos(math.radians(90+cfg.handRotation))))
    locs.append((locs[-1][0] + 9*math.sin(math.radians(rot+cfg.handRotation)),
                 locs[-1][1] + 9*math.cos(math.radians(rot+cfg.handRotation))))
    locs.append((locs[-1][0] + 5*math.sin(math.radians(90+cfg.handRotation)), 
                 locs[-1][1] + 5*math.cos(math.radians(90+cfg.handRotation))))
    locs.append((locs[-1][0] + 9*math.sin(math.radians((180-(rot)+cfg.handRotation))),
                 locs[-1][1] + 9*math.cos(math.radians((180-(rot)+cfg.handRotation)))))
    locs.append((locs[-1][0]-100, locs[-1][1]))
    outline_pcb = plate.polyline(locs).close().mirrorY().cutThruAll()
    
    
    locs = []
    pos = plate.faces(">Z").edges("%LINE").edges(">Y").vertices("<X").val().toTuple()
    locs.append((pos[0]+10, pos[1]))
    locs.append((locs[-1][0] + 9*math.sin(math.radians(180-rot)),
                 locs[-1][1] + 9*math.cos(math.radians(180-rot))))
    locs.append((locs[-1][0] + 5*math.sin(math.radians(90)), 
                 locs[-1][1] + 5*math.cos(math.radians(90))))
    locs.append((locs[-1][0] + 9*math.sin(math.radians(((rot)))),
                 locs[-1][1] + 9*math.cos(math.radians(((rot))))))
    locs.append((locs[-1][0], locs[-1][1]+100))
    outline_pcb = outline_pcb.polyline(locs).close().mirrorY().cutThruAll()
    
    
    locs = []
    pos = plate.faces("<Z").edges("|X").edges(">>Y[-2]").vertices("<X").val().toTuple()
    locs.append((pos[0], pos[1]))
    locs.append((locs[-1][0] + 15*math.sin(math.radians(270)),
                 locs[-1][1] + 15*math.cos(math.radians(270))))
    locs.append((locs[-1][0] + 20*math.sin(math.radians(270+(cfg.handRotation+cfg.tClusterRot[0]))),
                 locs[-1][1] + 20*math.cos(math.radians(270+(cfg.handRotation+cfg.tClusterRot[0])))))
    locs.append((locs[-1][0] + 20, locs[-1][1]))
    outline_pcb = outline_pcb.polyline(locs).close().mirrorY().cutThruAll()
    
    
    locs = []
    pos = plate.faces(">Z").edges("<Y").vertices("<X").val().toTuple()
    locs.append((pos[0]+1, pos[1]))
    locs.append((locs[-1][0] + 9*math.sin(math.radians((cfg.handRotation+cfg.tClusterRot[0]))),
                 locs[-1][1] + 9*math.cos(math.radians((cfg.handRotation+cfg.tClusterRot[0])))))
    locs.append((locs[-1][0] + 5, locs[-1][1]))
    locs.append((locs[-1][0] + 9*math.sin(math.radians(180-(cfg.handRotation+cfg.tClusterRot[0]))),
                 locs[-1][1] + 9*math.cos(math.radians(180-(cfg.handRotation+cfg.tClusterRot[0])))))
    locs.append((locs[-1][0], locs[-1][1] -20))
    locs.append((locs[-1][0] -30, locs[-1][1]))
    outline_pcb = outline_pcb.polyline(locs).close().mirrorY().cutThruAll()
    # outline_pcb = outline_pcb.faces(">Z").wires().first().toPending().extrude(1)

    
    return plate, outline_pcb

def GenerateMidLayer(plate, cfg):
    midlayer = plate.faces(">Z").wires().first().toPending().extrude(-cfg.height_mid).translate((0,0,-cfg.height_plate))
    midlayer = midlayer.faces(">Z").wires().first().toPending().offset2D(-cfg.holeToEdge).cutThruAll()
    
    return midlayer

def GeneratePcb(plate,cfg):
    pcb = plate.faces(">Z").wires().first().toPending().extrude(-cfg.height_pcb).translate((0,0,-(cfg.height_plate+cfg.height_mid)))
    return pcb

def GenerateCase(plate, cfg):
    case = (plate.faces(">Z").wires().first()
                 #.translate((0,0,cfg.heightAbovePlate))
                 .toPending()
                 .offset2D((cfg.wallThickness+cfg.wallSafety))
                 .extrude(-(cfg.switchClearance+cfg.clearanceSafety+cfg.wallThickness))
                 )
    case = (case.faces(">Z").wires().toPending()
                .offset2D(-cfg.wallThickness)
                .cutBlind(-(cfg.switchClearance+cfg.clearanceSafety))
                )
    
    # debug(case.faces("<Z").wires())
    case = (case.faces("<Z").wires().first().toPending().chamfer(1.5))
    case = (case.faces(">Z").wires().first().toPending().chamfer(1))
    
    return case

def GenerateCaseTop(plate, pCfg, cCfg):
    case_top = (plate.faces(">Z").wires().first()
                     .toPending()
                     .offset2D((cCfg.wallThickness+cCfg.wallSafety)).tag("test")
                     .extrude(cCfg.heightAbovePlate)
                  )
    
    thumbButtons = len(pCfg.tClusterRot)
    
    pts = [plate.faces(">Z").wires().item(i+1).val().Center() 
           for i in range(plate.faces(">Z").wires().size()-1)]
    
    ptsSrtY = sorted(pts, key = lambda vec: vec.y)
    ptsSrtAX = sorted(ptsSrtY[2*thumbButtons:], key= lambda vec: vec.x)
    ptsSrtTX = sorted(ptsSrtY[:2*thumbButtons], key= lambda vec: vec.x)
    
    last = cq.Vector((0,0,0))
    for vec in ptsSrtAX:
        next = vec-last
        last = vec
        if vec.x < 0:
            case_top = (case_top.faces(">Z")
                                .workplane()
                                .center(next.x, next.y)
                                .transformed(rotate=(0,0,-pCfg.handRotation))
                                .rect(pCfg.hSize[0]+cCfg.cutoutExtra[0],
                                      pCfg.hSize[1]+cCfg.cutoutExtra[1])
                                .cutBlind(-cCfg.heightAbovePlate)
                                )
        else:
            case_top = (case_top.faces(">Z")
                                .workplane()
                                .center(next.x, next.y)
                                .transformed(rotate=(0,0,pCfg.handRotation))
                                .rect(pCfg.hSize[0]+cCfg.cutoutExtra[0],
                                      pCfg.hSize[1]+cCfg.cutoutExtra[1])
                                .cutBlind(-cCfg.heightAbovePlate)
                                )
        
    for i,vec in enumerate(ptsSrtTX[:thumbButtons]):
        next = vec-last
        last = vec
        
        case_top = (case_top.faces(">Z")
                            .workplane()
                            .center(next.x, next.y)
                            .transformed(rotate=(0,0,-pCfg.handRotation-pCfg.tClusterRot[-1-i]))
                            .rect(pCfg.hSize[0]+cCfg.cutoutExtra[0]-1.5,
                                  pCfg.hSize[1]+cCfg.cutoutExtra[1]-1)
                            .cutBlind(-cCfg.heightAbovePlate)
                            )
        
    for i,vec in enumerate(ptsSrtTX[thumbButtons:]):
        next = vec-last
        last = vec
        
        case_top = (case_top.faces(">Z")
                            .workplane()
                            .center(next.x, next.y)
                            .transformed(rotate=(0,0,pCfg.handRotation+pCfg.tClusterRot[i]))
                            .rect(pCfg.hSize[0]+cCfg.cutoutExtra[0]-1.5,
                                  pCfg.hSize[1]+cCfg.cutoutExtra[1]-1)
                            .cutBlind(-cCfg.heightAbovePlate)
                            ) 
    
    return case_top

# config_32 = keebConfig(
#     height_plate = 1.2,
#     distance_pcb = 2,
#     height_pcb = 1.6,
#     spacing = (18,17),
#     hSize = (14,14),
#     rows =  3,
#     cols = 5,
#     keysPerCol= ( 3, 3, 3, 3, 3 ),
#     stagger  = ( 2, 2, 6, 0,-13.5),
#     staggerX = ( 0, 0, 0, 0, -1.75),
#     colRot= (0,0,0,4,15.5),
#     tClusterRot=   (15, 0),
#     tClusterSize = ( 1, 1.5),
#     tClusterPos= (-4.55,4),
#     tClusterSpacing= 3,
#     handRotation= 21,
#     handDistance = 22,
#     holeToEdge = 3,
#     filletSizeLarge= 5,
#     filletSizeSmall= 5,
#     upperEdgeIndent = True,
#     upperEdgeOffset = 2.25,
#     lowerEdgeStraight = False,
#     )

# config_highProfileChoc = caseConfig(
#     switchClearance = 5.2,
#     clearanceSafety = 1,
#     wallSafety = .5,
#     wallThickness = 4,
#     bottomThickness = 2,
#     heightAbovePlate = 5,
#     cutoutExtra = (0.25, 0.25 ),
#     thumbCutout = 2,
#     hDiameter = 3.2,
#     hDepth = 5,
#     )

# plate, outl_pcb = GeneratePlate(config_32, False)
# # plate = doFillet(plate, config_32)
# # show_object(plate, name = "plate")
# show_object(plate , name="plate")
# show_object(outl_pcb , name="pcb")
# # case = GenerateCase(plate, config_highProfileChoc)
# # show_object(case)
