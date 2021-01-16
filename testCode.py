from WindowsForms import Graphics, Form, DrawingObject, SolidBrush, Pen, VKCodes
import threading
import time
import math

isClosing = False
hasResponded = False

left = False
right = False
up = False
down = False


def setKeys(keyCode, val):
    global left
    global right
    global down
    global up
    if keyCode == VKCodes.VK_LEFT:
        left = val
    elif keyCode == VKCodes.VK_RIGHT:
        right = val
    elif keyCode == VKCodes.VK_UP:
        up = val
    elif keyCode == VKCodes.VK_DOWN:
        down = val


def wndProc(hWnd, message, wParam, lParam):
    if message == Form.WM_KEYDOWN:
        setKeys(wParam, True)

    elif message == Form.WM_KEYUP:
        setKeys(wParam, False)
        
    elif message == Form.WM_CLOSE:
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


Form1 = Form(wndProc, 'Form1', None, Form.BLACK_BRUSH)
Form1.show()


def checkBounds(pos, rect):
    if pos[0] >= rect[0] and pos[0] < rect[2] and pos[1] >= rect[1] and pos[1] < rect[3]:
        return True
    return False


def graphicsLoop(hWindow):
    global isClosing  # declare variables as global so that they can be used across both threads
    global hasResponded
    global left
    global right
    global down
    global up
    print("Graphics loop has been initiated.")

    clientRect = Form1.getClientRect()
    # print(clientRect)

    g2 = Form1.createGraphics()

    g = Graphics.fromMemory(g2, (clientRect[2], clientRect[3]))

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

    class Player:
        def __init__(self, pos, vel):
            self.pos = pos
            self.vel = vel

        def update(self):
            self.pos = self.pos.add(self.vel)
            self.vel = self.vel.amplify(0.99)

            if self.pos.x > clientRect[2]:
                self.vel.x = -self.vel.x
                self.pos.x = clientRect[2] - (self.pos.x - clientRect[2])
            elif self.pos.x < 0:
                self.vel.x = -self.vel.x
                self.pos.x = -self.pos.x

            if self.pos.y > clientRect[3]:
                self.vel.y = -self.vel.y
                self.pos.y = clientRect[3] - (self.pos.y - clientRect[3])
            elif self.pos.y < 0:
                self.vel.y = -self.vel.y
                self.pos.y = -self.pos.y

        def checkForKeyboardInput(self):
            if left:
                self.vel.x -= 0.02
            if right:
                self.vel.x += 0.02
            if down:
                self.vel.y += 0.02
            if up:
                self.vel.y -= 0.02

        def render(self):
            g.ellipse((int(self.pos.x - 10), int(self.pos.y - 10),
                       int(self.pos.x + 10), int(self.pos.y + 10)))
            # g.drawArc((int(round(self.pos.x)), int(round(self.pos.y))), 50, float(90), float(180))

    class Interacter:
        def __init__(self, pos):
            self.pos = pos

        def render(self):
            g.ellipse((int(self.pos.x - 20), int(self.pos.y - 20),
                       int(self.pos.x + 20), int(self.pos.y + 20)))

        def interact(self, player):
            diff = self.pos.sub(player.pos)
            dist = diff.getLength()
            force = 0.5 / dist
            fract = dist / force
            return diff.div(fract)

    class Attractor(Interacter):
        def __init__(self, pos):
            super().__init__(pos)

        def attract(self, player):
            player.vel = player.vel.add(self.interact(player))

    class Repeller(Interacter):
        def __init__(self, pos):
            super().__init__(pos)

        def repell(self, player):
            player.vel = player.vel.sub(self.interact(player))

    player = Player(Vector2f(100, 100), Vector2f.empty())
    att = Attractor(Vector2f(clientRect[2] / 2, clientRect[3] / 2))
    rep1 = Repeller(Vector2f(clientRect[2] / 2, 0))
    rep2 = Repeller(Vector2f(clientRect[2] / 2, clientRect[3]))

    mainPen = Pen(Pen.PS_SOLID, 1, Graphics.rgb(255, 0, 0))
    mainBrush = SolidBrush(Graphics.rgb(255, 0, 0))
    pen2 = Pen(Pen.PS_SOLID, 1, Graphics.rgb(0, 0, 255))
    brush2 = SolidBrush(Graphics.rgb(0, 0, 255))
    bgBrush = DrawingObject(Form1.bgBrushHandle)
    brushID = g.addDrawingObject(mainBrush)
    penID = g.addDrawingObject(mainPen)

    while isClosing == False:
        g.fillRect(clientRect, bgBrush)
        att.render()
        g.replaceDrawingObject(brushID, brush2)
        g.replaceDrawingObject(penID, pen2)
        rep1.render()
        rep2.render()
        g.replaceDrawingObject(brushID, mainBrush)
        g.replaceDrawingObject(penID, mainPen)
        player.render()
        player.update()
        att.attract(player)
        rep1.repell(player)
        rep2.repell(player)
        player.checkForKeyboardInput()
        g2.copyGraphics(clientRect, g, 0, 0)
    g.dispose()
    g2.dispose()
    # bgBrush.dispose()
    pen2.dispose()
    brush2.dispose()
    hasResponded = True


t = threading.Thread(target=graphicsLoop, args=(Form1.hWindow, ))
t.start()

Form1.pumpMessages()
