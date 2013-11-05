"""
Shows the given Super Hexagon video next to an unwrapped* version of it.

*unwrapped means the walls fall top-to-bottom instead of out-to-in.
"""

import sys
import os
import argparse

# SimpleCV image processing and computer vision library
import SimpleCV as scv

# Custom "Super Hexagon" parsing library
from hexagoncv.parse import parse_frame
from hexagoncv.unwrap import start_unwrap_window, Unwrapper

class VideoDone(Exception):
    """
    Used to signal when video is done processing.  We need an exception for
    this since there seems to be no other way to handle this smoothly.
    """
    pass

def unwrap_video(video_path, start_frame=0, stop_frame=-1, dump_dir=None, print_log=True):
    """
    Shows the given Super Hexagon video next to an unwrapped* version of it.

    *unwrapped means the walls fall top-to-bottom instead of out-to-in.

    video_path  = path to the Super Hexagon video
    start_frame = start at this frame in the video
    stop_frame = stop at this frame in the video
    frames_dir  = directory to dump the frames in
    """

    def log(*args):
        """
        Helper function to display messages on the same line.
        """
        if print_log:
            sys.stdout.write('\r' + ' '.join(map(str, args)).ljust(60))
            sys.stdout.flush()

    # Create virtual camera for reading the video.
    video = scv.VirtualCamera(video_path, 'video')

    # Create frames output directory.
    if dump_dir:
        if not os.path.exists(dump_dir):
            os.makedirs(dump_dir)

    # Skip to the starting frame.
    i = 0
    while i < start_frame:
        video.getImage()
        log("skipping frame:",i)
        i += 1

    # create unwrapper
    unwrapper = Unwrapper()

    # get first image so we can correctly size the gl window
    img = video.getImage()
    w,h = img.size()

    # create state object for the "on_draw" callback
    self = {
        "i": i,
        "total": 0,
        "first_img": img,
    }

    def get_dump_name(prefix):
        """
        Get the filename of the dumped frame.
        """
        return "%s/%s%04d.jpg" % (dump_dir, prefix, self["i"])

    def on_draw():
        """
        Our main processing loop that is called by the OpenGL window draw event.
        """

        # get first image or read next image
        img = self["first_img"]
        if img:
            self["first_img"] = None
        else:
            img = video.getImage()

        # Try to show the retrieved image in SimpleCV's own window.  If it
        # fails, then we reached the end of the video and can raise the custom
        # VideoDone exception.
        try:
            img.show()
        except:
            raise VideoDone()

        # Print log message
        if dump_dir:
            log('processing/dumping frame:', self["i"],'(%d fps)' % unwrapper.get_fps())
        else:
            log('processing frame:', self["i"],'(%d fps)' % unwrapper.get_fps())

        # Get the features out of the image.
        frame = parse_frame(img)

        # Create file names of the dumped frames.
        orig_name = get_dump_name('orig')
        unwrap_name = get_dump_name('unwrap')

        # Generate and show the unwrapped image.
        if frame:
            if not dump_dir:
                # Write the image to a temp file so pyglet can read the texture.
                img.save('tmp.jpg')
                unwrapper.update('tmp.jpg', frame)
                unwrapper.draw()
            else:
                # Dump the original frame.
                img.save(orig_name)

                # Update the unwrapper and draw the unwrapped frame.
                unwrapper.update(orig_name, frame)
                unwrapper.draw()

                # Dump the unwrapped frame.
                unwrapper.save_image(unwrap_name)
        else:
            if dump_dir:
                # dump the current images if the parsing failed
                img.save(orig_name)
                unwrapper.save_image(unwrap_name)

        self["total"] += 1

        # Stop processing if we reached the last requested frame.
        if self["i"] == stop_frame:
            raise VideoDone()

        self["i"] += 1

    # Run the opengl window until the last video frame is processed.
    try:
        start_unwrap_window(w,h,on_draw)
    except VideoDone:
        pass

    # Try to remove the temporary image file.
    if not dump_dir:
        try:
            os.remove('tmp.jpg')
        except OSError:
            pass

    # Print final log message.
    if dump_dir:
        log('Dumped',self["total"],'frames to "%s".' % dump_dir)
    else:
        log(self["total"],'frames processed.')

    # Append new line so the terminal can continue after our log line.
    if print_log:
        print

if __name__ == "__main__":

    # Create argument parser
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawTextHelpFormatter)
        #usage="%(prog)s [options] video")
    parser.add_argument('video', help='path to video of super hexagon')
    parser.add_argument('--dumpdir', help='dump frames into this directory')
    parser.add_argument('--start', type=int, help='start at this frame of the video')
    parser.add_argument('--stop', type=int, help='stop at this frame of the video')
    args = parser.parse_args()

    # Create optional args from those parsed
    opts = {}
    if args.dumpdir:
        opts['dump_dir'] = args.dumpdir
    if args.start:
        opts['start_frame'] = args.start
    if args.stop:
        opts['stop_frame'] = args.stop

    # Unwrap video
    unwrap_video(args.video, **opts)
