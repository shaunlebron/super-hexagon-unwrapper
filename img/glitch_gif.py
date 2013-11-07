"""
The script creates a glitchy gif (i.e. stutters and skips)...
from a file containing a "HEADER LINE" followed by "SEQUENCE LINES":

HEADER LINE:

    <output filename> <format string for selecting frames> <misc imagemagick args>

    Example: test.gif frame%04d.jpg -delay 1x30 -layers RemoveDups

COMMENT LINE:

    Any line starting with '#' is ignored and can be used for comments.

SEQUENCE LINE:

    <start frame> <duration> <repeat count>

        Start frame:
            The frame to jump to.
            If frame < 0, then it will continue from the previous sequence.

        Duration:
            The number of frames to play from the start frame.  Must be > 0.

        Repeat count:
            The number of times to play this sequence. Must be > 0.

    Example:
        4 3 2 will generate frames 4 5 6 4 5 6

    Helpful Pause Patterns:

        (frame 1 N):
            Pauses at a frame for N frames.

        (-1 1 N):
            Pauses after the previous segment for N frames.
"""

import argparse
import subprocess

class GlitchPlayer:
    def __init__(self):
        self.i = 0

    def next_frames(self,seg):
        """
        Continues the track with the given segment specification.
        """
        start,duration,repeat = seg
        if duration <= 0:
            raise Exception("duration must be > 0: "+seg)
        if repeat <= 0:
            raise Exception("repeat must be > 0: "+seg)
        if start < 0:
            start = self.i
        self.i = start + duration
        return range(start,start+duration)*repeat

def lines_to_segs(lines):
    segs = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            tokens = map(int,line.split())
            if len(tokens) != 3:
                raise Exception('there must be 3 tokens specified per line: '+line)
            segs.append(tokens)
    return segs

def segs_to_frames(segs):
    player = GlitchPlayer()
    frames = []
    for s in segs:
        frames.extend(player.next_frames(s))
    return frames

def make_gif_from_frames(frames, format_str, output_name, args=[]):
    cmd = ['convert'] + args + [format_str % f for f in frames] + [output_name]
    print ' '.join(cmd)
    subprocess.call(cmd)

def parse_file_header(line):
    tokens = line.split()
    return {
        'output_name': tokens[0],
        'format_str': tokens[1],
        'args': tokens[2:],
    }

def make_gif_from_file(f):
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            header = parse_file_header(line)
            break
    segs = lines_to_segs(f)
    frames = segs_to_frames(segs)
    if frames:
        print "making gif with %d frames" % len(frames)
        make_gif_from_frames(frames,**header)
    else:
        print "no frames to operate on."

if __name__ == "__main__":
    desc = "Create a gif from the given glitch file.  (See the file's __doc__ for more details.)"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('track_file', type=file)
    args = parser.parse_args()
    make_gif_from_file(args.track_file)
