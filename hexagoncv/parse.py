"""
This parses a frame from Super Hexagon to extract the features we want, using
Computer Vision.
"""

from SimpleCV import *

from simplify_blob import simplify_by_area, simplify_by_angle

class ParsedFrame:
    """
    This holds the features that we wish to extract from a Super Hexagon frame.
    """

    def __init__(self, img, center_blob, center_img):
        """
        img         = SimpleCV Image object of the original image
        center_blob = SimpleCV Blob object of the center polygon
        center_img  = SimpleCV Image object used to detect center polygon
        """

        self.img = img
        self.center_img = center_img

        # midpoint of the center polygon
        # (Just assume center of image is center point instead of using
        # center_blob.centroid())
        w,h = img.size()
        self.center_point = (w/2, h/2)

        # vertices of the center polygon
        # (remove redundant vertices)
        self.center_vertices = simplify_by_angle(center_blob.hull())
    
    def draw_frame(self, layer, linecolor=Color.RED, pointcolor=Color.WHITE):
        """
        Draw the reference frame created by our detected features.
        (for debugging)

        layer = SimpleCV Image Layer object to receive the drawing operations
        """

        # Draw the center polygon.
        width = 10
        layer.polygon(self.center_vertices, color=linecolor,width=width)

        # Draw the axes by extending lines from the center past the vertices.
        c = self.center_point
        length = 100
        for p in self.center_vertices:
            p2 = (c[0] + length*(p[0]-c[0]), c[1] + length*(p[1]-c[1]))
            layer.line(c,p2,color=linecolor,width=width)
        
        # Draw the reference points (center and vertices)
        def circle(p):
            layer.circle(p, 10, color=linecolor, filled=True)
            layer.circle(p, 5, color=pointcolor, filled=True)
        circle(self.center_point)
        for p in self.center_vertices:
            circle(p)

def parse_frame(img):
    """
    Parses a SimpleCV image object of a frame from Super Hexagon.
    Returns a ParsedFrame object containing selected features.
    """

    # helper image size variables
    w,h = img.size()
    midx,midy = w/2,h/2

    # Create normalized images for targeting objects in the foreground or background.
    # (This normalization is handy since Super Hexagon's colors are inverted for some parts of the game)
    # fg_img = foreground image (bright walls, black when binarized)
    # bg_img = background image (bright space, black when binarized)
    fg_img = img
    if sum(img.binarize().getPixel(midx,midy)) == 0:
        fg_img = img.invert()
    bg_img = fg_img.invert()

    # Locate the CENTER blob.

    # We need to close any gaps around the center wall so we can detect its containing blob.
    # The gaps are resulting artifacts from video encoding.
    # The 'erode' function does this by expanding the dark parts of the image.
    center_img = bg_img.erode()

    # Locate the first blob within a given size containing the midpoint of the screen.
    center_blob = None
    blobs = center_img.findBlobs()
    if blobs:
        size = h * 0.6667
        for b in blobs:
            try:
                if b.width() < size and b.height() < size and b.contains((midx,midy)):
                    center_blob = b
                    break
            except ZeroDivisionError:
                # blob 'contains' function throws this exception for some cases.
                continue

    if center_blob:
        return ParsedFrame(img, center_blob, center_img)
    else:
        return None

if __name__ == "__main__":

    # Run a test by drawing the reference frame parsed from a screenshot.
    display = Display()
    p = parse_frame(Image('test.jpg'))
    if p:
        img = p.center_img.binarize()
        p.draw_frame(img.dl())
        img.show()

    # Wait for user to close the window or break out of it.
    while display.isNotDone():
        try:
            pass
        except KeyboardInterrupt:
            display.done = True
        if display.mouseRight:
            display.done = True
    display.quit()
