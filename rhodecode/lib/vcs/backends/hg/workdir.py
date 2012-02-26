from rhodecode.lib.vcs.backends.base import BaseWorkdir
from rhodecode.lib.vcs.exceptions import BranchDoesNotExistError

from ...utils.hgcompat import hg_merge


class MercurialWorkdir(BaseWorkdir):

    def get_branch(self):
        return self.repository._repo.dirstate.branch()

    def get_changeset(self):
        return self.repository.get_changeset()

    def checkout_branch(self, branch=None):
        if branch is None:
            branch = self.repository.DEFAULT_BRANCH_NAME
        if branch not in self.repository.branches:
            raise BranchDoesNotExistError

        hg_merge.update(self.repository._repo, branch, False, False, None)
