"""Player Robot v3: a body on the ground is drawn over the ground line.

The rows the robot family lends this rig turn the whole body about the pelvis
(a roll is one full turn). The pelvis is 25 px over the ground and the head
reaches 60 px from it, so half way through a roll the head was drawn 20 px
under the floor. The landings put the boots 3 px under it on their first
frames, for the same reason: the pose was made for another body.

Each frame of the rows of ``GROUNDED`` is drawn, and a frame with paint under
the ground line is lifted by that amount. A frame that is over the line
already is not moved, so a row that leaves the ground (the top of a hop) keeps
its height.

The rig builder calls ``keep_over_ground`` on the finished document. The pass
draws, so the document must know the path of its rig (the art is beside it).
"""

from __future__ import annotations

from typing import Dict, Tuple

from ...authoring.rigdoc import RigDocument

#: Rows whose body is on the ground and whose pose is borrowed.
GROUNDED: Tuple[str, ...] = (
    "roll",
    "roll_back",
    "getup_roll",
    "tech_roll",
    "trip_roll",
    "grab_escape",
    "spot_dodge",
    "land",
    "land_hard",
    "land_recovery",
    "walk_stop",
    "jump_squat",
)


def keep_over_ground(doc: RigDocument, rows: Tuple[str, ...] = GROUNDED) -> Dict[str, float]:
    """Lift each frame of `rows` that has paint under the ground line.
    Returns the largest lift of each row that was changed."""
    ground = float(doc.frame["ground_y"])
    lifted: Dict[str, float] = {}
    for row in rows:
        clip = doc.data["clips"][row]
        n = int(clip["frames"])
        times = [doc.frame_time(row, i, n) for i in range(n)]
        heights = []
        for t in times:
            sampled = doc.sample(row, t).get("root_y", 0.0)
            box = doc.render_at(row, t).getchannel("A").getbbox()
            if box is None:
                raise ValueError(
                    f"{row} draws nothing at {t}: the document has no path to its art"
                )
            under = max(0.0, float(box[3]) - ground)
            heights.append(sampled - under)
            if under > 0.0:
                lifted[row] = max(lifted.get(row, 0.0), under)
        if row not in lifted:
            continue
        keys = [[round(t, 6), round(v, 5)] for t, v in zip(times, heights)]
        if bool(clip.get("loop", True)):
            keys.append([1.0, keys[0][1]])
        clip["channels"]["root_y"] = {"keys": keys}
    return lifted


__all__ = ["GROUNDED", "keep_over_ground"]
