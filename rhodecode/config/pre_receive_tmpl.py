#!/usr/bin/env python
import os
import sys

try:
    import rhodecode
    RC_HOOK_VER = '_TMPL_'
    os.environ['RC_HOOK_VER'] = RC_HOOK_VER
    from rhodecode.lib.hooks import handle_git_pre_receive
except ImportError:
    rhodecode = None


def main():
    if rhodecode is None:
        # exit with success if we cannot import rhodecode !!
        # this allows simply push to this repo even without
        # rhodecode
        sys.exit(0)

    repo_path = os.path.abspath('.')
    push_data = sys.stdin.readlines()
    # os.environ is modified here by a subprocess call that
    # runs git and later git executes this hook.
    # Environ get's some additional info from rhodecode system
    # like IP or username from basic-auth
    handle_git_pre_receive(repo_path, push_data, os.environ)
    sys.exit(0)

if __name__ == '__main__':
    main()
