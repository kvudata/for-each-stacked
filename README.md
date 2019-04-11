# for-each-stacked
A utility for making it easier to work with dependent branches.

On GitHub you operate on a multiple branches model, and if you want to provide your colleagues with easy-to-digest, bite-sized PRs to review, you make your PR branches dependent on each other, resulting in a stack of PRs.
But what happens when you get feedback on a PR at the bottom of your stack, and need to percolate an update to all the dependent branches?

`for-each-stacked` encourages a workflow to make this easier to manage. By following a simple naming scheme for your branches, `for-each-stacked` can manage running operations across the stack of branches:

```
> git checkout -b feature/p1-foo       # build PR 1 of your feature
> git push && hub pull-request                     # make a PR!
> git checkout -b feature/p2-blah      # build PR 2 of your feature
> git push && hub pull-request -b feature/p1-foo   # make PR #2
> git checkout -b feature/p3-wow       # build PR 3 of your feature
> git push && hub pull-request -b feature/p2-blah  # make PR #3
# you get some feedback on PR 1
> git checkout feature/p1-foo
# address feedback, make some commits
> git push
# *for-each-stacked* lets you propagate the update to all your branches in order!
> for-each-stacked feature/p2 'git merge %P && git push'
```
