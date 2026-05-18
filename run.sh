#!/bin/zsh
# Wrapper script called by the Mac Shortcut.
# Usage: ./run.sh "your event text here"
cd /Users/eugenio/cool_programs/voice-calendar-ai
source venv/bin/activate
python main.py --text "$*" 2>&1
