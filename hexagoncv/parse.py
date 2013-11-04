from SimpleCV import *

from simplify_blob import simplify_by_area, simplify_by_angle

class ParsedFrame:

    def __init__(self, img, center_blob, center_img):

        self.img = img
        self.center_img = center_img
        self.center_point = None
        self.center_vertices = None

        # Just assume center of image is center point instead of using the
        # center_blob.centroid()
        w,h = img.size()
        self.center_point = (w/2, h/2)
        self.center_vertices = simplify_by_angle(center_blob.hull())
    
    def draw_frame(self, layer, linecolor=(255,0,0), pointcolor=Color.WHITE):
        width = 10
        layer.polygon(self.center_vertices, color=linecolor,width=width)
        c = self.center_point
        mag = 100
        for p in self.center_vertices:
            p2 = (c[0] + mag*(p[0]-c[0]), c[1] + mag*(p[1]-c[1]))
            layer.line(c,p2,color=linecolor,width=width)

        def circle(p):
            layer.circle(p, 10, color=linecolor, filled=True)
            layer.circle(p, 5, color=pointcolor, filled=True)

        circle(self.center_point)
        for p in self.center_vertices:
            circle(p)

def parse_frame(img):
    """
    Parses a frame from Super Hexagon.
    Returns the center blob, the cursor blob, and an image drawing their locations.
    """

    # helper image size variables
    w,h = img.size()
    midx,midy = w/2,h/2

    # Normalize the image by undoing any inversion of color.
    # fg_img = foreground image (white walls)
    # bg_img = background image (white space)
    fg_img = img
    if sum(img.binarize().getPixel(midx,midy)) == 0:
        fg_img = img.invert()
    bg_img = fg_img.invert()

    # Locate the CENTER blob.
    # (the black blob at the center of the white wall image)
    center_blob = None
    center_img = bg_img.erode()
    blobs = center_img.findBlobs()
    if blobs:
        size = 260
        for b in blobs:
            try:
                if b.width() < size and b.height() < size and b.contains((midx,midy)):
                    center_blob = b
                    break
            except ZeroDivisionError:
                continue

    if center_blob:
        return ParsedFrame(img, center_blob, center_img)
    else:
        return None

if __name__ == "__main__":

    # Run a test
    display = Display()
    p = parse_frame(Image('test.jpg'))
    if p:
        img = p.center_img.binarize()
        p.draw_frame(img.dl())
        img.show()

	while display.isNotDone():
		try:
			pass
		except KeyboardInterrupt:
			display.done = True
		if display.mouseRight:
			display.done = True
	display.quit()
