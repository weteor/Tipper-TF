import cadquery as cq
import math
import pickle

from importlib import reload
import mods.boardGen as bg
import mods.configs as cfgs
import mods.common as mc
from copy import copy
import time
from typing import (TypeVar)

explode = False
explode_val = 30

changeLower = False

mc = reload(mc)
bg = reload(bg)
cfgs = reload(cfgs)

#tapping term auf 170 mit ignore_mod_tap_interrupt, so hab ich es am laufen, fühlt sich echt natural an bis auf das leichte delay beim tippen, da kommt man aber schnell drum rum
#[12:38 AM]
#und combo term 27ms weil rolling fingers
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

def getInterceptPoint2D(p11, p12, p21, p22):
    x  = -p12.x * p21.x * p11.y
    x +=  p12.x * p22.x * p11.y
    x +=  p11.x * p21.x * p12.y
    x += -p11.x * p22.x * p12.y
    x +=  p11.x * p22.x * p21.y
    x += -p12.x * p22.x * p21.y
    x += -p11.x * p21.x * p22.y
    x +=  p12.x * p21.x * p22.y
    
    xd  = -p21.x * p11.y + p22.x * p11.y + p21.x * p12.y - p22.x * p12.y
    xd +=  p11.x * p21.y - p12.x * p21.y - p11.x * p22.y + p12.x * p22.y
    
    x = x/xd
    
    y = ( p12.y - p11.y ) / (p12.x - p11.x) * (x - p11.x) + p11.y
    
    return (x,y)

# pCfg = cfgs.config_32
pCfg = cfgs.config_32_ap
cCfg = cfgs.config_highProfileChoc
angled = True
plate, oLine_pcb = bg.GeneratePlate(pCfg)

def generateCt(plate, oLine_pcb, cCfg, pCfg):

    if angled:
        # topExtra = 6
        # topAngle = 2.2
        # topOffset = cq.Vector(0,0,1.25)
        topExtra = 6
        topAngle = 1.3
        topOffset = cq.Vector(0,0,0.4)
    else:
        topExtra = 6
        topAngle = 0
        topOffset = cq.Vector(0,0,-0.5)
        
    filletS = 0.3
    filletL = 1
    chamferS = 0.25
    
    offset_s = -0.5
    
    tButtons = len(pCfg.tClusterRot)
    
    outline_case = plate.faces(">Z").wires().first().val()
    # outline_verts = outline.Vertices()
    # outline_case = outline.fillet2D(pCfg.filletSizeLarge, outline_verts)
    
    ct_ = (cq.Workplane().add(outline_case).wires().first().translate((0,0,cCfg.heightAbovePlate+offset_s))
                        .toPending()
                        .offset2D((cCfg.wallThickness+cCfg.wallSafety))
                        .extrude(-(cCfg.heightAbovePlate+offset_s+cCfg.switchClearance+cCfg.bottomThickness+cCfg.clearanceSafety))
                )

    ct = (cq.Workplane().add(outline_case).wires().first().translate((0,0,cCfg.heightAbovePlate))
                        .toPending()
                        .offset2D((cCfg.wallThickness+cCfg.wallSafety))
                        .extrude(-(cCfg.heightAbovePlate+cCfg.switchClearance+cCfg.bottomThickness+cCfg.clearanceSafety))
                )
    
    gndFace = ct.faces(">Z").tag("gndFace")
    
    ct = ct.faces(tag="gndFace").wires().first().toPending().extrude(topExtra)
    merger = cq.Workplane().transformed(offset=(topOffset.x,topOffset.y,cCfg.heightAbovePlate+topOffset.z)).rect(300,300).extrude(-20).rotateAboutCenter((1,0,0), topAngle)
    
    ct = ct.intersect(merger)
    
    selector = cq.selectors.BoxSelector( (-300,-20,-1), (+300,-100,20))
    invSelector = cq.selectors.InverseSelector(selector)

    ct= ct.faces(">Z").wires().first().chamfer(2.5)
    ct_=ct_.faces(">Z").wires().first().chamfer(2.5)
