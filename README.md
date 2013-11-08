![Super Hexagon Unwrapper](img/header.png)

[![comparison](img/comparison.gif)](https://vimeo.com/78922669)

__[Super Hexagon](http://superhexagon.com/)__ (shown above on the left) is a
game by Terry Cavanagh.  This project warps that image into a different
perspective (shown above on the right).  Angular motion is converted into
lateral motion, resulting in two different representations for the same
gameplay.  (Click the image above to see the video).

This project is written in Python.  It employs Computer Vision algorithms
provided by __[SimpleCV](http://www.simplecv.org/)__ to establish a reference
frame in the image.  Then it warps (or "unwraps") the image based on that
reference frame, using OpenGL fragment shaders.  ([more details here](code))

```
Unwrap a video:
> python unwrap_video.py vid/trailer.mp4
```

![screenshot](img/screenshot.jpg)

```
Script options

--help          (show all options)
--start N       (start at frame N)
--stop N        (stop at frame N)
--out DIR       (dump all frames into the given DIR)

Script Dependencies

* Python 2.7
* SimpleCV 1.3  (for video processing and computer vision)
* Pyglet        (for fast image transforms with OpenGL shaders)
```

* [Encode a video](vid)
* [Learn how it works](code)




_This program is free software: you can redistribute it and/or modify it under the terms
of the GNU General Public License Version 3 as published by the Free Software Foundation._
