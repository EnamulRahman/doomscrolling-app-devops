---
topic: Git
source: tech-vault
level: Beginner
---

? What is Git?
- [ ] A cloud hosting service
- [x] A distributed version control system: every clone has the full history
- [ ] A programming language
- [ ] A CI/CD tool
> GitHub, GitLab and Bitbucket **host** Git repositories. Git itself is the tool.

? How is Git different from SVN?
- [ ] Git can't do branches
- [x] Git is distributed (full history locally, works offline); SVN is centralised (one server holds the history)
- [ ] SVN is newer
- [ ] They are the same
> Distributed also makes branching and merging much cheaper in Git.

? `git fetch` vs `git pull`?
- [x] fetch downloads new commits without changing your files; pull fetches **and** merges (or rebases) into your branch
- [ ] They're identical
- [ ] pull only works on main
- [ ] fetch deletes local changes
> Use fetch to look before you merge.

? What does `git cherry-pick <sha>` do?
- [ ] Deletes a commit
- [x] Applies one specific commit from another branch onto your current branch
- [ ] Merges a whole branch
- [ ] Picks the best branch automatically
> Useful for bringing a single bug fix across without merging everything.

? What is `HEAD` in Git?
- [ ] The first commit
- [x] A pointer to the commit you currently have checked out (usually the tip of your branch)
- [ ] The remote server
- [ ] The newest tag
> "Detached HEAD" means you checked out a commit directly, not a branch.

? When do you use `git stash`?
- [x] To set aside uncommitted changes temporarily, e.g. to switch branches
- [ ] To delete a branch
- [ ] To push to a remote
- [ ] To undo a pushed commit
> `git stash pop` restores the changes and drops the stash. `git stash apply` restores them and keeps it.

? Fork vs clone vs branch?
- [ ] They're all the same
- [x] A fork is your own server-side copy of someone's repo; a clone is a local copy of a repo; a branch is a line of work inside a repo
- [ ] A branch is a copy on GitHub
- [ ] A clone only copies the latest commit
> Open-source flow: **fork** → **clone** your fork → **branch** → PR back.

@ level: Intermediate
? You want to throw away your last 2 **local, unpushed** commits and their changes. Which command?
- [ ] `git revert HEAD~2`
- [x] `git reset --hard HEAD~2`
- [ ] `git stash`
- [ ] `git fetch --prune`
> `reset --hard` moves the branch back and discards changes. Only do it on unshared work. Use `revert` for pushed commits.

? Which command shows the differences between two commits?
- [ ] `git log a b`
- [x] `git diff <sha1> <sha2>`
- [ ] `git status a b`
- [ ] `git compare a b`
> `git diff main..feature` compares two branches.

@ level: Intermediate
? How can you undo a rebase that went wrong?
- [ ] It can't be undone
- [x] Find the pre-rebase commit in `git reflog` and `git reset --hard` to it
- [ ] `git rebase --undo`
- [ ] Delete `.git` and clone again
> The **reflog** records where HEAD has been, which is your safety net for almost any local mistake.

@ level: Intermediate
? How do you edit a commit **further back** than the last one?
- [ ] `git commit --amend`
- [x] `git rebase -i <sha>^`, mark it `edit` (or `fixup`), make the change, then continue
- [ ] `git revert`
- [ ] `git cherry-pick`
> `--amend` only edits the **latest** commit. Interactive rebase rewrites older ones. Only do it on unpushed or your own branches.
