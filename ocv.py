#!/usr/bin/env python
#
# PyOCV - Python OpenCV
# ocv.py - Main Pyocv Library
#
# Author: Anders Evenrud <andersevenrud@gmail.com>
# License: Simple BSD
#

import cv
import os
import subprocess

from config import *

# ########################################################################### #
# FUNCTIONS                                                                   #
# ########################################################################### #

def OCVHistogram(frame, ranges = [[0, 256]], hist_size = 64):
    """Create a histogram of given frame"""
    if frame.nChannels != 1:
        dest = OCVCopyGrayscale(frame)
    else:
        dest = frame

    hist_image = cv.CreateImage((dest.width, dest.height), 8, 1)
    hist = cv.CreateHist([hist_size], cv.CV_HIST_ARRAY, ranges, 1)

    cv.CalcArrHist([dest], hist)
    (min_value, max_value, _, _) = cv.GetMinMaxHistValue(hist)
    cv.Scale(hist.bins, hist.bins, float(hist_image.height) / max_value, 0)

    cv.Set(hist_image, cv.ScalarAll(255))
    bin_w = round(float(hist_image.width) / hist_size)

    for i in range(hist_size):
        cv.Rectangle(hist_image, (int(i * bin_w), hist_image.height),
            (int((i + 1) * bin_w), hist_image.height - cv.Round(hist.bins[i])),
            cv.ScalarAll(0), -1, 8, 0)

    return hist_image

def OCVBrightnessContrast(frame, contrast, brightness):
    """Set brightness / contrast of given frame. Values from 0 to 200"""
    # The algorithm is by Werner D. Streidt
    # (http://visca.com/ffactory/archives/5-99/msg00021.html)
    if contrast > 0:
        delta = 127. * contrast / 100
        a = 255. / (255. - delta * 2)
        b = a * (brightness - delta)
    else:
        delta = -128. * contrast / 100
        a = (256. - delta * 2) / 255.
        b = a * brightness + delta

    cv.ConvertScale(frame, frame, a, b)

def OCVCloneImage(frame):
    """Clone and return given frame"""
    img = cv.CreateImage((frame.width, frame.height), frame.depth, frame.nChannels)
    cv.Copy(frame, img)
    return img

def OCVResizeImage(frame, size):
    """Clone, resize and return given frame"""
    img = cv.CreateImage(size, frame.depth, frame.nChannels)
    cv.Resize(frame, img)
    return img

def OCVCopyGrayscale(frame):
    """Copy frame and convert to GrayScale"""
    img = cv.CreateImage((frame.width, frame.height), frame.depth, 1)
    cv.CvtColor(frame, img, cv.CV_RGB2GRAY)
    return img

def OCVClear(frame, color = (0, 0, 0)):
    """Clear a Frame"""
    cv.Set(frame, color);

def OCVObjects(frame, storage, haar):
    """Read Objects from Frame"""
    cascade = cv.Load("%s/%s.%s" % (HAAR_PATH, haar, "xml"))
    objects = cv.HaarDetectObjects(frame, cascade, storage, 1.2, 2, 0, (20, 20))
    return objects
    #if objects:
    #    for ((x, y, w, h), n) in objects:
    #        return cv.GetSubRect(frame, (x, y, w, h))
    #return None

def OCVText(frame, text, x = 0, y = 0, step = 15, font = None, clear = False):
    """Apply text to an image"""
    img = cv.CreateImage((frame.width, frame.height), frame.depth, frame.nChannels)

    if font is None:
        font = cv.InitFont(cv.CV_FONT_HERSHEY_PLAIN, 0.9, 0.9, 0, 1, 1)

    if clear:
        OCVClear(img)

    for i in text.split("\n"):
        i = i.strip()
        if i:
            cv.PutText(img, i, (x, y), font, 255)
            y += step;

    return img

def OCVReadText(frame, name, out, psm = 3, lang = DEFAULT_LANGUAGE):
    """Read Text From Image"""
    data = None

    # Save image
    cv.SaveImage(name, frame);
    if os.path.isfile(name):
        # Detect text
        args = [TESSERACT_BIN, '-psm', str(psm), str(name), str(out)]
        print "Executing: %s" % (((" ").join(args)))
        cmdout = subprocess.Popen(args, stderr=subprocess.STDOUT, stdout=subprocess.PIPE).communicate()[0]
        if os.path.isfile(out + ".txt"):
            # Store result
            data = open(out + ".txt", 'r').read()
            if not data.strip():
                data = None

    return data

# ########################################################################### #
# CLASSES                                                                     #
# ########################################################################### #

#
# Class: CVApplication -- OpenCV Default Application
#
class OCVApplication:

    def __init__(self, id=0):
        """Create a new OpenCV Application"""
        self.storage      = cv.CreateMemStorage(id)
        self.font         = cv.InitFont(cv.CV_FONT_HERSHEY_PLAIN, 0.9, 0.9, 0, 1, 1)

    def run(self):
        """Start Application"""
        pass

    def stop(self):
        """Stop Application"""
        try:
            cv.ClearMemStorage(self.storage)
        except:
            pass

#
# Class: CVCapture -- OpenCV Capture Device Instance
#
class OCVCapture:

    def __init__(self, id=0, width=DEFAULT_DEV_WIDTH, height=DEFAULT_DEV_HEIGHT):
        """Create a new OpenCV Capture Device"""
        self.capture = cv.CreateCameraCapture(id)
        cv.SetCaptureProperty(self.capture, cv.CV_CAP_PROP_FRAME_WIDTH, width)
        cv.SetCaptureProperty(self.capture, cv.CV_CAP_PROP_FRAME_HEIGHT, height)


    def poll(self, flip = False):
        """Get a frame from device"""
        frame = cv.QueryFrame(self.capture)
        if flip:
            cv.Flip(frame, None, 1)
        return frame

