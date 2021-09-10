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

plate, oLine_pcb = bg.GeneratePlate(pCfg)

def generateCt(plate, oLine_pcb, cCfg, pCfg):
    
    filletS = 0.3
    filletL = 1
    chamferS = 0.3
    
    tButtons = len(pCfg.tClusterRot)
    
    outline_case = plate.faces(">Z").wires().first().val()
    # outline_verts = outline.Vertices()
    # outline_case = outline.fillet2D(pCfg.filletSizeLarge, outline_verts)
    
    ct = (cq.Workplane().add(outline_case).wires().first().translate((0,0,cCfg.heightAbovePlate))
                        .toPending()
                        .offset2D((cCfg.wallThickness+cCfg.wallSafety))
                        .extrude(-(cCfg.heightAbovePlate+cCfg.switchClearance+cCfg.bottomThickness+cCfg.clearanceSafety))
                )
    
    selector = cq.selectors.BoxSelector( (-300,-20,-1), (+300,-100,20))
    invSelector = cq.selectors.InverseSelector(selector)
    ct= ct.faces(">Z").wires().first().chamfer(2,2.5)
    # return ct, None, None
    # ct = ct.faces(">Z").wires().first().chamfer(2,2.5)
    # ct = ct.faces(">Z").wires().first().fillet(2)
    ct = ct.faces("<<Z[-2]").edges(">Z").fillet(1)

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
    cutout = cutout.edges(invSelector).edges("|Z").fillet(filletL)
    # ct = ct.cut(cutout.)
    cutout = cutout.edges(selector).edges("|Z").fillet(filletS)

    # pointytop = cutout.edges(selector).edges("|Z").vertices(">Z").rect(5,5).extrude(5)
    # pointytop = 
    # square = 
    # return ct, None, None
    ct = ct.cut(cutout.mirror("YZ",union=True))
    

    for i in [2,5]:
        ct = ct.faces(">Z").wires().item(i+1).chamfer(chamferS)
        
    pos = ct.faces("-Z").faces("<Z").edges("<Y").vertices("<X").val().toTuple()
    ct = (ct.faces("-Z").faces(">Z")
                        .pushPoints([(pos[0]-7, pos[1]+34.25)])
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
    locs.append((loc.x-10.5, -(loc.y -(cCfg.wallSafety))))
    
    loc = ct.faces("-Z").faces("<<Z[-3]").faces(">>Y[-2]").first().val().Center()
    locs.append((loc.x-10.5, -(loc.y -(10.5+cCfg.wallSafety))))
    
    loc = ct.faces("-Z").faces("<<Z[-3]").faces("<<Y[-2]").item(1).val().Center()
    locs.append((loc.x+8.5, -(loc.y +(4+cCfg.wallSafety))))
    
    loc = ct.faces("-Z").faces("<<Z[-3]").faces("<Y").item(1).val().Center()
    locs.append((loc.x+3.75, -(loc.y +(6+cCfg.wallSafety))))
    
    ct = ct.faces("-Z").faces("<<Z[-3]").workplane().pushPoints(locs).circle(cCfg.hDiameter/2).mirrorY().cutBlind(-cCfg.hDepth)
    
    pcb = oLine_pcb.faces(">Z").wires().first().toPending().extrude(-pCfg.height_pcb)
    pcb = pcb.translate((0,0,-cCfg.switchPlateToPcb))
    pcb = pcb.faces("<Z").workplane().pushPoints(locs).circle(cCfg.sHoleDiameter/2).mirrorY().cutThruAll()
        
    

    # ct = ct.pushPoints(locs).circle(1).cutBlind(5)
    
    return ct, bottomCase, pcb
    

ct, cb, pcb = generateCt(plate, oLine_pcb, cCfg, pCfg)

loc = cq.Location(cq.Vector((0,-20,0)))

ct = ct.faces(">Z").workplane().pushPoints([loc]).hole(33)
ct = ct.faces(">Z").wires(cq.selectors.NearestToPointSelector((0,-20,0))).chamfer(0.4)
plate = plate.faces(">Z").workplane().pushPoints([loc]).hole(32)

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

loc = ((0, -cCfg.heightAbovePlate-cCfg.switchPlateToPcb, -cCfg.wallThickness))
locc = ct.faces("+Y").faces(">>Y[-2]").val().Center()
ct = ct.faces("+Y").faces(">>Y[-2]").workplane().pushPoints([loc]).rect(12,6).cutBlind(cCfg.wallThickness)
ct = ct.edges("|Y").fillet(1)

ct = ct.faces("+Y").faces(">>Y[-2]").workplane().pushPoints([loc]).rect(15,6).cutBlind(-10+cCfg.wallSafety, 6)

t = cq.Workplane().pushPoints([(0,0)]).rect(31,41)
ct = ( ct.faces("-Z").faces("<<Z[-3]").workplane()
          .add(t).translate((0,-12.5,-cCfg.switchPlateToPcb)).toPending().extrude(5.2)
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
ct = ct.faces(tag="theFace").rect(31,41).cutBlind(-5.2)
# ct = ct.faces(tag="theFace").rect(60,60,(True, False)).extrude(-5.2)
# ct = ct.faces(tag="theFace").rect(30,60,(True, False)).extrude(1.5)
# ct = ct.faces(tag="theFace").rect(35,14).cutBlind(-5.2)

ct = ct.faces("<Z").wires().first().chamfer(0.5)


sel=cq.selectors.BoxSelector((-40,-30,5),(0,-80, 2))
wires = ct.faces(sel).edges(">>Z[-3]")

sel = cq.selectors.NearestToPointSelector((-50,-40,0))
startedge = ct.faces(">Z").wires(sel).edges("<<X[-2]")
p11 = startedge.vertices("<X").val().Center()
p12 = startedge.vertices(">X").val().Center()
p21 = wires.edges("<<X[-1]").vertices("<X").val().Center()
p22 = cq.Vector(p21.x + math.sin(math.radians(270+21)), p21.y + math.cos(math.radians(270+21)), p21.z )

Intpnt = getInterceptPoint2D(p11,p12,p21,p22)
contactLow = wires.edges("<<X[-1]").vertices("<X").val().Center()
contactHigh = p11 + cq.Vector(28.7*math.sin(math.radians(90+21)),28.7*math.cos(math.radians(90+21)),0)

verts = []
verts.append(contactLow)
verts.append(cq.Vector(Intpnt[0], Intpnt[1], p21.z))
verts.append(p11)
verts.append(contactHigh)

wirelist = []
for i in range(len(verts)):
    wirelist.append(cq.Edge.makeLine(verts[i], verts[(i+1)%len(verts)]))

cutout = cq.Workplane(cq.Wire.assembleEdges(wirelist)).wires().first().toPending().extrude(5).mirror("YZ", union=True)
ct = ct.cut(cutout)

sel = cq.selectors.NearestToPointSelector((-20,-50,0))
startedge = ct.faces(">Z").wires(sel).edges(">>X[-2]")
p11 = startedge.vertices("<X").val().Center()
p12 = startedge.vertices(">X").val().Center()
p21 = wires.edges("<<X[-1]").vertices("<X").val().Center()
p22 = wires.edges("<<X[-1]").vertices(">X").val().Center()

Intpnt = cq.Vector(*getInterceptPoint2D(p11,p12,p21,p22),p21.z)

verts = []
verts.append(contactHigh)
verts.append(p11)
verts.append(p22)
# verts.append(cq.Vector(p21.x, p21.y, p22.z))

wirelist = []
for i in range(len(verts)):
    wirelist.append(cq.Edge.makeLine(verts[i], verts[(i+1)%len(verts)]))

cutout = cq.Workplane(cq.Wire.assembleEdges(wirelist)).wires().first().toPending().extrude(5).mirror("YZ", union=True)
ct = ct.cut(cutout)

verts = []
verts.append(contactHigh)
# verts.append(p11)
verts.append(p22)
verts.append(cq.Vector(p21.x, p21.y, p22.z))

wirelist = []
for i in range(len(verts)):
    wirelist.append(cq.Edge.makeLine(verts[i], verts[(i+1)%len(verts)]))
    
cutout = cq.Workplane(cq.Wire.assembleEdges(wirelist)).wires().first().toPending().extrude(5).mirror("YZ", union=True)
ct = ct.cut(cutout)


p21 = wires.edges("<<X[-3]").vertices("<X").val().Center()
p22 = wires.edges("<<X[-3]").vertices(">X").val().Center()

verts = []
verts.append(p21)
verts.append(p11)
verts.append(p11+cq.Vector(20,0,0))
verts.append(p21+cq.Vector(20,0,0))

wirelist = []
for i in range(len(verts)):
    wirelist.append(cq.Edge.makeLine(verts[i], verts[(i+1)%len(verts)]))
    
cutout = cq.Workplane(cq.Wire.assembleEdges(wirelist)).wires().first().toPending().extrude(5).mirror("YZ", union=True)
ct = ct.cut(cutout)

contactLow = Intpnt
contactHigh = p11 

wirelist = []
# wirelist.append(wires.edges("<<X[-2]").val())
wirelist.append(cq.Edge.makeLine(wires.edges("<<X[-2]").vertices(">X").val().Center(), 
                                 wires.edges("<<X[-2]").vertices("<X").val().Center()))
wirelist.append(cq.Edge.makeLine(wires.edges("<<X[-2]").vertices("<X").val().Center(), p11))
wirelist.append(cq.Edge.makeLine(p11, wires.edges("<<X[-2]").vertices(">X").val().Center()))

cutout = cq.Workplane(cq.Wire.assembleEdges(wirelist)).wires().first().toPending().extrude(5).mirror("YZ", union=True)
ct = ct.cut(cutout)

wirelist = []
# wirelist.append(wires.edges("<<X[-2]").val())
wirelist.append(cq.Edge.makeLine(wires.edges("<<X[-2]").vertices(">X").val().Center(), 
                                 wires.edges("<<X[-2]").vertices("<X").val().Center()))
wirelist.append(wires.edges("<<X[-2]").val())

cutout = cq.Workplane(cq.Wire.assembleEdges(wirelist)).wires().first().toPending().extrude(5).mirror("YZ", union=True)
ct = ct.cut(cutout)

sel = cq.selectors.BoxSelector((-70,-30,5),(-60,-80, 2))


verts = []
verts.append(ct.faces(sel).vertices("<Z").val().Center())
verts.append(ct.faces(sel).vertices(">Z").vertices(">Y").val().Center())
verts.append(ct.faces(sel).vertices(">Z").vertices(">Y").val().Center()- cq.Vector(20*math.sin(math.radians(90+21)),20*math.cos(math.radians(90+21)),-2))
verts.append(ct.faces(sel).vertices("<Z").val().Center() - cq.Vector(20*math.sin(math.radians(90+21)),20*math.cos(math.radians(90+21)),-2))
# verts.append(ct.faces(sel).vertices(">Z").vertices("<Y").val().Center() - cq.Vector(60*math.sin(math.radians(90+21)),60*math.cos(math.radians(90+21))))

wirelist = []
for i in range(len(verts)):
    wirelist.append(cq.Edge.makeLine(verts[i], verts[(i+1)%len(verts)]))
    
debug(wirelist)
cutout = cq.Workplane(cq.Wire.assembleEdges(wirelist)).wires().first().toPending().extrude(5).mirror("YZ", union=True)
ct = ct.cut(cutout)

# midpnt = ct.faces("<<Y[-13]").edges(">Z").vertices("<X").val().Center()

# sel = cq.selectors.NearestToPointSelector((-50,-40,0))
# startpntL = ct.faces(">Z").edges(sel).vertices("<X").val().Center()

# sel = cq.selectors.NearestToPointSelector((-20,-50,0))
# startpntR = ct.faces(">Z").edges(sel).vertices("<X").val().Center()

# cutout = ( cq.Workplane()
#              .transformed(offset = startpntL)
#              .transformed(offset = cq.Vector(1*math.sin(math.radians(270+21)),1*math.cos(math.radians(270+21)),0), 
#                           rotate = cq.Vector(0,0,-21))
#              .transformed(offset = cq.Vector(0,1,0), rotate = cq.Vector(13.1,0,0))
#              )
# midpnt_local = cutout.plane.toLocalCoords(midpnt)
# pnts = []
# pnts.append( (0,0) )
# pnts.append( (28.68,0) )
# pnts.append( ( midpnt_local.x, midpnt_local.y))
#                # pnts[-1][1]+ 10*math.cos(math.radians(180+7.5))))
# pnts.append( ( 10*math.sin(math.radians(180)), #+15)),
#                -1+ 10*math.cos(math.radians(180))))#~+15))))
# pnts.append( (0,-1) )
# debug(cutout.polyline(pnts).close())
# ct = ct.cut(cutout.polyline(pnts).close().extrude(5).mirror("YZ", union=True))


# cutout = ( cq.Workplane()
#               .transformed(offset = startpntR)
#               .transformed(offset = cq.Vector(1*math.sin(math.radians(270+36)),1*math.cos(math.radians(270+36)),0), 
#                             rotate = cq.Vector(0,0,-36))
#               .transformed(offset = cq.Vector(0,1,0), rotate = cq.Vector(13.1,0,0))
#               )

# midpnt_local = cutout.plane.toLocalCoords(midpnt)
# pnts = []
# pnts.append( (0,0) ) 
# pnts.append( (-1.18,0))
# pnts.append( (midpnt_local.x, midpnt_local.y))
# pnts.append( ( 18.5+ 10*math.sin(math.radians(180)),#-15)),
#               -1 + 10*math.cos(math.radians(180))#-15))
#               )
#             )
# pnts.append( (18.5,0) )
# debug(cutout.polyline(pnts).close())

# ct = ct.cut(cutout.polyline(pnts).close().extrude(5).mirror("YZ", union=True))


# debug(cutout.polyline(pnts).close())


# # debug(cutout.rotateAboutCenter((1,0,0), 13.25).extrude(5).rotateAboutCenter((0,0,1),-21).translate((math.sin(math.radians(21)),math.cos(math.radians(21)))))
# ct = ct.cut(cutout.rotateAboutCenter((1,0,0), 10.6).extrude(5).rotateAboutCenter((0,0,1),-21).translate((3*math.sin(math.radians(21)),3*math.cos(math.radians(21)))))


pos = combine.faces(">Z").edges("|X").edges(">>Y[-3]").vertices("<X").val().Center()

locs = []
locs.append((   0, pos.y))
locs.append((   0, pos.y + cCfg.wallSafety-0.2))
locs.append((-7.5, pos.y + cCfg.wallSafety-0.2))
locs.append((locs[-1][0]+10*math.sin(math.radians(180+70)), locs[-1][1]+10*math.cos(math.radians(180+70))))
locs.append((0,locs[-1][1]))

combine = combine.faces(">Z").workplane().polyline(locs).mirrorY().extrude(-pCfg.height_pcb)
combine = combine.cut(ct)

# t = cq.Workplane().pushPoints([(0,-35)]).rect(17.55,23.35)
# ct = ( ct.faces("-Z").faces("<<Z[-3]").workplane()
#           .add(t).translate((0,-12.5,-cCfg.switchPlateToPcb)).toPending().extrude(4.2)
          # )
# show_object(combine, name="Combine", options={"color":(30,30,30)})
show_object(cb, name="Case_bottom", options={"color":(198,196,188)})
show_object(ct, name="Case_top", options={"color":(100,196,188)})
# show_object(pcb, name="pcb", options={"color":(30,30,30)})

