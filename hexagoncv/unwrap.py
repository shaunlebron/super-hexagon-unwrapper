"""
Given a Super Hexagon image and the vertices of its center polygon, this module
creates a new image by unwrapping it with the coordinate transform shown below:

(Vertices of the center polygon are marked [1][2][3][4][5][6])


              ORIGINAL                                     UNWRAPPED
  
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

R(ANGLE) is a function that returns the distance from the center of the polygon
to the edge of the polygon at the given angle.

NOTE: The Y-axis of the Unwrapped plot is warped such that R(ANGLE) lies on the
same horizontal line for all values of ANGLE.


DISTORTION WARNING: There is visible image distortion resulting from (1) subtle
errors in the locations of the vertices and (2) perspective deformation of the
image.  It is a hard problem to undo perspective deformation, so this
'unwrapping' is only an approximation.

"""

from SimpleCV import *

import pyglet
from pyglet.gl import *
from shader import Shader

from parse import parse_frame

def dist(p0,p1):
    """Distance between two 2D points."""
    x0,y0 = p0
    x1,y1 = p1
    dx = x0-x1
    dy = y0-y1
    return math.sqrt(dx*dx + dy*dy)

class Vertex:
    """A vertex of a polygon, containing calculated properties of that vertex."""
    def __init__(self,point,center):
        self.point = point
        self.center = center
        self.radius = dist(point,center)
        self.rel = (point[0]-center[0], point[1]-center[1])
        self.angle = math.atan2(self.rel[1], self.rel[0])
    
    def copy(self):
        return Vertex(self.point, self.center)

class TriangleProjector:
    """
    Given two Vertex objects sharing a center point, this class determines the
    distance from that center point to the line segment of those two vertices
    along the direction of a given angle.

    To illustrate:

        vertex1   = V1
        vertex2   = V2
        center    = C
        intersect = X

                V1 .............X........... V2
                      ..........|........
                           .....|....
                               .|.
                                C

    After computing the distance from C to X, we can compute the distance
    from the center to any point on V1->V2 given some angle:

          R(ANGLE) = |CX| / cos(ANGLE - angle(CX))

    """

    def __init__(self, vertex1, vertex2):

        # define angle bounds for this projector
        self.start_angle = vertex1.angle
        self.end_angle = vertex2.angle

        # short-hand names for each point
        point1 = vertex1.point
        point_center = vertex1.center
        point2 = vertex2.point

        # define the 2nd vertex and the center point relative to the 1st vertex
        rel_center = (point_center[0]-point1[0], point_center[1]-point1[1]) 
        rel_point2 = (point2[0]-point1[0], point2[1]-point1[1])

        # distance between the two vertices
        den = dist(rel_point2, (0,0))

        # Rotate the center point such that the 1st and 2nd vertex will be
        # horizontal from each other.
        x = (rel_center[0]*rel_point2[0] + rel_center[1]*rel_point2[1]) / den
        y = (rel_center[1]*rel_point2[0] - rel_center[0]*rel_point2[1]) / den

        # On the line segment between the vertices, find the closest point
        # to the center point.
        # (This is just the x-component of our rotated center point, so we pick
        # the point that is 'x' distance along the line between vertex 1 and
        # 2.)
        intersect = (
                int(point1[0] + x * rel_point2[0]/den),
                int(point1[1] + x * rel_point2[1]/den))

        # The angle to the mid point.
        self.center_angle = math.atan2(intersect[1]-point_center[1], intersect[0]-point_center[0])

        # Distance from the center point to the mid point on the line segment.
        self.center_dist = dist(intersect, point_center)
    
    def is_angle_inside(self, angle):
        """
        Determines if the given angle is inside the range covered by our
        triangle.
        """
        return self.start_angle <= angle and angle <= self.end_angle

    def angle_to_radius(self, angle):
        """
        Returns the distance to the line segment created by our two vertices
        at the given angle.
        """
        return self.center_dist / math.cos(abs(angle-self.center_angle))

class PolygonProjector:
    """
    Given a list of points along a concave polygon, this class creates a list
    of TriangleProjector objects so that we can compute the distance between
    the center and the edge of the polygon given some angle.
    """
    def __init__(self, center, points):

        vertices = [Vertex(v, center) for v in points]
        vertices.sort(key=lambda v: v.angle)

        # Make angle wrap from -pi to pi easier to deal with by copying each
        # endpoint vertex to the opposite side of the list with a lower or higher
        # but equivalent angle.
        v0 = vertices[0].copy()
        v0.angle += math.pi*2
        v1 = vertices[-1].copy()
        v1.angle -= math.pi*2
        vertices.insert(0,v1)
        vertices.append(v0)

        self.projectors = [TriangleProjector(vertices[i],vertices[i+1]) for i in xrange(len(vertices)-1)]
        self.vertices = vertices
    
    def angle_to_radius(self, angle):
        """
        Get the distance from the center of this polygon to its edge at the
        given angle.
        """
        for p in self.projectors:
            if p.is_angle_inside(angle):
                return p.angle_to_radius(angle)