#@+++++++++++
    # debug(ct_)
    # ct = ct.faces(">Z").wires().first().chamfer(2,2.5)
    # ct = ct.faces("<<Z[-2]").edges(">Z").fillet(1)

    outline = oLine_pcb.faces(">Z").wires().first()
    cutout = ( cq.Workplane().add(outline).translate((0,0,-cCfg.switchPlateToPcb))
                             .toPending()
                             .offset2D(cCfg.wallSafety)
                             .extrude(-(cCfg.switchClearance+cCfg.bottomThickness+cCfg.clearanceSafety))
                             )
    ct = ct.cut(cutout)
    
    # outline = plate_outline.faces(">Z").wires().first()
    cutout = ( cq.Workplane().add(outline_case).translate((0,0,-(cCfg.switchClearance+cCfg.bottomThickness+cCfg.clearanceSafety)))
                                 .toPending()
                                 .offset2D((cCfg.wallSafety))
                                 .extrude(cCfg.bottomThickness)
                                 )
    bottomCase = ( cq.Workplane().add(outline_case).translate((0,0,-(cCfg.switchClearance+cCfg.bottomThickness+cCfg.clearanceSafety)))
                                 .toPending()
                                 .offset2D((cCfg.wallSafety-0.1))
                                 .extrude(cCfg.bottomThickness)
                                 )
    wirelipi = ( cq.Workplane().add(outline_case).translate((0,0,-(cCfg.switchClearance+cCfg.clearanceSafety)))
                                 .toPending()
                                 .offset2D((cCfg.wallSafety))
                                 )
    
    wirelipo = ( cq.Workplane().add(outline_case).translate((0,0,-(cCfg.switchClearance+cCfg.clearanceSafety)))
                               .toPending()
                               .offset2D((cCfg.wallSafety-0.75))
                               )
    lip = cq.Workplane().add(cq.Face.makeFromWires(wirelipo.wires().val(), [wirelipi.wires().val()])).wires().toPending().extrude(cCfg.switchClearance+cCfg.bottomThickness+cCfg.clearanceSafety)
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
    cutout = cutout.extrude(cCfg.heightAbovePlate+cCfg.switchPlateToPcb+topExtra)

    selector = cq.selectors.BoxSelector( (-300,0,-1), (0,15,cCfg.heightAbovePlate+1+topExtra))
    invSelector = cq.selectors.InverseSelector(selector)
    cutout = cutout.edges(invSelector).edges("|Z").fillet(filletL)

    cutout = cutout.edges(selector).edges("|Z").fillet(filletS)

    ct = ct.cut(cutout.mirror("YZ",union=True))
    
    sel = cq.selectors.NearestToPointSelector((0,0,8))
    ct.faces(sel).tag("Top")
    
    for i in [1,2,3,4,5,6]:
        ct = ct.faces(tag="Top").wires().item(i).chamfer(chamferS)
    
    pos = ct.faces("-Z").faces("<Z").edges("<Y").vertices("<X").val().toTuple()
    ct = (ct.faces("-Z").faces(">Z")
                        .pushPoints([(pos[0]-7.3, pos[1]+33.5)])
                        .circle(3.5).mirrorY()
                        .extrude(-(cCfg.switchClearance+cCfg.clearanceSafety))
                        )

    locs = []
    locsbc = []
    for i in range(ct.faces("-Z").faces("<<Z[-2]").size()):
        loc = ct.faces("-Z").faces("<<Z[-2]").item(i).val().Center()
        locsbc.append((loc.x, -loc.y))
        locs.append(loc)
   
    ct = ct.pushPoints(locs).circle(cCfg.hDiameter/2).cutBlind(cCfg.hDepth)
    bottomCase = bottomCase.faces("<Z").workplane().pushPoints(locsbc).hole(cCfg.sHoleDiameter)#.cboreHole(cCfg.sHoleDiameter,2*cCfg.sHoleDiameter,0.75)
    
    locs = []
    loc = ct.faces("-Z").faces("<<Z[-3]").faces(">Y").first().val().Center()
    # locs.append((loc.x-10.5, -(loc.y -(cCfg.wallSafety))))
    locs.append((loc.x-10.497, -(loc.y-12.482)))
    
    loc = ct.faces("-Z").faces("<<Z[-3]").faces(">>Y[-2]").first().val().Center()
    locs.append((loc.x-9.390, -(loc.y-1.220)))
    
    loc = ct.faces("-Z").faces("<<Z[-3]").faces("<<Y[-2]").item(1).val().Center()
    locs.append((loc.x+12.441, -(loc.y +6.649)))
    
    loc = ct.faces("-Z").faces("<<Z[-3]").faces("<Y").item(1).val().Center()
    locs.append((loc.x+7, -(loc.y +(17.15+cCfg.wallSafety))))
    ct = ct.faces("-Z").faces("<<Z[-3]").workplane().pushPoints(locs).circle(cCfg.hDiameter/2).mirrorY().cutBlind(-cCfg.hDepth)
    
    pcb = oLine_pcb.faces(">Z").wires().first().toPending().extrude(-pCfg.height_pcb)
    pcb = pcb.translate((0,0,-cCfg.switchPlateToPcb))
    pcb = pcb.faces("<Z").workplane().pushPoints(locs).circle(cCfg.sHoleDiameter/2).mirrorY().cutThruAll()
    
    ct = ct.union(lip)
    

    # ct = ct.pushPoints(locs).circle(1).cutBlind(5)
    
    return ct, bottomCase, pcb, lip
    

