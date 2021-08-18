import cadquery as cq
from dataclasses import dataclass
# from math import cos,sin,radians
# from .common import *
from .common import *
from copy import copy

# def GetPosCartesian(start, coords):
#     X=0
#     Y=1
#     tmp = start
#     for (l,a) in coords:
#         tmp = (tmp[0] + l * cos(radians(a)), tmp[Y] + l * sin(radians(a)))
#     return tmp

# def cut(base, vertString, moveBy, baseLength, rotation=0, center=(True,False)):
#     return ( base
#             .faces(">Z").vertices(vertString).workplane(centerOption="CenterOfMass",)
#             .transformed(rotate=(0,0, rotation))
#             .move(*moveBy)
#             .rect(baseLength*2,baseLength*2,center)
#             .cutThruAll()
#            )



@dataclass
class keebConfig:
    height_plate: float
    height_mid: float
    height_pcb: float
    spacing: tuple 
    hSize : tuple
    rows : int
    cols : int
    keysPerCol: tuple
    stagger: tuple
    colRot: tuple
    tClusterRot: tuple
    tClusterPos: tuple
    tClusterSpacing: float
    handRotation: float
    handDistance: float
    holeToEdge: float
    doFillet: bool
    filletSizeLarge: float
    filletSizeSmall: float
    startCorrection: float
    outerThumb1u5: bool
    upperEdgeOffset: float = 0
    pass

@dataclass
class caseConfig:
    switchClearance: float
    clearanceSafety: float
    wallSafety: float
    wallThickness: float
    heightAbovePlate: float
    cutoutExtra: tuple
    pass


def doFillet(obj, cfg):
    ret = obj.edges("|Z and >Y").fillet(cfg.filletSizeLarge)
    ret = ret.edges("|Z").edges(">>X[-2] or <<X[-2]").fillet(cfg.filletSizeLarge)
    ret = ret.edges("|Z").edges(">X or <X").fillet(cfg.filletSizeLarge)
    ret = ret.faces("#Z and |Y").faces(">>Y[-2]").edges("|Z").fillet(cfg.filletSizeSmall)
    ret = ret.edges("|Z and <Y").fillet(cfg.filletSizeSmall)
    
    return ret


