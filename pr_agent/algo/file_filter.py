import fnmatch
import re

from pr_agent.config_loader import get_settings

def filter_ignored(files):
    """
    Filter out files that match the ignore patterns.
    """

    # load regex patterns, and translate glob patterns to regex
    patterns = get_settings().ignore.regex
    patterns += [fnmatch.translate(glob) for glob in  get_settings().ignore.glob]

    compiled_patterns = [re.compile(r) for r in patterns]
    filenames = [file.filename for file in files]

    # keep filenames that don't match the ignore regex
    for r in compiled_patterns:
        filenames = [f for f in filenames if not r.match(f)]

    # map filenames back to files
    return [file for file in files if file.filename in filenames]
