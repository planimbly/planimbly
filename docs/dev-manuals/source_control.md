# Source control manual

## Branching model
To enable Continuous Integration in our project, we are using **Trunk Based Development** as source-control branching model. 

The rules, that we apply: 
- by default commit changes to ***master*** branch,
- don't develop on ***release*** branches, instead "cherry-pick" hotfixes from master branch to avoid painful merges,
- when needed, create short-lived feature branches, as a way to separate your code from master and submit your code for an interview

## Commit message
Our Github is connected to **Jira**. If you wish to connect your commit to specific task code on Jira be sure to submit a commit message like this
```console
"Fixed blah blah blah <YOUR JIRA TASK CODE HERE>"
```
I.E:
```console
$ git commit -a -m "Added new file: source_control.md PNBY-119"
```
Your commit is now visible from task on Jira.

## Creating feature branch

### Scenario #1:
#### *You've already developed code on local master and you wish to push it to a feature branch on github*

Commit your changes on local master:
```console
$ git commit -a -m "commit message"
```
Checkout to (and create) a new branch
```console
$ git checkout -b <new_branch_name>
```
Push to repo:
```console
$ git push -u origin <new_branch_name>
```
### Scenario #2:
#### *You want to separate your changes from local master before you start developing*


Checkout to (and create) a new branch
```console
$ git checkout -b <new_branch_name>
```
Commit your changes to the new branch:
```console
$ git commit -a -m "commit message"
```
Push to repo:
```console
$ git push -u origin <new_branch_name>
```

### Deleting branches:
  
To delete local branch use following commands:
```console
$ git checkout master
$ git branch -d <branch_name>
```
To delete remote branch use:
```console
$ git push origin --delete <branch_name>
```

## Pull-request of feature branch

Create pull-requests preferably from Github website, and assign at least one person for *Code Review*

## Pushing code to production
To push release-ready software to production, go to release branch on github and create a pull-request.
It's not preferred, but you can push changes to production directy through command line:
```console
$ git push -u origin release
```
Changes will be pushed to production environment only if Github Actions will **check success** on release.
