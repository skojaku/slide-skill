"""Allow running as: python3 -m gatelib <command>"""
from .cli import main
import sys
sys.exit(main())
