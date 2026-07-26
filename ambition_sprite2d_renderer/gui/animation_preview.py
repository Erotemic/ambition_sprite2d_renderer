"""Independent live-loop preview for the rig editor.

The main canvas is an editing surface: it stays parked on the pose, bone, and
geometry the author is manipulating.  This pane continuously loops the current
clip from the same in-memory document so every edit can be judged in motion
without moving the editing playhead.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QElapsedTimer, QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .canvas import pil_to_qimage
from .state import EditorState

try:
    from line_profiler import profile
except ImportError:  # Optional developer dependency.
    from ..profiling import profile


PREVIEW_INTERVAL_MS = 40  # 25 fps is smooth enough for a small diagnostic pane.
PREVIEW_SUPERSAMPLE = 1


class LoopPreviewCanvas(QWidget):
    """Small independent viewport that loops ``state.clip_name`` continuously."""

    frameAdvanced = Signal(int, int)

    def __init__(self, state: EditorState, parent=None) -> None:
        super().__init__(parent)
        self.state = state
        self._image: Optional[QImage] = None
        self._error: Optional[str] = None
        self._clip_name = state.clip_name
        self._playing = True
        self._phase_offset_ms = 0.0
        self._clock = QElapsedTimer()
        self._clock.start()
        self._timer = QTimer(self)
        self._timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._timer.setInterval(PREVIEW_INTERVAL_MS)
        self._timer.timeout.connect(self._tick)
        self._timer.start()
        self.setMinimumSize(220, 190)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setToolTip(
            "Independent loop preview. It uses the current in-memory rig but does "
            "not move the editing playhead."
        )

        state.poseChanged.connect(self._document_changed)
        state.docChanged.connect(self._document_changed)
        state.timeChanged.connect(self._time_or_clip_changed)

    def _cycle_ms(self) -> float:
        clip = self.state.clip()
        frames = max(1, int(clip.get("frames", 1)))
        frame_ms = max(1, int(clip.get("duration_ms", 100)))
        return float(frames * frame_ms)

    def normalized_time(self) -> float:
        cycle_ms = self._cycle_ms()
        elapsed = float(self._clock.elapsed()) if self._playing else 0.0
        return ((self._phase_offset_ms + elapsed) % cycle_ms) / cycle_ms

    def set_playing(self, playing: bool) -> None:
        playing = bool(playing)
        if playing == self._playing:
            return
        if playing:
            self._clock.restart()
            self._playing = True
            self._timer.start()
        else:
            cycle_ms = self._cycle_ms()
            self._phase_offset_ms = self.normalized_time() * cycle_ms
            self._playing = False
            self._timer.stop()
        self._render_current()

    def reset_loop(self) -> None:
        self._phase_offset_ms = 0.0
        self._clock.restart()
        self._render_current()

    def _time_or_clip_changed(self) -> None:
        # Main-playhead motion must not disturb this viewport. Only a clip switch
        # restarts the independent loop.
        if self.state.clip_name != self._clip_name:
            self._clip_name = self.state.clip_name
            self.reset_loop()

    def _document_changed(self) -> None:
        # The playing preview already refreshes at 25 fps. Do not synchronously
        # render again for every mouse-move signal during a drag; that would make
        # the editing surface pay for two renders per event. A paused preview does
        # need one immediate refresh at its frozen phase.
        if not self._playing:
            self._render_current()

    def _tick(self) -> None:
        if not self.isVisible():
            return
        self._render_current()

    @profile
    def _render_current(self) -> None:
        clip_name = self.state.clip_name
        if clip_name not in self.state.doc.clips:
            return
        t = self.normalized_time()
        try:
            image = self.state.doc.render_at(
                clip_name,
                t,
                supersample=PREVIEW_SUPERSAMPLE,
            )
            self._image = pil_to_qimage(image)
            self._error = None
            frames = max(1, int(self.state.clip().get("frames", 1)))
            frame = min(frames - 1, int(t * frames))
            self.frameAdvanced.emit(frame, frames)
        except Exception as ex:  # noqa: BLE001 - mid-edit documents can be invalid.
            self._error = f"{type(ex).__name__}: {ex}"
        self.update()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self._playing:
            self._timer.start()
        self._render_current()

    def hideEvent(self, event) -> None:
        self._timer.stop()
        super().hideEvent(event)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(28, 25, 32))
        if self._image is None and self._error is None:
            self._render_current()
        image = self._image
        if image is not None:
            margin = 10.0
            available_w = max(1.0, self.width() - 2.0 * margin)
            available_h = max(1.0, self.height() - 2.0 * margin)
            scale = min(available_w / image.width(), available_h / image.height())
            target_w = image.width() * scale
            target_h = image.height() * scale
            target = QRectF(
                (self.width() - target_w) / 2.0,
                (self.height() - target_h) / 2.0,
                target_w,
                target_h,
            )
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
            painter.setPen(QPen(QColor(89, 82, 98), 1))
            painter.drawRect(target)
            painter.drawImage(target, image, QRectF(image.rect()))
        if self._error:
            painter.setPen(QPen(QColor(255, 120, 120), 1))
            painter.drawText(
                QRectF(12, 12, self.width() - 24, self.height() - 24),
                Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                self._error,
            )
        painter.end()


class AnimationPreviewPanel(QWidget):
    """Compact controls plus :class:`LoopPreviewCanvas`."""

    def __init__(self, state: EditorState, parent=None) -> None:
        super().__init__(parent)
        self.state = state
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(5)

        header = QHBoxLayout()
        self.clip_label = QLabel()
        self.clip_label.setToolTip("This preview always follows the selected clip")
        header.addWidget(self.clip_label, stretch=1)
        self.frame_label = QLabel()
        self.frame_label.setMinimumWidth(54)
        self.frame_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header.addWidget(self.frame_label)
        self.play_button = QToolButton()
        self.play_button.setCheckable(True)
        self.play_button.setChecked(True)
        self.play_button.setText("Pause")
        self.play_button.setToolTip("Pause only this live preview")
        header.addWidget(self.play_button)
        self.restart_button = QToolButton()
        self.restart_button.setText("Restart")
        self.restart_button.setToolTip("Restart this preview loop without moving the editing playhead")
        header.addWidget(self.restart_button)
        root.addLayout(header)

        self.canvas = LoopPreviewCanvas(state)
        root.addWidget(self.canvas, stretch=1)

        self.play_button.toggled.connect(self._set_playing)
        self.restart_button.clicked.connect(self.canvas.reset_loop)
        self.canvas.frameAdvanced.connect(self._show_frame)
        state.timeChanged.connect(self._refresh_clip_label)
        state.docChanged.connect(self._refresh_clip_label)
        self._refresh_clip_label()

    def _set_playing(self, playing: bool) -> None:
        self.play_button.setText("Pause" if playing else "Play")
        self.canvas.set_playing(playing)

    def _show_frame(self, frame: int, frames: int) -> None:
        self.frame_label.setText(f"{frame + 1}/{frames}")

    def _refresh_clip_label(self) -> None:
        self.clip_label.setText(f"Loop: {self.state.clip_name}")