def GeneratePlate(cfg):
    
    baseLength=cfg.rows*cfg.cols*cfg.hSize[0]*4
    base = cq.Workplane("XY").rect(baseLength, baseLength).extrude(cfg.height_plate)
    
    #alphas r
    hPnts = []
    for i in range(cfg.cols):
        for j in range(cfg.keysPerCol[i]):
            hPnts.append((i*cfg.spacing[0], j*cfg.spacing[1]+cfg.stagger[i]))
    
    
    thPnts = []
    tstart = (-cfg.tClusterPos[0],-cfg.tClusterPos[1]-cfg.spacing[1])

    tmp = GetPosCartesian(tstart, [( cfg.hSize[1]/2, cfg.tClusterRot[1]+270),
                                   ( cfg.hSize[0]/2+cfg.tClusterSpacing/2, cfg.tClusterRot[1]+180),
                                   ( cfg.hSize[0]/2+cfg.tClusterSpacing/2, cfg.tClusterRot[0]+180),
                                   ( cfg.hSize[1]/2, cfg.tClusterRot[0]-270)
                                  ])
    
    thPnts.append(tmp)
    
    for i in range(len(cfg.tClusterRot)-1):
        if(cfg.outerThumb1u5 and i == len(cfg.tClusterRot)-1):
            tmp = GetPosCartesian((0,0), [( cfg.hSize[1]/2, cfg.tClusterRot[i]+270),
                                          ( cfg.hSize[0]/2+cfg.tClusterSpacing/2, cfg.tClusterRot[i]),
                                          ( cfg.hSize[0]/2+cfg.tClusterSpacing/2+0.25*cfg.spacing[0], cfg.tClusterRot[i+1]),
                                          ( cfg.hSize[1]/2, cfg.tClusterRot[i+1]-270)
                                         ])
        else:
            tmp = GetPosCartesian((0,0), [( cfg.hSize[1]/2, cfg.tClusterRot[i]+270),
                                          ( cfg.hSize[0]/2+cfg.tClusterSpacing/2, cfg.tClusterRot[i]),
                                          ( cfg.hSize[0]/2+cfg.tClusterSpacing/2, cfg.tClusterRot[i+1]),
                                          ( cfg.hSize[1]/2, cfg.tClusterRot[i+1]-270)
                                         ])
        thPnts.append(tmp)
    
    
    base = (base.transformed(rotate=(0,0,cfg.handRotation))
            .pushPoints(hPnts)
            .rect(cfg.hSize[0], cfg.hSize[1])
            .cutThruAll()
             )
    
    for i,tc in enumerate(thPnts):
        if (cfg.outerThumb1u5 and i==len(thPnts)-1):
            base = (base.faces(">Z").workplane().transformed(rotate=(0,0,cfg.handRotation))
                     .center(*thPnts[i])
                     .transformed(rotate=(0,0,cfg.tClusterRot[i]))
                     .center(4.5,0)
                     .rect(cfg.hSize[0],cfg.hSize[1])
                     .cutThruAll()
                     )
        else:
            base = (base.faces(">Z").workplane().transformed(rotate=(0,0,cfg.handRotation))
                     .center(*thPnts[i])
                     .transformed(rotate=(0,0,cfg.tClusterRot[i]))
                     .rect(cfg.hSize[0],cfg.hSize[1])
                     .cutThruAll()
                     )

    
    LMThumbPos = GetPosCartesian(tstart, [( cfg.hSize[1]/2, cfg.tClusterRot[1]+270),
                                          ( cfg.hSize[0]/2+cfg.tClusterSpacing/2, cfg.tClusterRot[1]+180),
                                          ( cfg.holeToEdge*1.35, 270+(cfg.tClusterRot[0]+cfg.tClusterRot[1])/2),
                                         ])
    
    
    base = (base.faces(">Z").workplane(centerOption='CenterOfBoundBox')
                .transformed(rotate=(0,0,cfg.handRotation))
                .center(*LMThumbPos)
                .transformed(rotate=(0,0,180+cfg.tClusterRot[0]))
                .rect(baseLength*2,baseLength*2,(False,False))
                .cutThruAll()
                )
    
    if len(cfg.tClusterRot) == 2:
        base = (base.faces(">Z").workplane(centerOption='CenterOfBoundBox')
                    .transformed(rotate=(0,0,cfg.handRotation))
                    .center(*LMThumbPos)
                    .transformed(rotate=(0,0,270+cfg.tClusterRot[1]))
                    .rect(baseLength*2,baseLength*2,(False,False))
                    .cutThruAll()
                    )
    else:
        base = (base.faces(">Z").workplane(centerOption='CenterOfBoundBox')
                    .transformed(rotate=(0,0,cfg.handRotation))
                    .center(*LMThumbPos)
                    .transformed(rotate=(0,0,270+cfg.tClusterRot[-1]*2+cfg.tClusterRot[1]-1))
                    .rect(baseLength*2,baseLength*2,(False,False))
                    .cutThruAll()
                    )
    
    base = cut(base, ">>Y[-3]", moveBy=(0,cfg.holeToEdge*1.2), baseLength=baseLength)
    base = cut(base, "<<Y[-2]", moveBy=(0,cfg.holeToEdge*1.5), rotation=180, baseLength=baseLength)
    base = cut(base, ">>X[-2]", moveBy=(0,cfg.holeToEdge*1.6), rotation=270+cfg.handRotation, baseLength=baseLength)
    base = cut(base, ">>X[-2]", moveBy=(0,cfg.holeToEdge*1.5+cfg.startCorrection ),rotation=270+cfg.handRotation-1.75*cfg.handRotation, baseLength=baseLength)
    base = (base.faces(">Z").vertices("<<X[-2]").workplane(centerOption="CenterOfMass")
                .center(-cfg.handDistance/2,0)
                .transformed(rotate=(0,90,0))
                .split(keepTop=True)
                )
    
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
    
    base = base.faces(">Z").workplane()
    
    base = base.center(base.plane.toLocalCoords(cq.Vector(0,0,0)).x, base.plane.toLocalCoords(cq.Vector(0,0,0)).y)
    base = base.polyline(plstt).close().cutThruAll()
    
    plate = base.mirror(base.faces("<X"), union=True)
    
    tmp = plate.faces(">Z").workplane(centerOption="CenterOfMass")
    
    plate = plate.translate(tmp.plane.toLocalCoords(cq.Vector(0,0,0)))
    
    return plate

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
#     height_mid = 2,
#     height_pcb = 1.6,
#     spacing = (18,17),
#     hSize = (14,14),
#     rows =  3,
#     cols = 5,
#     keysPerCol= ( 3, 3, 3, 3, 2 ),
#     stagger= ( 0, 2, 6, 2,-7+17),
#     colRot= (0,0,0,0,0),
#     tClusterRot= (36, 15),
#     tClusterPos= (1,7),
#     tClusterSpacing= 7,
#     handRotation= 19,
#     handDistance = 25,
#     holeToEdge = 4,
#     doFillet= True,
#     filletSizeLarge= 5,
#     filletSizeSmall= 3,
#     startCorrection = 2.5,
#     outerThumb1u5 = True,
#     upperEdgeOffset = 5,
#     )

# config_highProfileChoc = caseConfig(
#     switchClearance = 5.2,
#     clearanceSafety = 1,
#     wallSafety = .5,
#     wallThickness = 2,
#     heightAbovePlate = 5,
#     cutoutExtra = (0.25, 0.25 )
#     )

# plate = GeneratePlate(config_32)
# show_object(plate)
# GenerateCase(plate, config_highProfileChoc)