vertex_shader = """
void main() {
    // transform the vertex position
    gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
    // pass through the texture coordinate
    gl_TexCoord[0] = gl_MultiTexCoord0;
}
"""

fragment_shader = """
uniform sampler2D tex0;

// defined in pixels
uniform vec2 region_size;
uniform vec2 actual_size;

uniform float angle_bounds[14];
uniform float radii[13];
uniform float angles[13];
uniform int count;

float PI = 3.14159265358979323846264;

float get_radius(float angle) {
    int i;
    for (i=0; i<count; i++) {
        if (angle_bounds[i] <= angle && angle < angle_bounds[i+1]) {
            return radii[i] / cos(abs(angles[i]-angle));
        }
    }
    return 0.0;
}

void main() {
    vec2 c = gl_TexCoord[0].xy;

    float angle = c.x*PI*2.0 - PI;
    float poly_radius = get_radius(angle);
    float max_radius = poly_radius * 11.0;
    float r = c.y * max_radius;

    vec2 p = region_size/2.0 + r * vec2(cos(angle),-sin(angle));

    p /= actual_size;

    if (0.0 <= p.x && p.x < 1.0 && 0.0 <= p.y && p.y < 1.0) {
        gl_FragColor = vec4(texture2D(tex0, p).rgb, 1.0);
    }
    else {
        gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0);
    }
}
"""

class Unwrapper:
    def __init__(self):
        self.shader = Shader(vertex_shader, fragment_shader)
        self.shader.bind()
        self.shader.uniformi('tex0', 0)
        self.shader.unbind()

        # create a fullscreen quad
        self.batch = pyglet.graphics.Batch()
        self.batch.add(4, GL_QUADS, None, ('v2i', (0,0, 1,0, 1,1, 0,1)), ('t2f', (0,0, 1,0, 1,1, 0,1)))

    def update(self, img_path, frame):

        projector = PolygonProjector(frame.center_point, frame.center_vertices)
        angle_bounds = [v.angle for v in projector.vertices]
        radii = [p.center_dist for p in projector.projectors]
        angles = [p.center_angle for p in projector.projectors]

        self.texture = pyglet.image.load(img_path).get_texture()
        region_w, region_h = self.texture.width, self.texture.height
        actual_w, actual_h = self.texture.owner.width, self.texture.owner.height

        # set the correct texture unit
        self.shader.bind()
        self.shader.uniformf('region_size', region_w, region_h)
        self.shader.uniformf('actual_size', actual_w, actual_h)
        self.shader.uniformfv('angle_bounds', 1, angle_bounds)
        self.shader.uniformfv('radii', 1, radii)
        self.shader.uniformfv('angles', 1, angles)
        self.shader.uniformi('count', len(radii))
        self.shader.unbind()

    def draw(self):
        glBindTexture(self.texture.target, self.texture.id)
        self.shader.bind()
        self.batch.draw()
        self.shader.unbind()
        glBindTexture(self.texture.target, 0)

    def save_image(self, filename):
        pyglet.image.get_buffer_manager().get_color_buffer().save(filename)

    def get_fps(self):
        return pyglet.clock.get_fps()

def start_unwrap_window(width, height, draw_callback):
    window = pyglet.window.Window(width, height, resizable=False, visible=False, caption="Unwrap")

    @window.event
    def on_resize(width, height):
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, 1, 0, 1, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        return pyglet.event.EVENT_HANDLED
     
    @window.event
    def on_draw():
        draw_callback()

    pyglet.clock.schedule_interval(lambda dt: None, 1.0/60.0)
     
    window.set_visible(True)
    pyglet.app.run()

if __name__ == "__main__":
    img_path = 'test.jpg'
    img = Image(img_path)
    w,h = img.size()
    img.show()
    frame = parse_frame(img)
    if frame:
        unwrapper = Unwrapper()
        unwrapper.update(img_path, frame)
        def on_draw():
            unwrapper.draw()
        start_unwrap_window(w,h,on_draw)
