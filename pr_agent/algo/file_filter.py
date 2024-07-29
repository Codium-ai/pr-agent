import fnmatch
import re

from pr_agent.config_loader import get_settings


def filter_ignored(files, platform = 'github'):
    """
    Filter out files that match the ignore patterns.
    """

    try:
        # load regex patterns, and translate glob patterns to regex
        patterns = get_settings().ignore.regex
        if isinstance(patterns, str):
            patterns = [patterns]
        glob_setting = get_settings().ignore.glob
        if isinstance(glob_setting, str):  # --ignore.glob=[.*utils.py], --ignore.glob=.*utils.py
            glob_setting = glob_setting.strip('[]').split(",")
        patterns += [fnmatch.translate(glob) for glob in glob_setting]

        # compile all valid patterns
        compiled_patterns = []
        for r in patterns:
            try:
                compiled_patterns.append(re.compile(r))
            except re.error:
                pass

        # keep filenames that _don't_ match the ignore regex
        if files and isinstance(files, list):
            for r in compiled_patterns:
                if platform == 'github':
                    files = [f for f in files if (f.filename and not r.match(f.filename))]
                elif platform == 'bitbucket':
                    files = [f for f in files if (f.new.path and not r.match(f.new.path))]
                elif platform == 'gitlab':
                    files = [f for f in files if (f['new_path'] and not r.match(f['new_path']))]
                elif platform == 'azure':
                    files = [f for f in files if not r.match(f)]

    except Exception as e:
        print(f"Could not filter file list: {e}")

    return files
