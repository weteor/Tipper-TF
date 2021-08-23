import cadquery as cq

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


plate = bg.GeneratePlate(pCfg)
# plate = bg.doFillet(plate,pCfg)

platef = bg.GeneratePlate(pCfg)
platef = bg.doFillet(platef,pCfg)
#case_top = bg.GenerateCaseTop(platec, pCfg, cCfg)
case_bottom = bg.GenerateCase(platef, cCfg)

def generateCt(plate, platef, cCfg, pCfg):
    
    filletS = 0.4
    filletL = 0.9
    chamferS = 0.4
    
    tButtons = len(pCfg.tClusterRot)
    
    outline = plate.faces(">Z").wires().first().val()
    outline_verts = outline.Vertices()
    outline = outline.fillet2D(pCfg.filletSizeLarge, outline_verts)
    
    ct = (cq.Workplane().add(outline).wires().first()
                        .toPending()
                        .offset2D((cCfg.wallThickness+cCfg.wallSafety))
                        .extrude(cCfg.heightAbovePlate)
                )
    
    
    
    pts = [platef.faces(">Z").wires().item(i+1).val().Center()
            for i in range(platef.faces(">Z").wires().size()-1)]
    
    
    
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
    
    cutout = (cq.Workplane()
                .pushPoints(locs)
                .rect(pCfg.spacing[0]+cCfg.cutoutExtra[0]*2, 
                      (keysCol) * pCfg.spacing[1] + cCfg.cutoutExtra[1]*2))
    
    for i in range(tButtons):
        loc = cq.Location((ptsSrtTX[i]),cq.Vector(0,0,1), -(pCfg.tClusterRot[tButtons-1-i] + pCfg.handRotation))
        cutout = ( cutout.pushPoints([loc])
                         .rect(pCfg.spacing[0] * pCfg.tClusterSize[tButtons-1-i] + cCfg.cutoutExtra[1] * 2,
                               pCfg.spacing[1] + cCfg.cutoutExtra[1] * 2)
                         )
    cutout = cutout.extrude(cCfg.heightAbovePlate)
    
    selector = cq.selectors.BoxSelector( (-300,0,-1), (0,15,cCfg.heightAbovePlate+1))
    invSelector = cq.selectors.InverseSelector(selector)
    cutout = cutout.edges(selector).edges("|Z").fillet(filletS)
    cutout = cutout.edges(invSelector).edges("|Z").fillet(filletL)
    
    ct = ct.cut(cutout.mirror("YZ",union=True))
    
    ct = ct.faces(">Z").wires().first().chamfer(3)
    ct = ct.faces(">Z").wires().first().fillet(3)
    for i in range(6):
        ct = ct.faces(">Z").wires().item(i+1).edges("%LINE").chamfer(chamferS)


    
    return ct
    

ct = generateCt(plate, platef, cCfg, pCfg)

# ct = ct.faces(">Z").workplane().center(0-last.x,-21-last.y).circle(16.5).cutThruAll()

# plate = plate.faces(">Z").workplane().center(0,-21).circle(16).cutThruAll()

pcb_outline = plate.faces("<Z").wires().first().val()
pcb = (cq.Workplane().add(pcb_outline).wires().first()
                     .toPending()
                     .offset2D(-(cCfg.wallThickness+pCfg.holeToEdge-2))
                     .extrude(-pCfg.height_pcb)
                     .translate((0,0,-(pCfg.height_plate+pCfg.height_mid)))
                     )



# case = (case.faces("<Z").wires().first())
show_object(plate, name="Plate", options={"color":(30,30,30)})
show_object(case_bottom, name="Case_bottom", options={"color":(198,196,188)})
show_object(ct, name="Case_top", options={"color":(100,196,188)})
# debug(case.faces("<Z").wires().first().chamfer(1))
# show_object(pcb, name="pcb", options={"color":(30,30,30)})
# ct_ = ct.faces("<Z").wires().first()


# ct_ = ct.shells("
                
#                 ")
# debug(ct_)