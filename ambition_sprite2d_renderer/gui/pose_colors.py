"""Shared colors for temporal pose direction in the rig editor.

The same colors are used on the canvas, keyframe strip, and navigation
controls so an author never has to remember which ghost is earlier or later.
"""

from __future__ import annotations

from PySide6.QtGui import QColor

BEFORE_POSE_RGB = (90, 195, 255)
AFTER_POSE_RGB = (210, 125, 255)
CURRENT_POSE_RGB = (255, 205, 95)
OTHER_POSE_RGB = (149, 189, 205)


def before_pose_color(alpha: int = 255) -> QColor:
    return QColor(*BEFORE_POSE_RGB, alpha)


def after_pose_color(alpha: int = 255) -> QColor:
    return QColor(*AFTER_POSE_RGB, alpha)


def current_pose_color(alpha: int = 255) -> QColor:
    return QColor(*CURRENT_POSE_RGB, alpha)


def other_pose_color(alpha: int = 255) -> QColor:
    return QColor(*OTHER_POSE_RGB, alpha)
