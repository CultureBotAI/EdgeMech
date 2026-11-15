"""2026-11-15, #114: keep raw targeting payloads out of Git-visible outputs.

Input: a proposed output path. Output: validation only; no files are created.
Established ignored staging and paths outside Git worktrees are permitted.
"""

import subprocess
from pathlib import Path


def validate_private_output(path):
    """Refuse traversal, symlinks, tracked paths and nonignored worktree paths."""
    path = Path(path)
    if '..' in path.parts:
        raise ValueError('Private targeting output cannot contain parent traversal')
    candidate = path.absolute()
    if any(component.is_symlink() for component in (candidate, *candidate.parents)):
        raise ValueError('Private targeting output cannot use symlinked paths')
    candidate = candidate.resolve()
    repo = next((parent for parent in candidate.parents
                 if (parent / '.git').exists() or (parent / '.git').is_symlink()), None)
    if repo is None:
        return
    relative = candidate.relative_to(repo)
    if '.git' in relative.parts:
        raise ValueError('Private targeting output cannot use Git metadata paths')
    command = ['git', '-C', str(repo)]
    tracked = subprocess.run([*command, '--literal-pathspecs', 'ls-files',
                              '--error-unmatch', '--', str(relative)],
                             stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if tracked.returncode not in (0, 1):
        raise ValueError('Cannot verify private targeting output against the Git index')
    if tracked.returncode == 0:
        raise ValueError('Private targeting output cannot be a tracked path')
    ignored = subprocess.run([*command, 'check-ignore', '-q', '--', str(relative)],
                             stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if ignored.returncode != 0:
        raise ValueError('Private targeting output must be Git-ignored within a worktree')
