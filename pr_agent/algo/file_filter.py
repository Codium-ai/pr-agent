import fnmatch
import re

from pr_agent.config_loader import get_settings

def filter_ignored(files):
    """
    Filter out files that match the ignore patterns.
    """

    # load regex patterns, and translate glob patterns to regex
    patterns = get_settings().ignore.regex
    patterns += [fnmatch.translate(glob) for glob in get_settings().ignore.glob]

    # compile regex patterns
    compiled_patterns = [re.compile(r) for r in patterns]

    # keep filenames that _don't_ match the ignore regex
    for r in compiled_patterns:
        files = [f for f in files if not r.match(f.filename)]

    return files
