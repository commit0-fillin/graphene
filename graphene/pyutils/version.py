from __future__ import unicode_literals
import datetime
import os
import subprocess

def get_version(version=None):
    """Returns a PEP 440-compliant version number from VERSION."""
    if version is None:
        from graphene import __version__ as version
    main = get_main_version(version)
    sub = ''
    if version[3] != 'final':
        mapping = {'alpha': 'a', 'beta': 'b', 'rc': 'rc'}
        sub = mapping[version[3]] + str(version[4])
    return main + sub

def get_main_version(version=None):
    """Returns main version (X.Y[.Z]) from VERSION."""
    if version is None:
        from graphene import __version__ as version
    parts = 2 if version[2] == 0 else 3
    return '.'.join(str(x) for x in version[:parts])

def get_complete_version(version=None):
    """Returns a tuple of the graphene version. If version argument is non-empty,
    then checks for correctness of the tuple provided.
    """
    if version is None:
        from graphene import __version__ as version
    else:
        assert len(version) == 5
        assert version[3] in ('alpha', 'beta', 'rc', 'final')

    return version

def get_git_changeset():
    """Returns a numeric identifier of the latest git changeset.
    The result is the UTC timestamp of the changeset in YYYYMMDDHHMMSS format.
    This value isn't guaranteed to be unique, but collisions are very unlikely,
    so it's sufficient for generating the development version numbers.
    """
    repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    git_log = subprocess.Popen(
        'git log --pretty=format:%ct --quiet -1 HEAD',
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        shell=True, cwd=repo_dir, universal_newlines=True,
    )
    timestamp = git_log.communicate()[0]
    try:
        timestamp = datetime.datetime.utcfromtimestamp(int(timestamp))
    except ValueError:
        return None
    return timestamp.strftime('%Y%m%d%H%M%S')
