# conversion from vim location (r,c) to canvas coord (x,y):
# x = c-1
# y = r-5
template = """
                 [2]                       ________________________________________
                 ...                      |                                        ^
              .........                   |                                        |
           ..............X                |                                        |
        ................/....             |                                        |
     ................../........          |                                        |
[3]........R(ANGLE)->./...........[1]     |                                        |
   ................../............        |                                        |<--R(ANGLE)*4
   ................./\.<-ANGLE....        |                                        |
   ................/  \...........        |                                        |
   ...............O===============        |                                        |<--R(ANGLE)*3
   ...............................        |                                        |
   ...............................        |                                        |
   ...............................        |                                        |<--R(ANGLE)*2
[4]...............................[6]     |                                        |
     ...........................          |  [1]  X [2]    [3]    [4]    [5]   [6] |
        .....................             ||::::::|::::::::::::::::::::::::::::::::|<--R(ANGLE)
           ...............                ||::::::|::::::::::::::::::::::::::::::::|
              .........                   ||::::::|::::::::::::::::::::::::::::::::|
                 ...                      0--------------------------------------->
                 [5]                                        ANGLE
"""

title = """
                         ______  ____  ______ _____________________
                        / / /  \/ / / / / . // .  / . / . / __/ . //
                       / / / /\  /  ^^ /   </ _  / __/ __/ _//   <<
                      /___/_/ /_/__/\_/_/\_\_//_/_/ /_/ /___/_/\_\\\\ 
"""

title2 = """
                          _ _ ___ _ __ ___ ___  __ __ __ ___
                         | | |   \ | |\  _\__ \| .\ .\ :\  _\ 
                         |___\_|_|__|_|_| |_.__| _/ _/__|_|
                                               |_||_|
"""

import os, sys
import subprocess
import math
import time

from termcolor import colored

def get_line(p1, p2):
    """
    Bresenham line function that returns a list of (x,y) tuples.
    source: http://roguebasin.roguelikedevelopment.org/index.php?title=Bresenham%27s_Line_Algorithm
    """
    x1,y1 = p1
    x2,y2 = p2
    points = []
    issteep = abs(y2-y1) > abs(x2-x1)
    if issteep:
        x1, y1 = y1, x1
        x2, y2 = y2, x2
    rev = False
    if x1 > x2:
        x1, x2 = x2, x1
        y1, y2 = y2, y1
        rev = True
    deltax = x2 - x1
    deltay = abs(y2-y1)
    error = int(deltax / 2)
    y = y1
    ystep = None
    if y1 < y2:
        ystep = 1
    else:
        ystep = -1
    for x in range(x1, x2 + 1):
        if issteep:
            points.append((y, x))
        else:
            points.append((x, y))
        error -= deltay
        if error < 0:
            y += ystep
            error += deltax
    # Reverse the list if the coordinates were reversed
    if rev:
        points.reverse()
    return points

class AsciiCanvas:

    def __init__(self,w,h):
        self.w = w
        self.h = h
        self.canvas = [[' ']*w for i in xrange(h)]

    def clear(self):
        for y in xrange(self.h):
            for x in xrange(self.w):
                self.canvas[y][x] = ' '

    def text(self, x, y, text, color='white'):
        for i,c in enumerate(text):
            x0 = x+i
            try:
                if x0 < self.w:
                    self.canvas[y][x0] = colored(c, color) if color else c
            except IndexError:
                continue
    def get(self, x,y):
        return self.canvas[y][x]

    def line(self, p1, p2, c):
        pairs = get_line(p1, p2)
        for x,y in pairs:
            self.text(x,y,c)

    def display(self):
        os.system('clear')
        print title2
        print
        for line in self.canvas:
            print ' '+''.join(line)
        print '\n'*5

    def set_debug_border(self):
        for y in xrange(self.h):
            self.text(0,y,'|')
            self.text(self.w-1,y,'|')
        for x in xrange(self.w):
            self.text(x,0,'-')
            self.text(x,self.h-1,'-')

ray_color = 'blue'
angle_color = 'magenta'
r_color = 'yellow'
vert_color = 'green'

