"""The hand generator: hands drawn at the Dealer's Hand's level of detail,
from one 3D model, in any pose and from either side.

A ``HandSpec`` (the skeleton and proportions, right or left) is posed by a
``HandPose`` (finger curls, thumb opposition, spread, hook), seen by a
``Camera`` (where the wrist is, which way the fingers point, the roll from
palm to back), and drawn by ``draw_hand`` in a ``HandStyle`` ("skin",
"spectral", "glove"): the 3D model places, the 2D parts draw. Landmarks
(joints, tips, the grip) let a caller hang a ring, a cuff or a held item on
it. ``solve`` poses by contact: a ``grip`` closes on a rod of any size, a
``pinch`` meets two fingertips. ``reference`` renders the model's turnaround and the drawn pose sheets;
``python -m ambition_sprite2d_renderer.handgen --help``.
"""

from .draw import STYLES, HandDrawing, HandStyle, draw_hand, paint_order
from .model import DIGIT_NAMES, FINGER_NAMES, SPECS, Camera, FingerSpec, HandPose, HandSpec, digits, landmarks
from .poses import POSES, blend
from .solve import Capsule, Rod, close_until_contact, grip, pinch, rest_tip_on, touch

__all__ = [
    "DIGIT_NAMES", "FINGER_NAMES", "POSES", "SPECS", "STYLES", "Camera", "FingerSpec", "HandDrawing", "HandPose", "HandSpec", "HandStyle",
    "Capsule", "Rod", "blend", "close_until_contact", "digits", "draw_hand", "grip", "paint_order", "landmarks", "pinch", "rest_tip_on", "touch",
]
