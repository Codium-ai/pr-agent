import fnmatch
import re

from pr_agent.config_loader import get_settings

def filter_ignored(files):
    """
    Filter out files that match the ignore patterns.
    """

    try:
        # load regex patterns, and translate glob patterns to regex
        patterns = get_settings().ignore.regex
        patterns += [fnmatch.translate(glob) for glob in get_settings().ignore.glob]

        # compile all valid patterns
        compiled_patterns = []
        for r in patterns:
            try:
                compiled_patterns.append(re.compile(r))
            except re.error:
                pass

        # keep filenames that _don't_ match the ignore regex
        for r in compiled_patterns:
            files = [f for f in files if not r.match(f.filename)]

    except Exception as e:
        print(f"Could not filter file list: {e}")

    return files