def draw_rest(c,count=6,angle=0):
    # center of polygon
    c.text(18,10,'O')

    # inner polygon labels
    c.text(11,6,'R(ANGLE)->', color=r_color)
    c.text(23,8,'<-ANGLE', color=angle_color)

    # inner polygon angle degree marker
    for i in xrange(2):
        c.text(22-i,9-i,'\\')
    c.text(20,9,'  ')

    # top unwrap plot border
    for i in xrange(40):
        c.text(43+i,0,'_')

    # left/right unwrap plot border
    for i in xrange(18):
        c.text(42,1+i,'|')
        c.text(83,1+i,'|')
    c.text(83,1,'^')

    # unwrap plot origin
    c.text(42,19,'0')

    # unwrap plot bottom border
    for i in xrange(39):
        c.text(43+i,19,'-')
    c.text(82,19,'>')

    # y axis labels
    c.text(84,7,'<--R(ANGLE)*4')
    c.text(84,10,'<--R(ANGLE)*3')
    c.text(84,13,'<--R(ANGLE)*2')
    c.text(84,16,'<--R(ANGLE)', color=r_color)
    c.text(60,20,'ANGLE', color=angle_color)

    
    # draw polygon area
    for i in xrange(3):
        for j in xrange(40):
            c.text(43+j,16+i,':')

    # draw vertices
    maxa = 40
    da = maxa/count
    base_a = int(angle/math.pi/2*maxa)
    angles = [base_a + int(float(maxa)/count * i) for i in xrange(count)]
    for i,a in enumerate(angles):
        x = 43 + a % maxa
        y = 15
        c.text(x-1,y,"[%d]"%(i+1),color=vert_color)

    # draw ray
    for i in xrange(3):
        c.text(50,16+i,'|', color=ray_color)
        c.text(43,16+i,'|')
    c.text(50,15,'X', color=ray_color)

def draw_poly(c,count=6,angle=0):
    # center and radius
    cx = 18
    cy = 10
    r = 17

    da = 2*math.pi/count
    
    # calculate vertices
    verts = []
    for i in xrange(count):
        a = angle+da*i
        dx = int(r*math.cos(-a)+0.5)
        dy = int(r*math.sin(-a)+0.5)
        verts.append((cx+dx, cy+dy/2))

    # create the horizontal scan lines
    rows = {}
    for i in xrange(count):
        for x,y in get_line(verts[i], verts[(i+1)%count]):
            if y in rows:
                rows[y]['min'] = min(x, rows[y]['min'])
                rows[y]['max'] = max(x, rows[y]['max'])
            else:
                rows[y] = { 'min': x, 'max': x }

    # fill polygon by drawing scan lines
    for y,xs in rows.items():
        for x in xrange(xs['min'],xs['max']+1):
            c.text(x,y,'.')

    # get polygon ray length
    raylen = 0
    rx = 19
    ry = 9
    for i in xrange(10):
        raylen += 1
        x = rx+i
        y = ry-i
        if c.get(x+1,y-1) == ' ':
            break

    # get polygon base angle length
    baselen = 0
    bx = 19
    by = 10
    for i in xrange(100):
        baselen += 1
        if c.get(bx+i,by) == ' ':
            break

    # inner polygon base angle line
    for i in xrange(baselen-1):
        c.text(bx+i,by,'=')

    # draw vertex labels
    for i in xrange(count):
        a = angle+da*i
        x = cx + int((r)*math.cos(-a)+0.5)
        y = cy + int((r)*math.sin(-a)+0.5)/2
        c.text(x-1,y,"[%d]"%(i+1), color=vert_color)

    # draw polygon ray
    for i in xrange(raylen):
        x = rx+i
        y = ry-i
        if i == raylen-1:
            c.text(x,y,'X',color=ray_color)
        else:
            c.text(x,y,'/',color=ray_color)

def get_window_id():
    """
    source:http://stackoverflow.com/a/3552462/142317
    """
    output = subprocess.check_output(['xprop', '-root'])
    for line in output.splitlines():
        if '_NET_ACTIVE_WINDOW(WINDOW):' in line:
            return line.split()[4]

if __name__ == "__main__":
    _id = get_window_id()

    c = AsciiCanvas(97,21)

    a = 0
    num_frames = 40
    da = 2*math.pi/num_frames
    for i in xrange(num_frames):
        c.clear()
        #c.set_debug_border()
        draw_poly(c,count=6,angle=a)
        draw_rest(c,count=6,angle=a)
        c.display()
        a += da

        time.sleep(0.1)

        # use imagemagick to take a screenshot
        subprocess.call([
            'import',
            '-window',_id,
            'frame%02d.png' % i,
        ])
