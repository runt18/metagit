import os
import re
from gmp.policy import PolicyMixin
from gmp.tools import *
from gmp.scm import *

class Repository (PolicyMixin):
    """A Repository instance represents exactly one repository"""

    homedir = os.path.expanduser("~/")

    def __init__(self, clone_url, local_url = None, 
                 into = ".", default_policy = "allow", 
                 scm = Git()):
        """clone_url: the url which is used to clone the repository
local_url: to this directory the repository is cloned
into: if local_url is null, the repository is cloned into the <into> directory, and the 
      repository name is appended (without the .git)
default_policy: defines if the repo can be cloned on all machines ("allow") or not 
      ("deny"). See add_policy and check_policy for details"""

        PolicyMixin.__init__(self, default_policy)


        # Save what kind of source control we use
        self.scm = scm

        # After initialisation we aren't in any set
        self.set = []

        self.clone_url = clone_url
        # If no local_url is specified, we use the last part of the clone url
        # without the .git
        if local_url == None:
            m = re.match(".*/([^/]+?)(\\." + scm.binary + ")?$", clone_url)
            if m:
                # Remove .git / .hg or whatever
                self.local_url = os.path.join(into, m.group(1))
            else:
                self.local_url = into
        else:
            if local_url[-1] == '/':
                local_url = local_url[0:-1]
            self.local_url = local_url

        self.local_url = os.path.expanduser(self.local_url)


    def __str__(self):
        """A Repository can be serialized"""
        ret = "{0!s}({1!s}, {2!s}, default_policy = {3!s}, scm = {4!s})".format( 
            self.__class__.__name__,
            repr(self.clone_url),
            repr(self.local_url),
            repr(self.policies[0][1]),
            str(self.scm))

        ret += self.policy_serialize()

        return ret


    def status_line(self):
        sets = ":".join(self.set)
        if sets != "":
            sets = ":" + sets

        local = self.local_url
        if local.startswith(self.homedir):
            local = "~/" + local[len(self.homedir):]
        return "{0!s} ({1!s}{2!s}) {3!s} --> {4!s}".format(self.get_state(), 
                                        self.scm.name, sets, 
                                        self.clone_url, local)


    #
    # Thin Wrappers for the underlying scm implementation
    #
    def get_state(self):
        return self.scm.get_state(self.local_url)

    def execute(self, command, args = [], parallel = False, **kwargs):
        """Will use the self.<command> function if there is one, or
        otherwise use scm.execute to do it directly"""
        if command in dir(self):
            return getattr(self, command)(command, args = args, **kwargs)

        return self.scm.execute(command, args = args, destdir = self.local_url, **kwargs)

    def clone(self, command, args):
        """Clone must be special, because there is no destdir at this very moment"""
        return self.scm.execute(command, args = args)
