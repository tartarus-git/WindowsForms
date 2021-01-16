import ctypes
from ctypes import windll
from ctypes import wintypes

WNDPROCTYPE = ctypes.WINFUNCTYPE(ctypes.c_int, wintypes.HWND, ctypes.c_uint, wintypes.WPARAM, wintypes.LPARAM)

# Definition of WNDCLASSEX
class WNDCLASSEX(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint),
                ("style", ctypes.c_uint),
                ("lpfnWndProc", WNDPROCTYPE),
                ("cbClsExtra", ctypes.c_int),
                ("cbWndExtra", ctypes.c_int),
                ("hInstance", wintypes.HANDLE),
                ("hIcon", wintypes.HANDLE),
                ("hCursor", wintypes.HANDLE),
                ("hBrush", wintypes.HANDLE),
                ("lpszMenuName", wintypes.LPCWSTR),
                ("lpszClassName", wintypes.LPCWSTR),
                ("hIconSm", wintypes.HANDLE)]

# Storage class for virtual key codes. Used when getting input from the keyboard.
class VKCodes:
    # Arrow keys:
    VK_LEFT = 0x25
    VK_UP = 0x26
    VK_RIGHT = 0x27
    VK_DOWN = 0x28

# Parent class for all drawing objects. Makes use of inheritance.
class DrawingObject:
    def __init__(self, handle):
        self.handle = handle

    def dispose(self):
        windll.gdi32.DeleteObject(self.handle)

# Inherited Pen class from DrawingObject class. Contains constants for pen styles.
class Pen(DrawingObject):
    PS_SOLID = 0
    PS_DASH = 1
    PS_DOT = 2
    PS_DASHDOT = 3
    PS_DASHDOTDOT = 4
    PS_NULL = 5
    PS_INSIDERFRAME = 6

    def __init__(self, penStyle, width, color):
        super().__init__(windll.gdi32.CreatePen(penStyle, width, color))

# Inherited SolidBrush class from DrawingObject class. Contains constructor for solid brushes.
class SolidBrush(DrawingObject):
    def __init__(self, color):
        super().__init__(windll.gdi32.CreateSolidBrush(color))

# Wrapper for the graphical functions inside of win32gui.
class Graphics:
    # Constants
    SRCCOPY = 13369376

    def __init__(self, hDC):
        self.hDC = hDC
        self.drawingObjects = []
        self.hWnd = None

    # 2 different "constructors" for 2 different use cases. 1: graphical context from window 2: graphical context from memory <---- useful for buffering
    @classmethod
    def fromHwnd(cls, hWnd):
        result = cls(windll.user32.GetDC(hWnd))
        result.hWnd = hWnd
        return result

    @classmethod
    def fromMemory(cls, blueprintG, size):
        memG = cls(windll.gdi32.CreateCompatibleDC(blueprintG.hDC))
        memBmp = DrawingObject(windll.gdi32.CreateCompatibleBitmap(blueprintG.hDC, size[0], size[1]))
        memG.addDrawingObject(memBmp)
        return memG

    # Simple static method that converts r, g, b to a single integer using bitshifts and OR logic.
    @staticmethod
    def rgb(r, g, b):
        return (b << 8 | g) << 8 | r

    # Disposes the graphical context aswell as all currently loaded DrawingObjects.
    def dispose(self):
        for drawingObject in self.drawingObjects:
            drawingObject.dispose()
        if self.hWnd == None:
            windll.gdi32.DeleteObject(self.hDC)
        else:
            windll.user32.ReleaseDC(self.hWnd, self.hDC)
    
    # Wrappers for the different draw calls, like drawing a line, circle, rect, etc...
    def setPixel(self, pos, color):
        windll.gdi32.SetPixel(self.hDC, pos[0], pos[1], color)

    def addDrawingObject(self, drawingObject):
        i = len(self.drawingObjects)
        self.drawingObjects.append(drawingObject)
        windll.gdi32.SelectObject(self.hDC, drawingObject.handle)
        return i

    def replaceDrawingObject(self, id, drawingObject):
        self.drawingObjects[id] = drawingObject
        windll.gdi32.SelectObject(self.hDC, drawingObject.handle)

    def drawLine(self, p1, p2):
        windll.gdi32.MoveToEx(self.hDC, p1[0], p1[1], None)
        windll.gdi32.LineTo(self.hDC, p2[0], p2[1])

    # This function does not work properly (cause: unknown).
    # def drawArc(self, pos, rad, startAngle, sweepAngle):
    #     windll.gdi32.AngleArc(self.hDC, pos[0], pos[1], rad, startAngle, sweepAngle)

    def ellipse(self, rect):
        windll.gdi32.Ellipse(self.hDC, rect[0], rect[1], rect[2], rect[3])
    
    def fillRect(self, rect, brush):
        bounds = wintypes.RECT()
        bounds.left = rect[0]
        bounds.top = rect[1]
        bounds.right = rect[2]
        bounds.bottom = rect[3]
        windll.user32.FillRect(self.hDC, ctypes.byref(bounds), brush.handle)

    # Copies graphics from one context to another. Useful for buffering.
    def copyGraphics(self, rect, sourceG, srcX, srcY):
        windll.gdi32.BitBlt(self.hDC, rect[0], rect[1], rect[2], rect[3], sourceG.hDC, srcX, srcY, self.SRCCOPY)

