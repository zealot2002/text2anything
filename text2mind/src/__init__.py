"""
Text2Mind - A tool to convert text to XMind mind maps and export them as PNG images.
"""

from .parser import parse_text
from .xmind_generator import create_xmind_from_structure, export_xmind_to_png
from .main import convert, batch_convert

__version__ = '0.1.0' 