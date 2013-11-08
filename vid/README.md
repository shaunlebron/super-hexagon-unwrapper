![Making Videos](../img/title_makingvideos.png)

The following examples use the included video "trailer.mp4", the [Super Hexagon
Trailer](http://www.youtube.com/watch?v=2sz0mI_6tLQ).

(Make sure you run the commands from the project's root directory, and install
the FFmpeg and ImageMagick commands.)

To make a __video of the unwrapped frames__, first dump the frames with the script:
```
python unwrap_video.py vid/trailer.mp4 --out frames
```

Look for the framerate of the source video in the following output:
```
ffmpeg -i vid/trailer.mp4
```

Extract the sound from source video:
```
ffmpeg -i vid/trailer.mp4 vid/trailer.mp3
```

Finally, encode the video from unwrapped frames, assuming a framerate of 30:
```
ffmpeg -r 30 -i frames/unwrap%04d.jpg -i vid/trailer.mp3 -vcodec libx264 -acodec copy vid/unwrap.avi
```

You should get a video that looks like the following (click to watch):

[![unwrapped vid screenshot](../img/vid_unwrap.jpg)](https://vimeo.com/78922670)

To make a __composite video__ that displays both the original and unwrapped on
top of each other, first create the composite frames:
```
for f in frames/orig*.jpg; do \
    echo "creating ${f/orig/comp}"
    montage -tile 1x2 -geometry +0+0 ${f/orig/unwrap} $f ${f/orig/comp}
done
```

Then, encode the video as before but with the new composite frames:
```
ffmpeg -r 30 -i frames/comp%04d.jpg -i vid/trailer.mp3 -vcodec libx264 -acodec copy vid/comp.avi
```

You should get a video that looks like the following (click to watch):

[![composite vid screenshot](../img/vid_comp.jpg)](https://vimeo.com/78922669)


