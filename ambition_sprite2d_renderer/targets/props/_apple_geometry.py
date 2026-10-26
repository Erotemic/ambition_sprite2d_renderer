"""The body and leaf geometry shared by GNU-ton's apple and apple creatures.

Coordinates use the original 512-unit GNU-ton projectile canvas. Keep its
published PNG stable when updating the character sprites.
"""

BODY_LOBES = (
    (102, 112, 410, 456),
    (56, 158, 292, 462),
    (220, 158, 456, 462),
    (150, 260, 362, 498),
)
STEM_NOTCH = (206, 74, 306, 176)
LEAF_MAIN = ((252, 122), (352, 88), (404, 140), (350, 196), (258, 178))
LEAF_FAR = ((246, 126), (176, 158), (216, 214), (282, 184))
STEM_MAIN = (286, 130, 266, 62)

__all__ = ["BODY_LOBES", "STEM_NOTCH", "LEAF_MAIN", "LEAF_FAR", "STEM_MAIN"]
