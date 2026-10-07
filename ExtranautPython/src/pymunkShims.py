import pymunk

class ObjectCircle(pymunk.Circle):
    def setObject(self, object):
        self.object = object
    
    def getObject(self):
        return self.object

def collisionCallback(space, arb):
    for shape in arb.shapes:
        if isinstance(shape, ObjectCircle):
            for shape2 in arb.shapes:
                if shape != shape2:
                    shape.object.handleCollision(shape, shape2, arb.contacts)    