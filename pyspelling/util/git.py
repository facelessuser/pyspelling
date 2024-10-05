"""Git support."""
import subprocess
import sys
import os

WIN = sys.platform.startswith('win')
GIT_BINARY = "git.exe" if WIN else "git"


def get_git_tree(target):
    """Recursively get Git tree."""

    is_file = os.path.isfile(target)
    folder = os.path.dirname(target) if is_file else target
    if os.path.exists(os.path.join(folder, ".git")):
        return folder
    else:
        parent = os.path.dirname(folder)
        if parent == folder:
            return None
        else:
            return get_git_tree(parent)


def get_git_dir(tree):
    """Get Git directory from tree."""

    return os.path.join(tree, ".git")


def get_file_diff(target, git_binary=None):
    """Get the file list of the HEAD vs the specified target."""

    args = ['--no-pager', 'diff', '--name-only', '--cached', '--merge-base', f'{target}']
    return gitopen(
        args,
        git_binary=git_binary,
        git_tree=get_git_tree(os.path.abspath('.'))
    ).decode('utf-8').splitlines()


def gitopen(args, git_binary=None, git_tree=None):
    """Call Git with arguments."""

    returncode = output = None

    if git_binary is None or not git_binary:
        git_binary = GIT_BINARY

    if git_tree is not None:
        cmd = [git_binary, f"--work-tree={git_tree}", f"--git-dir={get_git_dir(git_tree)}"] + args
    else:
        cmd = [git_binary] + args

    if WIN:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        process = subprocess.Popen(
            cmd,
            startupinfo=startupinfo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False
        )
    else:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
        )
    output = process.communicate()
    returncode = process.returncode

    if returncode != 0:
        raise RuntimeError(output[1].decode('utf-8').rstrip())

    return output[0]
