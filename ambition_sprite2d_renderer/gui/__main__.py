"""Entry point: ``python -m ambition_sprite2d_renderer.gui [file.rig.json]``."""

from __future__ import annotations

import argparse
import signal
import sys
from pathlib import Path


def _install_terminal_signal_handlers(app, *, poll_interval_ms: int = 100):
    """Make terminal Ctrl+C / SIGTERM reliably stop the Qt event loop.

    CPython only dispatches Python signal handlers while the interpreter is
    executing Python bytecode.  A Qt event loop can otherwise remain inside
    native code long enough that Ctrl+C appears to do nothing.  The small
    ``QTimer`` periodically returns control to Python, while the signal handler
    asks Qt to leave its event loop cleanly.

    Returns the live timer and a one-item list containing the received signal.
    The caller must keep the timer referenced until ``app.exec()`` returns.
    """
    from PySide6.QtCore import QTimer

    received_signal = [None]

    def request_quit(signum, _frame):
        received_signal[0] = signum
        app.quit()

    signal.signal(signal.SIGINT, request_quit)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, request_quit)

    signal_timer = QTimer()
    signal_timer.setInterval(max(10, int(poll_interval_ms)))
    signal_timer.timeout.connect(lambda: None)
    signal_timer.start()
    return signal_timer, received_signal


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Ambition rig editor (PySide6)")
    parser.add_argument("file", nargs="?", help="rig document (*.rig.json) to open")
    args = parser.parse_args(argv)

    from PySide6.QtWidgets import QApplication

    from ..authoring.rigdoc import RigDocument
    from .app import TEMPLATE_DIR, MainWindow
    from .state import EditorState

    app = QApplication(sys.argv[:1])
    app.setApplicationName("Ambition Rig Editor")
    signal_timer, received_signal = _install_terminal_signal_handlers(app)

    if args.file:
        doc = RigDocument.load(args.file)
        state = EditorState(doc, str(Path(args.file).resolve()))
    else:
        template = TEMPLATE_DIR / "player_robot_fable.rig.json"
        doc = RigDocument.load(template) if template.exists() else RigDocument.new_empty()
        state = EditorState(doc, None)

    win = MainWindow(state)
    win.show()
    exit_code = app.exec()

    # Keep the timer alive through the complete Qt run, then stop it explicitly
    # so application teardown does not emit a late timeout callback.
    signal_timer.stop()
    if received_signal[0] is not None:
        return 128 + int(received_signal[0])
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
