from pathlib import Path
from os import chdir

# Open elevation API
# url = "https://api.open-elevation.com/api/v1/lookup"  # Seems to be offline
URL = "http://localhost:8080/api/v1/lookup"  # Fuck you, I open my own hotel!


# Path to write images out to.
chdir(Path('..'))  # Sets CWD up to project level
OUT_PATH = Path.cwd().joinpath('data', 'output')
