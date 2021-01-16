from WindowsForms import Graphics, Form, DrawingObject, SolidBrush, Pen
import threading
import time
import math
from random import random

isClosing = False
hasResponded = False

GRAVITY = 0.015

def wndProc(hWnd, message, wParam, lParam):
    if message == Form.WM_CLOSE:
        global isClosing
        global hasResponded

        print("Closing graphics thread...")
        isClosing = True
        while hasResponded == False:
            time.sleep(0.1)

        print("Destroying Window")
        Form.postQuitMessage(0)

    else:
        return Form.defWndProc(hWnd, message, wParam, lParam)

    return 0

Form1 = Form(wndProc, u'Fireworks', None, Form.BLACK_BRUSH)
Form1.show()

def graphicsLoop(hWindow):
    global isClosing        #declare variables as global so that they can be used across both threads
    global hasResponded

    print("Graphics loop has been initiated.")

    clientRect = Form1.getClientRect()

    g2 = Form1.createGraphics()

    g = Graphics.fromMemory(g2, (clientRect[2], clientRect[3]))

    penID = None
    brushID = None

    class Vector2f:
        def __init__(self, x, y):
            self.x = x
            self.y = y

        @staticmethod
        def empty():
            return Vector2f(0, 0)

        def add(self, v):
            return Vector2f(self.x + v.x, self.y + v.y)

        def sub(self, v):
            return Vector2f(self.x - v.x, self.y - v.y)

        def amplify(self, mag):
            return Vector2f(self.x * mag, self.y * mag)

        def getLength(self):
            return math.sqrt(self.x * self.x + self.y * self.y)

        def div(self, n):
            return Vector2f(self.x / n, self.y / n)

        def rotate(self, rad):
            length = self.getLength()
            angle = (self.y + length) * length * 2 * math.pi
            if self.x > 0:
                angle -= rad
            else:
                angle += rad
            return Vector2f(-math.sin(angle) * length, -math.cos(angle) * length)

    class FireworkParticle:
        def __init__(self, vel):
            self.pos = Vector2f.empty
            self.vel = vel
            color = color = Graphics.rgb(math.floor(random() * 255), math.floor(random() * 255), math.floor(random() * 255))
            self.pen = Pen(Pen.PS_SOLID, 1, color)
            self.brush = SolidBrush(color)

        def update(self):
            self.pos = self.pos.add(self.vel)
            self.vel.y += GRAVITY

        def render(self):
            g.replaceDrawingObject(penID, self.pen)
            g.replaceDrawingObject(brushID, self.brush)
            g.ellipse((int(self.pos.x - 5), int(self.pos.y - 5), int(self.pos.x + 5), int(self.pos.y + 5)))
    
    class Firework:
        def __init__(self):
            self.pos = Vector2f(random() * clientRect[2], clientRect[3])
            self.vel = random() * 3 + 1.5
            color = Graphics.rgb(math.floor(random() * 255), math.floor(random() * 255), math.floor(random() * 255))
            self.pen = Pen(Pen.PS_SOLID, 1, color)
            self.brush = SolidBrush(color)
            self.freeFallDetector = False
            self.expObjects = []
            i = 0
            rotVector = Vector2f(0, 1)
            while True:
                self.expObjects.append(FireworkParticle(rotVector.rotate(random() * math.pi * 2)))
                if i == 5:
                    break
                i += 1
        
        def update(self):
            if self.freeFallDetector == False:
                self.pos.y -= self.vel
                self.vel -= GRAVITY
                if self.vel <= 0:
                    for item in self.expObjects:
                        item.pos = self.pos
                    self.freeFallDetector = True
            else:
                for item in self.expObjects:
                    item.render()
                    item.update()
        
        def render(self):
            if self.freeFallDetector == False:
                g.replaceDrawingObject(penID, self.pen)
                g.replaceDrawingObject(brushID, self.brush)
                g.ellipse((int(self.pos.x - 5), int(self.pos.y - 5), int(self.pos.x + 5), int(self.pos.y + 5)))

    objects = []
    i = 0
    while True:
        objects.append(Firework())
        if i == 99:
            break
        i += 1

    penID = g.addDrawingObject(objects[0].pen)
    brushID = g.addDrawingObject(objects[0].brush)
    bgBrush = DrawingObject(Form1.bgBrushHandle)

    while isClosing == False:
        g.fillRect(clientRect, bgBrush)
        i = 0
        while True:
            item = objects[i]
            item.render()
            item.update()
            if i == 99:
                break
            i += 1
        g2.copyGraphics(clientRect, g, 0, 0)
    
    # TODO: Dispose everything which needs to be disposed here.

    hasResponded = True

t = threading.Thread(target=graphicsLoop, args=(Form1.hWindow, ))
t.start()

Form1.pumpMessages()