import pyglet
import math
from pyglet.gl import *
from shader import Shader

# We do not use custom vertex shaders, so this is the default one.
vertex_shader = """
void main() {
    // transform the vertex position
    gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
    // pass through the texture coordinate
    gl_TexCoord[0] = gl_MultiTexCoord0;
}
"""

# This fragment shader is a compiled GPU program that is executed for
# every pixel in our new image.
#    Input:  gl_TexCoord[0].xy   (0 <= x,y < 1  such that x+ right, y+ up)
#    Output: gl_FragColor
# The global "uniform" variables are inputs shared by all pixels.
fragment_shader = """

// the texture holding the original game image
uniform sampler2D tex0;

// size of texture in memory (padded to meet a power of 2)
uniform vec2 actual_size;

// size of the active region of the texture (excluding the padding)
uniform vec2 region_size;

uniform vec2 center;
uniform float radius;

float PI = 3.14159265358979323846264;

void main() {

    vec2 c = gl_TexCoord[0].xy;

    // interpolate angle between -pi and pi
    float angle = c.x*PI*2.0 - PI;

    float h = region_size.y;
    float r = radius;
    float dy = c.y * (h + 2.0*r) - (center.y + r);

    // calculate the pixel position to retrieve from the original texture
    vec2 p = vec2(
      r * cos(angle) + center.x,
      r * sin(angle) + center.y + dy
    );

    // convert pixel position to texture UV coordinates
    p /= actual_size;

    // Return color of that pixel if in bounds, else return black.
    if (0.0 <= p.x && p.x < 1.0 && 0.0 <= p.y && p.y < 1.0) {
        gl_FragColor = vec4(texture2D(tex0, p).rgb, 1.0);
    }
    else {
        gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0);
    }
}
"""

class Unwrapper:
    """
    This unwrapper takes an image path and a parsed frame and fulfills
    the operations required to draw the unwrapped image.

    The draw operations MUST be called inside of the "on_draw" callback
    passed to "start_unwrap_window" in order to be fulfilled.  This class
    cannot function without an OpenGL window.
    """
    def __init__(self):

        # Create the shader.
        self.shader = Shader(vertex_shader, fragment_shader)

        # Set the texture unit.
        self.shader.bind()
        self.shader.uniformi('tex0', 0)
        self.shader.unbind()

        # Create a quad geometry to fit the whole window that will be the target of our drawing.
        self.batch = pyglet.graphics.Batch()
        self.batch.add(4, GL_QUADS, None, ('v2i', (0,0, 1,0, 1,1, 0,1)), ('t2f', (0,0, 1,0, 1,1, 0,1)))

    def update(self, image):
        """
        Update the texture to the given image path, and update the shaders with the new
        frame information to unwrap the given image correctly.
        """

        # Load the new image, and update the size variables.
        self.texture = image
        region_w, region_h = self.texture.width, self.texture.height
        actual_w, actual_h = self.texture.owner.width, self.texture.owner.height

        # screen 0:
        bluex = 192 # 420
        bluey = 700 # 876
        redx = 442 # 530
        redy = 708 # 1238
        centerx = (bluex+redx)/2.0
        centery = (bluey+redy)/2.0
        radius = math.sqrt((bluex-redx)**2 + (bluey-redy)**2)/2

        # Update the shader variables.
        self.shader.bind()
        self.shader.uniformf('region_size', region_w, region_h)
        self.shader.uniformf('actual_size', actual_w, actual_h)
        self.shader.uniformf('center', centerx, centery)
        self.shader.uniformf('radius', radius)
        self.shader.unbind()

    def draw(self):
        """Draw the unwrapped image to the window."""
        glBindTexture(self.texture.target, self.texture.id)
        self.shader.bind()
        self.batch.draw()
        self.shader.unbind()
        glBindTexture(self.texture.target, 0)

    def save_image(self, filename):
        """Save the current window image to the given filename."""
        pyglet.image.get_buffer_manager().get_color_buffer().save(filename)

    def get_fps(self):
        """Get the current framerate in frames per second."""
        return pyglet.clock.get_fps()

def start_unwrap_window(width, height, draw_callback):
    """
    This starts the Pyglet OpenGL window and does not return until window has exited.

    draw_callback = a function that is called every frame (usually for the purpose of drawing)
    """

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

    # This is a dummy event whose presence in the event queue causes consistent redrawing.
    # Otherwise, the window would only draw when necessary (e.g. when window is moved).
    pyglet.clock.schedule_interval(lambda dt: None, 1.0/60.0)

    window.set_visible(True)
    pyglet.app.run()

i = 1
dump = True
if __name__ == "__main__":

    unwrapper = Unwrapper()
    image = pyglet.image.load('frames/0001.jpg').get_texture()

    def on_draw():
        global i
        global dump
        if i == 1639:
            dump = False
            i = 1
        image = pyglet.image.load('frames/%04d.jpg' % i).get_texture()
        unwrapper.update(image)
        i = i + 1
        unwrapper.draw()
        if dump:
            unwrapper.save_image('frames/warp%04d.jpg' % i)

    start_unwrap_window(image.width,image.height,on_draw)