ct, cb, pcb, lip = generateCt(plate, oLine_pcb, cCfg, pCfg)

# loc = cq.Location(cq.Vector((0,-19.8,20)))
# cutout = cq.Workplane().pushPoints([loc]).circle(16.5).extrude(-50)
loc = cq.Location(cq.Vector((0,-19,20)),cq.Vector((0,0,1)),45)
cutout = cq.Workplane().pushPoints([loc]).rect(27.6,27.6).extrude(-50).edges("|Z").fillet(1)

ct = ct.cut(cutout)


# ct = ct.faces(">Z").workplane().pushPoints([loc]).hole(33)
sel = cq.selectors.NearestToPointSelector((0,0,8))
ct = ct.faces(sel).wires(cq.selectors.NearestToPointSelector((0,-20,0))).chamfer(0.6)
plate = plate.faces(">Z").workplane().pushPoints([loc]).hole(32)

outline_case = plate.faces(">Z")
combine = (cq.Workplane().add(outline_case).wires().toPending()
                        .extrude(-20)
                        )

combine = combine.intersect(pcb)


locc = ct.faces("+Y").faces(">>Y[-2]").val().Center()

if angled:
    loc = ((0, -(locc.z + cCfg.switchPlateToPcb)-0.1, -cCfg.wallThickness))
    ct = ct.faces("+Y").faces(">>Y[-2]").workplane().pushPoints([loc]).rect(12,6).cutBlind(cCfg.wallThickness)
    # ct = ct.edges("|Y").fillet(1.5)
else:
    loc = ((0, -(locc.z + cCfg.switchPlateToPcb)-0.8, -cCfg.wallThickness))
    ct = ct.faces("+Y").faces(">>Y[-2]").workplane().pushPoints([loc]).rect(12,6).cutBlind(cCfg.wallThickness)

ct = ct.faces("+Y").faces(">>Y[-2]").workplane().pushPoints([loc]).rect(20,8).cutBlind(-12+cCfg.wallSafety, 8)

t = cq.Workplane().pushPoints([(0,0)]).rect(31,41)
ct = ( ct.faces("-Z").faces("<<Z[-3]").workplane()
          .add(t).translate((0,-12.5+0.2,-cCfg.switchPlateToPcb)).toPending().extrude(5.2)
          )
ct = (ct.faces("-Z")
        .faces("<<Z[-3]")
        .faces(cq.selectors.NearestToPointSelector((0,0,0))).tag("theFace")
        .rect(35, 45)
        # .rect(35, 26)
        .extrude(-5.2)
        )
ct = ct.faces(tag="theFace").rect(35,16.5,(True,False)).cutBlind(-5.2)
ct = ct.faces(tag="theFace").rect(24,30,(True,False)).cutBlind(-5.2)
ct = ct.faces(tag="theFace").rect(35,-45,(True,False)).cutBlind(-5.2)
ct = ct.faces(tag="theFace").rect(6,-22.5,(True,False)).extrude(-5.2)
ct = ct.faces(tag="theFace").rect(35,-10,(True,False)).extrude(-5.2)
ct = ct.faces(tag="theFace").rect(35,-5,(True,False)).cutBlind(-5.2)
ct = ct.faces(tag="theFace").rect(-17.5, 22.5,(False,False)).cutBlind(-5.2)
ct = ct.faces(tag="theFace").rect(31,41).cutBlind(-5.2)
# ct = ct.faces(tag="theFace").rect(60,60,(True, False)).extrude(-5.2)
# ct = ct.faces(tag="theFace").rect(30,60,(True, False)).extrude(1.5)
# ct = ct.faces(tag="theFace").rect(35,14).cutBlind(-5.2)

ct = ct.faces("<Z").wires().first().chamfer(0.75)

pos = combine.faces(">Z").edges("|X").edges(">>Y[-3]").vertices("<X").val().Center()

locs = []
locs.append((   0, pos.y))
locs.append((   0, pos.y + cCfg.wallSafety-0.2))
locs.append((-7.5, pos.y + cCfg.wallSafety-0.2))
locs.append((locs[-1][0]+10*math.sin(math.radians(180+70)), locs[-1][1]+10*math.cos(math.radians(180+70))))
locs.append((0,locs[-1][1]))

combine = combine.faces(">Z").workplane().polyline(locs).mirrorY().extrude(-pCfg.height_pcb)
combine = combine.cut(ct)

# show_object(combine, name="Combine", options={"color":(30,30,30)})
# show_object(cb, name="Case_bottom", options={"color":(198,196,188)})
show_object(ct, name="Case_top", options={"color":(100,196,188)})
# # show_object(pcb, name="pcb", options={"color":(30,30,30)})