# Form class wraps form controls in an easy-to-use object-oriented fashion.
class Form:
    # Constants:
    WM_CLOSE = 16
    WM_KEYDOWN = 256
    WM_KEYUP = 257
    
    CS_HREDRAW = 2
    CS_VREDRAW = 1

    #IDI_APPLICATION = 32512

    #IDC_ARROW = 32512

    BLACK_BRUSH = 4
    DKGRAY_BRUSH = 3
    DC_BRUSH = 18
    GRAY_BRUSH = 2
    HOLLLOW_BRUSH = 5
    LTGRAY_BRUSH = 1
    NULL_BRUSH = 5
    WHITE_BRUSH = 0

    CW_USEDEFAULT = -2147483648

    WS_EX_LEFT = 0
    WS_OVERLAPPEDWINDOW = 13565952

    SW_SHOW = 5

    def __init__(self, wndProc, wndTitle, rect, bgBrush):
        # Gets instance handle.
        self.hInstance = windll.kernel32.GetModuleHandleW(None)
        
        # The class name.
        self.className = u'PythonWin32Window'

        # Retrieve the stock object which will be used for the background fill with the "bgBrush" handle.
        self.bgBrushHandle = windll.gdi32.GetStockObject(bgBrush)

        # Create and initialize window class.
        self.wndClass                = WNDCLASSEX()
        self.wndClass.cbSize         = ctypes.sizeof(WNDCLASSEX)
        self.wndClass.style          = self.CS_HREDRAW | self.CS_VREDRAW
        self.wndClass.lpfnWndProc    = WNDPROCTYPE(wndProc)
        self.wndClass.cbClsExtra     = 0
        self.wndClass.cbWndExtra     = 0
        self.wndClass.hInstance      = self.hInstance
        self.wndClass.hIcon          = None #windll.user32.LoadIconA(0, self.IDI_APPLICATION)
        self.wndClass.hCursor        = None #windll.user32.LoadCursorA(0, self.IDC_ARROW)
        self.wndClass.hbrBackground  = self.bgBrushHandle
        self.wndClass.lpszMenuName   = None
        self.wndClass.lpszClassName  = self.className
        self.wndClass.hIconSm        = None

        # Register window class
        self.wndClassAtom = windll.user32.RegisterClassExW(ctypes.byref(self.wndClass))

        # Check for user defined bounds, if not --> use default bounds.
        x = self.CW_USEDEFAULT
        y = self.CW_USEDEFAULT
        width = self.CW_USEDEFAULT
        height = self.CW_USEDEFAULT
        if rect != None:
            if rect[0] != None:
                x = rect[0]
            if rect[1] != None:
                y = rect[1]
            if rect[2] != None:
                width = rect[2]
            if rect[3] != None:
                height = rect[3]

        # Create the window and retrieve the handle to said window.
        self.hWindow = windll.user32.CreateWindowExW(
            self.WS_EX_LEFT,
            self.wndClassAtom,
            wndTitle,
            self.WS_OVERLAPPEDWINDOW,
            x,
            y,
            width,
            height,
            None,
            None,
            self.hInstance,
            None)

    # Wrappers for functions related to forms.
    def show(self):
        windll.user32.ShowWindow(self.hWindow, self.SW_SHOW)
    
    def pumpMessages(self):
        # Starts listening for messages. NOT ASYNCRONOUS --> will freeze up the current thread.
        while True:
            msg = wintypes.MSG()
            msgRef = ctypes.byref(msg)
            returnVal = windll.user32.GetMessageW(msgRef, None, 0, 0)
            if returnVal == 0:
                break
            if returnVal != -1:
                windll.user32.TranslateMessage(msgRef)
                windll.user32.DispatchMessageW(msgRef)

    def createGraphics(self):
        return Graphics.fromHwnd(self.hWindow)

    def getWindowRect(self):
        windowRect = wintypes.RECT()
        windll.user32.GetWindowRect(self.hWindow, ctypes.byref(windowRect))
        return (windowRect.left, windowRect.top, windowRect.right, windowRect.bottom)

    def getCursorPos(self):
        screenPos = windll.user32.GetCursorPos()
        return windll.user32.ScreenToClient(self.hWindow, screenPos)
    
    def getClientRect(self):
        clientRect = wintypes.RECT()
        windll.user32.GetClientRect(self.hWindow, ctypes.byref(clientRect))
        return (clientRect.left, clientRect.top, clientRect.right, clientRect.bottom)

    # Wrapper for the SetDCBrushColor function, which changes the default brush color associated with the form. <------ only when DC_BRUSH is selected as the bgBrush
    def setDCBrushColor(self, color):
        windll.gdi32.SetDCBrushColor(self.hWindow, color)

    # Post a windows message notifying the OS that this window should be closed.
    @staticmethod
    def postQuitMessage(exitCode):
        windll.user32.PostQuitMessage(exitCode)

    # Sends data back to the default message handler for the Form.
    @staticmethod
    def defWndProc(hWnd, message, wParam, lParam):
        return windll.user32.DefWindowProcW(hWnd, message, wParam, lParam)