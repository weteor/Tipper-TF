import cadquery as cq
import math

from importlib import reload
import mods.boardGen as bg
import mods.configs as cfgs
import mods.common as mc
from copy import copy
import time
from typing import (TypeVar)

explode = False
explode_val = 30

mc = reload(mc)
bg = reload(bg)
cfgs = reload(cfgs)


def generateKeeb(pCfg, cCfg):
    plate = bg.GeneratePlate(pCfg)
    midlayer = bg.GenerateMidLayer(plate, pCfg)
    pcb = bg.GeneratePcb(plate, pCfg)

    case = bg.GenerateCase(plate, cCfg)

    return (plate, midlayer, pcb, case )

T = TypeVar("T", bound="Workplane")

def _getOutline( self: T ) -> T:
    ol = self.wires().first().toPending()
    log(ol)
    self.newObject([ol])

cq.Workplane.getOutline = _getOutline

def GenerateFromOutline(obj, fillet = 0, extrude = 0):
    outline = obj.val()
    ov = outline.Vertices()
    of = outline.fillet2D(fillet,ov)
    
    return cq.Workplane().add(of).wires().first().toPending().extrude(extrude)


# pCfg = cfgs.config_32
pCfg = cfgs.config_32_ap
cCfg = cfgs.config_highProfileChoc


plate, oLine_pcb = bg.GeneratePlate(pCfg)


