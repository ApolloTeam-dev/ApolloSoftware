Unfortunately we are not allowed to include the frame images done by 'gelb' and
'jobbo' in our distribution of MUI. However, these frame images work perfectly
with this MUI version. All you have to do is to get a recent MorphOS release
(i.e. from http://www.morphos-team.net/morphos-3.9.iso) and copy the frame image
directories from MorphOS/Prefs/MUIGfx/frames over to here. After that those
frame images will be ready for use.

!!! IMPORTANT NOTE FOR AMIGAOS3 USERS !!!
Bitmap frames require a picture.datatype and a PNG datatype both of which are
able to provide the full alpha channel information of a loaded image to the
application. Without suitable components all you will see will be empty frames.
However, AfAOS prodives an enhanced picture.datatype which fullfils MUI's
requirements. So please consider installing AfAOS before you open a ticket in
MUI's bugtracker about missing frame images.


Can I design own bitmap frame images?
Yes of course! There are few guidelines to be respected:
 * the bitmap frame should be saved as PNG. The PNG image format is able to
   handle 24bit truecolor image data along with transparency information (alpha
   channel) with a depth of 8 bits. In contrast to that GIF and ILBM files can
   handle 8bit image data with a single transparent color only (1 bit depth).
 * the bitmap frame image consists of 3 square base images each of which is
   devided up into 9 subsquares. The first (left) base image represents the
   normal/unpressed state of the frame. The second (middle) image represents the
   selected/pressed state of the frame. The third (right) image represents the
   frame and the content area. The full bitmap frame image must have an aspect
   ratio of 9:3, the subparts must have an aspect ratio of 3:3.
   For example, a frame design with 24x24 pixels must have a dimension of 72x24
   pixels.
 * the "corner" parts will be drawn as they are, the "side" parts will be drawn
   repeatedly up to the final frame dimension.
 * the real frame parts (corner and side) of the normal and the selected images
   may have arbitrary imagery, including full 8bit alpha blending. However, the
   third (right) image must be drawn in pure black and white only. The outer
   white area defines the frame's thickness, while the inner black area defines
   the usable area for the object's contents, i.e. the label of a button. Do not
   use other colors than black (RGB 0/0/0) and white (RGB 255/255/255) and use a
   square shape only.
 * imagine the object's final look as a combination of 3 stacked layers:
     - bottom layer: the object's background
     - middle layer: frame
     - top layer:    the object's contents (i.e. the button label)
   This makes clear that the frame's thickness should be chosen in such a way
   that the object's contents do not cover the non-transparent parts of the
   frame imagery.


A very simple ASCII example:

111122223333AAAABBBBCCCC............
111122223333AAAABBBBCCCC............
111122223333AAAABBBBCCCC............
111122223333AAAABBBBCCCC............
4444    5555DDDD    EEEE............
4444    5555DDDD    EEEE.....##.....
4444    5555DDDD    EEEE.....##.....
4444    5555DDDD    EEEE............
666677778888FFFFGGGGHHHH............
666677778888FFFFGGGGHHHH............
666677778888FFFFGGGGHHHH............
666677778888FFFFGGGGHHHH............

corner parts: 1, 3, 6, 8, A, C, F, H
side parts:   2, 4, 5, 7, B, D, E, G
The '.' in the right image must be white pixels, the '#' must be black pixels.

Note that the right images defines a frame thickness of 5 pixels, whereas the
frame imagery might be up to 4 pixels thick only. Thus the frame will have an
additional space of one pixel between the frame imagery and the object contents.
These proportions are your design decisions. The thickness does not need to be
symmetrical. Even something like pixel at the top, 2 pixels on the left,
5 pixels on the right and 4 pixels at the bottom is allowed.

Such a frame design might be drawn like shown below. The additional inner frame
indicated by "+---+" is there to show the additional space between the frame
image and the inner contents as described above. It is not visible within the
MUI GUI.

11112222222222222222222222222222222222222223333
11112222222222222222222222222222222222222223333
11112222222222222222222222222222222222222223333
11112222222222222222222222222222222222222223333
4444                                       5555
4444  +----------------------------------+ 5555
4444  |                                  | 5555
4444  |                                  | 5555
4444  |                                  | 5555
4444  |     This is a normal button      | 5555
4444  |                                  | 5555
4444  |                                  | 5555
4444  |                                  | 5555
4444  +----------------------------------+ 5555
4444                                       5555
66667777777777777777777777777777777777777778888
66667777777777777777777777777777777777777778888
66667777777777777777777777777777777777777778888
66667777777777777777777777777777777777777778888

AAAABBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBCCCC
AAAABBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBCCCC
AAAABBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBCCCC
AAAABBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBCCCC
DDDD                                       EEEE
DDDD +-----------------------------------+ EEEE
DDDD |                                   | EEEE
DDDD |                                   | EEEE
DDDD |                                   | EEEE
DDDD |      This is a pressed button     | EEEE
DDDD |                                   | EEEE
DDDD |                                   | EEEE
DDDD |                                   | EEEE
DDDD +-----------------------------------+ EEEE
DDDD                                       EEEE
FFFFGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGHHHH
FFFFGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGHHHH
FFFFGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGHHHH
FFFFGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGHHHH
