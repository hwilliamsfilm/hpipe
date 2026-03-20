"""
Pipe Layer Viewer GUI.
Re-exports OutputViewer from pipeDisplay so both apps share a single implementation.
"""
from hpipe.apps.pipeDisplay.output_gui import OutputViewer, ThumbnailLoader  # noqa: F401
