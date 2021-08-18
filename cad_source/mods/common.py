from math import cos,sin,radians
import cadquery as cq

def GetPosCartesian(start, coords):
    tmp = start
    for (l,a) in coords:
        tmp = (tmp[0] + l * cos(radians(a)), tmp[1] + l * sin(radians(a)))
    return tmp

def PolarPolyline(start, coords):
    lines = []
    tmp = start
    lines.append(tmp)
    for (l,a) in coords:
        tmp = (tmp[0] + l * cos(radians(a)), tmp[1] + l * sin(radians(a)))
        lines.append(tmp)
    return lines



def cut(base, vertString, moveBy, baseLength, rotation=0, center=(True,False)):
    return ( base
            .faces(">Z").vertices(vertString).workplane(centerOption="CenterOfMass",)
            .transformed(rotate=(0,0, rotation))
            .move(*moveBy)
            .rect(baseLength*2,baseLength*2,center)
            .cutThruAll()
           )
