import os
from socket import getfqdn
import re
import sys
import subprocess


# Project specify
from policy import *
from repository import *
from listers import *


#
# The Repository manager
#

class RepoManager:
    """Manages all repositories and provides the command line interface"""
    sets = {}
    help_commands = {"selector": """A selector is a regexp which is checked against
<sets>:<clone-url> of a repository. So '^<set>:' will only select repositories within a given set."""}

    def __init__(self):
        self.hostname = getfqdn()
        self.commands = {"list": self.cmd_list,
                         "clone": self.cmd_clone,
                         "foreach": self.cmd_foreach,
                         "status" : self.shortcut("status"),
                         "commit" : self.shortcut("commit"),
                         "push" : self.shortcut("push"),
                         "pull" : self.shortcut("pull"),
                         "fetch" : self.shortcut("fetch"),
                         "sets"  : self.cmd_sets,
                         "clean" : self.cmd_clean,
                         "help" : self.cmd_help}

    def __call__(self):
        """The Reposity Manager can be called in order to start the command
line interface"""
        args = sys.argv[1:]
        if len(args) < 1:
            self.die("Too less arguments")

        if args[0] in self.commands:
            self.commands[args[0]](args[1:])
        else:
            self.die("Command not found: " + args[0])

    def die(self, msg):
        print msg
        print
        print "Commands: " + ", ".join(self.commands.keys())
        
        sys.exit(-1)


    def add_set(self, set_name, repo_list):
        """You can add a list of repositories to a set"""
        if not set_name in self.sets:
            self.sets[set_name] = []
        self.sets[set_name].extend(repo_list)

    def _select(self, selector):
        selector = ".*" + selector
        repos = []
        for s in self.sets.keys():
            for repo in self.sets[s]:
                if (selector == ".*all" or re.match(selector, repo.status_line())) \
                        and repo.check_policy(self.hostname):
                    repos.append(repo)
        return repos
    
    def cmd_list(self, selector):
        """Lists all repositories, which matches the selector. If no selector given 
list all repositories. See help selector for help with selectors.

metagit list == metagit list all

usage: metagit list <selector>"""
        if len(selector) == 0:
            selector = ["all"]
        repos = self._select(selector[0])
        for repo in repos:
            print repo.status_line()
        
    def cmd_clone(self, selector):
        if len(selector) == 0:
            selector = ["all"]

        repos = self._select(selector[0])
        for repo in repos:
            directory = os.path.dirname(repo.local_url)
            if not os.path.exists(directory):
                print("mkdir -p " + directory)
                os.makedirs(directory)
            if os.path.exists(repo.local_url):
                continue
            print repo.git_clone()
            a = subprocess.Popen(repo.git_clone(), shell = True)
            a.wait()

    def _shortcut(self, args):
        if len(args) == 0:
            return ["all"]
        return args

    def shortcut(self, git_command, help = None):
        if not help:
            help = "alias %s <selector> = foreach <selector> %s" %(git_command, git_command)
        func = lambda x: self.cmd_foreach([self._shortcut(x)[0], git_command] + self._shortcut(x)[1:])
        func.__doc__ = help
        return func

    def cmd_foreach(self, args):
        """usage: metagit foreach <selector> <git-command>
 executes git command on all repositories matching the selector

help selector for more information on selectors"""
        if len(args) < 2:
            self.die("Not enough arguments")
        repos = self._select(args[0])
        for repo in repos:
            if not os.path.exists(repo.local_url + "/.git"):
                continue
            os.chdir(repo.local_url)
            command = "git " + repo.git_alias(args[1]) + " " + (" ".join(repo.git_option(args[1]))) + " " + " ".join(args[2:])
            print "cd %s; %s"%(repo.local_url, command)
            a = subprocess.Popen(command, shell = True)
            a.wait()

    def cmd_sets (self, args):
        """Show only git repository sets"""
        if len(args) < 1:
            args = [".*all"]
        else:
            args[0] = ".*" + args[0]

        for key in self.sets.keys():
            if args[0] == ".*all" or re.match(args[0], key):
                print "%s:" % key
                for repo in self.sets[key]:
                    print "  " + repo.clone_url + " --> " + repo.local_url

    def cmd_clean(self, args):
        """Deletes all Cache files used by directory Listers"""
        for lister in RepoLister.listers:
            if lister.cache:
                try:
                    os.unlink(lister.cache)
                except:
                    pass

    def cmd_help(self, args):
        """recursive: see recursive"""
        if len(args) < 1:
            self.die("No topic selected")
        if args[0] in self.commands:
            doc = self.commands[args[0]].__doc__
            if doc:
                print doc
            else:
                self.die("No help available")

        elif args[0] in self.help_commands:
            print self.help_commands[args[0]]

        else:
            self.die("No help available")
