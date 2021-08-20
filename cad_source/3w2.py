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

    tButtons = len(pCfg.tClusterRot)
    # enclose_ = ct.faces(">Z").workplane().polyline(lines).close().wires().val()
    # f = cq.Face.makeFromWires(enclose_)
    # verts = enclose_.Vertices()
    # enclose_=enclose_.fillet2D(1,verts)
    
    outline = plate.faces(">Z").wires().first().val()
    outline_verts = outline.Vertices()
    outline = outline.fillet2D(pCfg.filletSizeLarge, outline_verts)
    # debug(cq.Workplane().add(of).wires().first().toPending().extrude(2))
    
    
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
    
    for i in range(pCfg.cols):
        log(i)
        keysCol = pCfg.keysPerCol[pCfg.cols-1-i]
        low  = ptsSrtAX[sum(pCfg.keysPerCol[pCfg.cols-i:])]
        high = ptsSrtAX[sum(pCfg.keysPerCol[pCfg.cols-i:])+keysCol-1]

        log("whiiiienst\n")
        loc = cq.Location((high+low)*0.5, cq.Vector(0,0,1), -pCfg.handRotation+pCfg.colRot[pCfg.cols-1-i])
        ct = ( ct.pushPoints([loc])
                 .rect(pCfg.spacing[0]+cCfg.cutoutExtra[0]*2, 
                       (keysCol) * pCfg.spacing[1] + cCfg.cutoutExtra[1]*2)
                 .cutThruAll()
                 )
    

    return ct
    
    left  = -pCfg.handRotation + 180
    down  = -pCfg.handRotation + 270
    right = -pCfg.handRotation 
    up    = -pCfg.handRotation +  90
    
    stag = pCfg.stagger
    spc  = pCfg.spacing
    yDiff = pCfg.spacing[1] - pCfg.hSize[1]
    kpc = pCfg.keysPerCol
    hs  = pCfg.hSize[1]
    coe = (cCfg.cutoutExtra[0]+(spc[0]-pCfg.hSize[0])/2, cCfg.cutoutExtra[1]+(spc[1]-pCfg.hSize[1])/2)
    
    stPnt = mc.GetPosCartesian((ptsSrtAX[0].x, ptsSrtAX[0].y),
                                   [( pCfg.hSize[0]/2+coe[0], left + pCfg.colRot[pCfg.cols-1] ),#
                                    ( pCfg.hSize[1]/2+coe[1], down + pCfg.colRot[pCfg.cols-1])])#
    
    stg_now  = stag[pCfg.cols-1] - (pCfg.rows - kpc[pCfg.cols-1]) * spc[1]
    stg_next = stag[pCfg.cols-2] - (pCfg.rows - kpc[pCfg.cols-2]) * spc[1]
    
    if (stg_now < stg_next):
        upStag = True
    else :
        upStag = False
    
    lines = []
    lines.append(stPnt)
    lines.append(mc.GetPosCartesian(lines[-1],
                                    [(coe[1]*2+spc[1]*(kpc[pCfg.cols-1]-1)+hs, up + pCfg.colRot[pCfg.cols-1])]))
        
    for i in range(pCfg.cols):
        stg_now  = stag[pCfg.cols-1-i] - (pCfg.rows - kpc[pCfg.cols-1-i]) * spc[1]
        stg_next = stag[pCfg.cols-2-i] - (pCfg.rows - kpc[pCfg.cols-2-i]) * spc[1]
        col_rot      = pCfg.colRot[pCfg.cols-1-i]
        col_rot_next = pCfg.colRot[pCfg.cols-2-i]
        if (stg_now < stg_next):
            log(" < ")
            if upStag: 
                log("true")
                lines.append(mc.GetPosCartesian(lines[-1],
                                                [(spc[0], right + col_rot)]))
            else:
                log("false")
                lines.append(mc.GetPosCartesian(lines[-1], 
                                                [(hs, right + col_rot)]))
                upStag = True;
            
        else:
            log(" > ")
            if upStag:
                lines.append(mc.GetPosCartesian(lines[-1], 
                                                [(hs+2*coe[0], right + col_rot)]))
                upStag = False
            else:
                lines.append(mc.GetPosCartesian(lines[-1], 
                                                [(spc[0], right + col_rot)]))
                
            sw = True
    
        lines.append(mc.GetPosCartesian(lines[-1], 
                                        [((stg_next - stg_now), up + col_rot_next)]))
    
    del lines[-1]
    
    debug(ct.faces(">Z").workplane().polyline(lines))
    return ct

    lines.append(mc.GetPosCartesian(lines[-1],
                                    [(coe[1]*2+spc[1]*(kpc[0]-1)+hs, down)]))
    
    if (stag[0] < stag[1]):
        upStag = False
    else :
        upStag = True
    
    for i in range(pCfg.cols):
        stg_now  = stag[i] - (pCfg.rows - kpc[i]) * spc[1]
        stg_next = stag[(i+1)%pCfg.cols] - (pCfg.rows - kpc[(i+1)%pCfg.cols]) * spc[1]
        if (stg_now < stg_next):
            if upStag:        
                lines.append(mc.GetPosCartesian(lines[-1], 
                                                [(spc[0], left)]))
            else:
                lines.append(mc.GetPosCartesian(lines[-1], 
                                                [(hs+2*coe[0], left)]))
                upStag = True;
            
        else:
            if upStag:
                lines.append(mc.GetPosCartesian(lines[-1],
                                                [(2*spc[0]-hs-2*coe[0], left)]))
                upStag = False
            else:
                lines.append(mc.GetPosCartesian(lines[-1],
                                                [(hs+2*coe[0], left)]))
                # lines.append(mc.GetPosCartesian(lines[-1],
                #                                 [(spc[0], left)]))
                
            sw = True
    
        lines.append(mc.GetPosCartesian(lines[-1], 
                                        [(stag[(i+1)%pCfg.cols] - stag[i], up)]))
    
    del lines[-1]
    del lines[-1]
    outline = plate.faces(">Z").wires().first().val()
    outline_verts = outline.Vertices()
    outline = outline.fillet2D(pCfg.filletSizeLarge, outline_verts)
    
    switch_cutout = cq.Workplane().polyline(lines)
    debug(switch_cutout)
    
    # enclose_ = ct.faces(">Z").workplane().polyline(lines).close().wires().val()
    # f = cq.Face.makeFromWires(enclose_)
    # verts = enclose_.Vertices()
    # enclose_=enclose_.fillet2D(1,verts)
    
    ct = ct.faces(">Z").workplane().polyline(lines).close().mirrorY().cutBlind(-cCfg.heightAbovePlate)
    
    # 'debug(ct)
    last = cq.Vector((0,0,0))
    for i,vec in enumerate(ptsSrtTX[:tButtons]):
            next = vec-last
            last = vec
            
            if i == 0:
                ct = (ct.faces(">Z")
                        .workplane()
                        .center(next.x, next.y)
                        .transformed(rotate=(0,0,-pCfg.handRotation-pCfg.tClusterRot[-1-i]))
                        .rect(pCfg.hSize[0]+2*coe[0]+0.5*spc[0],
                              pCfg.hSize[1]+2*coe[1])
                        .cutBlind(-cCfg.heightAbovePlate)
                        )
            else:
                ct = (ct.faces(">Z")
                        .workplane()
                        .center(next.x, next.y)
                        .transformed(rotate=(0,0,-pCfg.handRotation-pCfg.tClusterRot[-1-i]))
                        .rect(pCfg.hSize[0]+2*coe[0],
                              pCfg.hSize[1]+2*coe[1])
                        .cutBlind(-cCfg.heightAbovePlate)
                        )
            
    for i,vec in enumerate(ptsSrtTX[tButtons:]):
        next = vec-last
        last = vec
        
        if i == len(ptsSrtTX[tButtons:])-1:
            ct = (ct.faces(">Z")
                    .workplane()
                    .center(next.x, next.y)
                    .transformed(rotate=(0,0,pCfg.handRotation+pCfg.tClusterRot[i]))
                    .rect(pCfg.hSize[0]+2*coe[0]+0.5*spc[0],
                          pCfg.hSize[1]+2*coe[1])
                    .cutBlind(-cCfg.heightAbovePlate)
                    ) 
        else:
            ct = (ct.faces(">Z")
                .workplane()
                .center(next.x, next.y)
                .transformed(rotate=(0,0,pCfg.handRotation+pCfg.tClusterRot[i]))
                .rect(pCfg.hSize[0]+2*coe[0],
                      pCfg.hSize[1]+2*coe[1])
                .cutBlind(-cCfg.heightAbovePlate)
                ) 
    
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
# show_object(ct, name="Case_top", options={"color":(100,196,188)})
# debug(case.faces("<Z").wires().first().chamfer(1))
# show_object(pcb, name="pcb", options={"color":(30,30,30)})
# ct_ = ct.faces("<Z").wires().first()


# ct_ = ct.shells("
                
#                 ")
# debug(ct_)