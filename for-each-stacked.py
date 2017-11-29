#!/usr/bin/env python3
import argparse
import re
import sys
import subprocess
from typing import Callable, List, Optional, Tuple


def runForEachStacked(branchPrefix: str, cmd: List[str], dryrun: bool) -> None:
    isDependentBranch = isDependentBranchGenerator(branchPrefix)

    branchRefs = subprocess.run(
        ['git', 'for-each-ref', 'refs/heads', '--format=%(refname)'],
        stdout=subprocess.PIPE).stdout.decode('utf-8').split()
    dependentBranches = []
    for ref in branchRefs:
        br = ref[len('refs/heads/'):]
        if isDependentBranch(br):
            dependentBranches.append(br)

    command = ' '.join(cmd)
    prevBranch = None
    for branch in sortBranches(dependentBranches):
        run('git checkout {}'.format(branch), dryrun)

        expandedCommand, expanded = expandCommand(command, branch, prevBranch)
        if not expanded:
            print('Failed to expand command on branch {}, skipping ({})'.format(branch, command))
            prevBranch = branch
            continue

        run(expandedCommand, dryrun)
        prevBranch = branch


def isDependentBranchGenerator(branchPrefix: str) -> Callable[[str], bool]:
    match = re.search('(\D+)(\d+)', branchPrefix)
    if match is None:
        # easy, just do regular prefix match
        return lambda br: br.startswith(branchPrefix)

    # prefix is of the form <prefix><number>
    prefix = match.group(1)
    num = int(match.group(2))
    def prefixMatchesAndNumGreaterThan(br: str) -> bool:
        brMatch = re.search('(\D+)(\d+)', br)
        if brMatch is None or brMatch.group(1) != prefix:
            return False
        brNum = int(brMatch.group(2))
        return brNum >= num
    return prefixMatchesAndNumGreaterThan


def sortBranches(branches: List[str]) -> List[str]:
    """
    Alphabetically sorts the branches, but if there are numbers will
    numerically sort so:
    ['branch10', 'branch2'] -> ['branch2', 'branch10']
    """
    def splitByNumber(br: str) -> Tuple:
        match = re.search('(\D+)(\d+)(.*)', br)
        if match is None:
            return (br,)
        return match.group(1), int(match.group(2)), match.group(3)

    splitBranches = map(splitByNumber, branches)
    return [''.join(map(str, tup)) for tup in sorted(splitBranches)]


def expandCommand(command: str, currentBranch: str, prevBranch: Optional[str]) -> Tuple[str, bool]:
    """
    Replaces
    %P with prevBranch,
    %B with currentBranch.
    If couldn't replace e.g. due to prevBranch being None, then does
      no replacement.
    Returns:
        Tuple[expandedCommand, True if succeeded in expanding]
    """
    expandedCommand = command
    if command.find('%P') >= 0:
        if prevBranch is None:
            return command, False
        expandedCommand = command.replace('%P', prevBranch)

    expandedCommand = expandedCommand.replace('%B', currentBranch)
    return expandedCommand, True


def run(cmd: str, dryrun: bool) -> None:
    """
    Like subprocess.run() but prints before command and throws exception on
    failure
    """
    print('> {}'.format(cmd))
    if dryrun:
        return
    proc = subprocess.Popen(cmd, shell=True)
    proc.communicate() # wait for command to finish
    if proc.returncode != 0:
        raise Exception(
            'Command failed with returncode {}'.format(proc.returncode))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Run a command on stacked git branches',
        epilog="""
        You can use placeholders in your command:
        * %P will be replaced by previous i.e. parent branch name
        * %B will be replaced by current branch name

        Example:
          for-each-stacked branch-prefix 'git merge %P'
              Will go to each branch and merge the changes from the parent
              branch into the child branch
        """
    )
    parser.add_argument('--dryrun', dest='dryrun', action='store_const', const=True, default=False)
    parser.add_argument('branchPrefix', type=str)
    parser.add_argument('command', metavar='cmd', type=str, nargs='+')

    args = parser.parse_args()
    if args.dryrun:
        print('running in dryrun mode')
    print('prefix: {}'.format(args.branchPrefix))
    runForEachStacked(args.branchPrefix, args.command, args.dryrun)