def generateCt(plate, oLine_pcb, cCfg, pCfg):
    
    filletS = 0.4
    filletL = 1.5
    chamferS = 0.4
    
    tButtons = len(pCfg.tClusterRot)
    
    outline_case = plate.faces(">Z").wires().first().val()
    # outline_verts = outline.Vertices()
    # outline_case = outline.fillet2D(pCfg.filletSizeLarge, outline_verts)
    
    ct = (cq.Workplane().add(outline_case).wires().first().translate((0,0,cCfg.heightAbovePlate))
                        .toPending()
                        .offset2D((cCfg.wallThickness+cCfg.wallSafety))
                        .extrude(-(cCfg.heightAbovePlate+cCfg.switchClearance+cCfg.wallThickness+cCfg.clearanceSafety))
                )
    
    ct = ct.faces(">Z").wires().first().chamfer(3)
    ct = ct.faces(">Z").wires().first().fillet(2)
    ct = ct.faces("<<Z[-2]").edges(">Z").fillet(2)

    outline = oLine_pcb.faces(">Z").wires().first()
    cutout = ( cq.Workplane().add(outline).translate((0,0,-cCfg.switchPlateToPcb))
                             .toPending()
                             .offset2D(cCfg.wallSafety)
                             .extrude(-(cCfg.switchClearance+cCfg.bottomThickness+cCfg.clearanceSafety))
                             )
    ct = ct.cut(cutout)
    
    # outline = plate_outline.faces(">Z").wires().first()
    cutout = ( cq.Workplane().add(outline_case).translate((0,0,-(cCfg.switchClearance+cCfg.wallThickness+cCfg.clearanceSafety)))
                                 .toPending()
                                 .offset2D((cCfg.wallSafety))
                                 .extrude(cCfg.bottomThickness)
                                 )
    bottomCase = ( cq.Workplane().add(outline_case).translate((0,0,-(cCfg.switchClearance+cCfg.wallThickness+cCfg.clearanceSafety)))
                                 .toPending()
                                 .offset2D((cCfg.wallSafety-0.1))
                                 .extrude(cCfg.bottomThickness)
                                 )
    # bottomCase = bottomCase.edges("|Z").fillet(10)
    ct = ct.cut(cutout)
    


    pts = [plate.faces(">Z").wires().item(i+1).val().Center()
    
    for i in range(plate.faces(">Z").wires().size()-1)]
    
    
    
    ptsSrtY = sorted(pts, key= lambda vec: vec.y)
    ptsSrtAX = sorted(ptsSrtY[2*tButtons:], key= lambda vec: vec.x)
    ptsSrtTX = sorted(ptsSrtY[:2*tButtons], key= lambda vec: vec.x)
    
    locs = []
    for i in range(pCfg.cols):
        keysCol = pCfg.keysPerCol[pCfg.cols-1-i]
        low  = ptsSrtAX[sum(pCfg.keysPerCol[pCfg.cols-i:])]
        high = ptsSrtAX[sum(pCfg.keysPerCol[pCfg.cols-i:])+keysCol-1]

        loc = cq.Location((high+low)*0.5, cq.Vector(0,0,1), -pCfg.handRotation+pCfg.colRot[pCfg.cols-1-i])
        locs.append(loc)
    
    cutout = (cq.Workplane("XY", origin=(0,0,-cCfg.switchPlateToPcb))
                .pushPoints(locs)
                .rect(pCfg.spacing[0]+cCfg.cutoutExtra[0]*2, 
                      (keysCol) * pCfg.spacing[1] + cCfg.cutoutExtra[1]*2))
    
    for i in range(tButtons):
        loc = cq.Location((ptsSrtTX[i]),cq.Vector(0,0,1), -(pCfg.tClusterRot[tButtons-1-i] + pCfg.handRotation))
        cutout = ( cutout.pushPoints([loc])
                         .rect(pCfg.spacing[0] * pCfg.tClusterSize[tButtons-1-i] + cCfg.cutoutExtra[1] * 2,
                               pCfg.spacing[1] + cCfg.cutoutExtra[1] * 2)
                         )
    cutout = cutout.extrude(cCfg.heightAbovePlate+cCfg.switchPlateToPcb)

    selector = cq.selectors.BoxSelector( (-300,0,-1), (0,15,cCfg.heightAbovePlate+1))
    invSelector = cq.selectors.InverseSelector(selector)
    cutout = cutout.edges(selector).edges("|Z").fillet(filletS)
    cutout = cutout.edges(invSelector).edges("|Z").fillet(filletL)
    
    ct = ct.cut(cutout.mirror("YZ",union=True))

    for i in range(6):
        ct = ct.faces(">Z").wires().item(i+1).chamfer(chamferS)
        
    locs = []
    locsbc = []
    for i in range(ct.faces("-Z").faces("<<Z[-2]").size()):
        loc = ct.faces("-Z").faces("<<Z[-2]").item(i).val().Center()
        locsbc.append((loc.x, -loc.y))
        locs.append(loc)
        
    ct = ct.pushPoints(locs).circle(cCfg.hDiameter/2).cutBlind(cCfg.hDepth)
    bottomCase = bottomCase.faces("<Z").workplane().pushPoints(locsbc).cboreHole(cCfg.sHoleDiameter,2*cCfg.sHoleDiameter,1)
    
    locs = []
    loc = ct.faces("-Z").faces("<<Z[-3]").faces(">Y").first().val().Center()
    locs.append((loc.x-2.5, -(loc.y -8)))
    
    loc = ct.faces("-Z").faces("<<Z[-3]").faces(">>Y[-2]").first().val().Center()
    locs.append((loc.x-10.5, -(loc.y -10.5)))
    
    loc = ct.faces("-Z").faces("<<Z[-3]").faces("<<Y[-2]").item(1).val().Center()
    locs.append((loc.x-4, -(loc.y +10)))
    
    loc = ct.faces("-Z").faces("<<Z[-3]").faces("<Y").first().val().Center()
    locs.append((loc.x+12.1, -(loc.y +29.6)))
    
    ct = ct.faces("-Z").faces("<<Z[-4]").workplane().pushPoints(locs).circle(cCfg.hDiameter/2).mirrorY().cutBlind(-cCfg.hDepth)
    
    
    
    # ct = ct.pushPoints(locs).circle(cCfg.hDiameter/2+1.3).cutBlind(1)
        
    # locs = []
    # for i in range(7):
    #     loc = ct.faces("-Z").faces("<<Z[-4]").item(i).val().Center()
    #     locspcb.append((loc.x, -loc.y))
    #     locs.append(loc)
    
    # ct = ct.pushPoints(locs).circle(1).cutBlind(5)
    
    # cutout = cq.Workplane()
    # cutout_ = cq.Workplane()
    
    # dist = pCfg.spacing[1] * 0.5 +5
    # x = dist * math.sin(math.radians(180+(pCfg.handRotation + pCfg.tClusterRot[0])))
    # y = dist * math.cos(math.radians(180+(pCfg.handRotation + pCfg.tClusterRot[0])))
    
    # loc = cq.Location((ptsSrtTX[0]),cq.Vector(0,0,1), -(pCfg.tClusterRot[tButtons-1-0] + pCfg.handRotation))
    # cutout = ( cutout.pushPoints([loc])
    #                  .rect(pCfg.spacing[0] * pCfg.tClusterSize[tButtons-1] + cCfg.cutoutExtra[1] * 2 ,
    #                        pCfg.spacing[1] + cCfg.cutoutExtra[1] * 2)
    #                  )
    # cutout = cutout.extrude(cCfg.thumbCutout).translate((x,y,cCfg.heightAbovePlate-cCfg.thumbCutout))
    
    # loc = cq.Location((ptsSrtTX[1]),cq.Vector(0,0,1), -(pCfg.tClusterRot[tButtons-2] + pCfg.handRotation))
    # cutout_ = ( cutout_.pushPoints([loc])
    #                  .rect(pCfg.spacing[0] * pCfg.tClusterSize[tButtons-2] + cCfg.cutoutExtra[1] * 2,
    #                        pCfg.spacing[1] + cCfg.cutoutExtra[1] * 2)
    #                  )
    # cutout_ = cutout_.extrude(cCfg.thumbCutout).translate((x,y,cCfg.heightAbovePlate-cCfg.thumbCutout))
    # # cutout = cutout.extrude(cCfg.thumbCutout).translate((x,y,cCfg.heightAbovePlate-cCfg.thumbCutout))
    
    # cutout = cutout.union(cutout_)
    # ct = ct.cut(cutout.mirror("YZ",union=True))

    
    
    pcb = oLine_pcb.faces(">Z").wires().first().toPending().extrude(-pCfg.height_pcb)
    pcb = pcb.translate((0,0,-cCfg.switchPlateToPcb))
    pcb = pcb.faces("<Z").workplane().pushPoints(locs).circle(cCfg.sHoleDiameter/2).mirrorY().cutThruAll()
        
    

    # ct = ct.pushPoints(locs).circle(1).cutBlind(5)
    
    return ct, bottomCase, pcb
    