#
# Class: CVWindow -- OpenCV Window Abstraction
#
class OCVWindow:

    def __init__(self, name, x = -1, y = -1, w = None, h = None):
        """Create OpenCV Window"""

        if w is not None and h is not None:
            cv.NamedWindow(name, 0)
            cv.ResizeWindow(name, w, h)
        else:
            cv.NamedWindow(name, cv.CV_WINDOW_AUTOSIZE)

        if x != -1 and y != -1:
            cv.MoveWindow(name, x, y)

        self.name     = name
        self.settings = {}

    def __del__(self):
        """Remove OpenCV Window"""
        try:
            cv.DestroyWindow(self.name)
        except:
            pass

    def createTrackbar(self, name, val = 0, maxval = 255, callback = None):
        """Insert a new Trackbar"""

        if callback is None:
            def callback(name, a):
                pass

        def wrapper(a):
            self.handleTrackbarEvent(name, a)
            callback(name, a)

        cv.CreateTrackbar(name, self.name, val, maxval, wrapper)
        wrapper(val)

    def handleTrackbarEvent(self, name, val):
        """Handle Trackbar onchange"""
        self.settings[name] = int(val)

    def render(self, frame):
        """Render the selected frame"""
        cv.ShowImage(self.name, frame)


#
# Class: OCVImage -- OpenCV Image OO
#
class OCVImage:

    def __init__(self, frame = None, width = None, height = None, depth = cv.IPL_DEPTH_8U, channels = 3):
        """Create a new instance from (frame is cloned if given)"""
        if frame is None:
          img = cv.CreateImage((width, height), depth, channels)
        else:
          img = OCVCloneImage(frame)

        self.frame    = img
        self.depth    = img.depth
        self.channels = img.nChannels
        self.width    = img.width
        self.height   = img.height
        self.size     = (self.width, self.height)
        self.font     = None

    # MISC

    def clone(self):
        """Clone image and return new instance"""
        return OCVImage(self.frame)

    def save(self, path):
        """Save the image to given path/filename"""
        cv.SaveImage(path, self.frame);

    # MANIPULATION

    def clear(self, color = (0, 0, 0)):
        """Clear frame to given color"""
        cv.Set(self.frame, color);

    def resize(self, size):
        """Resize image to given dimension"""
        self.frame  = OCVResizeImage(self.frame, size)
        self.width  = img.width
        self.height = img.height
        self.size   = (self.width, self.height)

    def crop(self, x, y, w, h):
        """Crop image to given dimension/position"""
        self.frame  = cv.GetSubRect(self.frame, (x, y, w, h))
        self.width  = img.width
        self.height = img.height
        self.size   = (self.width, self.height)

    def mode(self, channels = 1):
        """Convert image to given number of channels"""
        if self.channels != channels:
            if channels == 1:
                self.frame    = OCVCopyGrayscale(self.frame)
                self.channels = self.frame.nChannels
                self.depth    = self.frame.depth

                return True

        return False

    def equalize(self):
        """Equalize frame"""
        cv.EqualizeHist(self.frame, self.frame)

    # RENDER

    def text(self, text, x = 0, y = 0, step = 15, font = None):
        """Draw text on image (Font will be stored and used by default until changed)"""
        if font is None:
            if self.font is None:
                font = self.font = cv.InitFont(cv.CV_FONT_HERSHEY_PLAIN, 0.9, 0.9, 0, 1, 1)
        else:
            self.font = font

        self.frame = OCVText(self.frame, text, x, y, step, self.font)

    def line(self, p1, p2, color = (0, 255, 0), border = 1, line = 8):
        """Draw a line"""
        shift = 0
        cv.Line(self.frame, p1, p2, color, border, line, shift)

    def rect(self, x, y, w, h, color = (0, 255, 0), line = 3):
        """Draw a rectangle on the image"""
        tl = (x + w, y + h)
        br = (x + w, y + h)
        cv.Rectangle(self.frame, tl, br, color, border)

    def circle(self, dx, dy, radius, color = (0, 255, 0), border = -1, line = 8):
        """Draw a circle on image"""
        self.ellipse(dx, dy, radius, radius, color, border, line)

    def ellipse(self, dx, dy, width, height, color = (0, 255, 0), border = -1, line = 8):
        """Draw a ellipse on image"""
        rotation = 0
        start_angle = 0
        stop_angle = 360
        shift = 0

        cv.Ellipse(self.frame,
            cv.cvPoint (dx, dy),
            cv.cvSize(width, height),
            rotation, start_angle, stop_angle, color, border, line, shift)

    # GETTERS

    def getDetectableObjects(self, storage, haar):
        """Detect object(s) with given HAAR"""
        return OCVObjects(self.frame, storage, haar)

    def getDetectableText(self, **ka):
        return OCVReadText(**ka)

    def getSection(self, x, y, w, h, instance = False):
        """Get a section of the image with given envelope (can return new OCVImage() instance"""
        img = cv.GetSubRect(self.frame, (x, y, w, h))
        if instance:
            return OCVImage(img)

        return img

    # SETTERS

    def setThreshold(self, threshold, type, max = 255):
        """Set threshold"""
        cv.Threshold(self.frame, self.frame, threshold, max, type);

    def setBrightness(self, brightness):
        """Set brightness"""
        self.setBrightnessContrast(brightness, 0)

    def setContrast(self, contrast):
        """Set contrast"""
        self.setBrightnessContrast(0, contrast)

    def setBrightnessContrast(self, brightness, contrast):
        """Set brightness / contrast of given frame. Values from 0 to 200"""
        OCVBrightnessContrast(self.frame, contrast, brightness)