ct, cb, pcb = generateCt(plate, oLine_pcb, cCfg, pCfg)

loc = cq.Location(cq.Vector((0,-20,0)))

ct = ct.faces(">Z").workplane().pushPoints([loc]).hole(33)
ct = ct.faces(">Z").wires(cq.selectors.NearestToPointSelector((0,-20,0))).chamfer(0.4)
# plate = plate.faces(">Z").workplane().pushPoints([loc]).hole(32)

# pcb_outline = plate.faces("<Z").wires().first().val()
# pcb = (cq.Workplane().add(pcb_outline).wires().first()
#                      .toPending()
#                      .offset2D(-(cCfg.wallThickness+pCfg.holeToEdge-2))
#                      .extrude(-pCfg.height_pcb)
#                      .translate((0,0,-(pCfg.height_plate+pCfg.height_mid)))
#                      )
outline_case = plate.faces(">Z")
combine = (cq.Workplane().add(outline_case).wires().toPending()
                        .extrude(-20)
                        )

combine = combine.intersect(pcb)

# case = (case.faces("<Z").wires().first())
# show_object(plate, name="Plate", options={"color":(30,30,30)})
show_object(cb, name="Case_bottom", options={"color":(198,196,188)})
show_object(ct, name="Case_top", options={"color":(100,196,188)})
# debug(case.faces("<Z").wires().first().chamfer(1))
show_object(pcb, name="pcb", options={"color":(30,30,30)})
# ct_ = ct.faces("<Z").wires().first()


# ct_ = ct.shells("
                
#                 ")
# debug(ct_)