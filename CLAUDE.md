# ApolloSoftware - notes for Claude

The public software library for the Apollo V4. ApolloUpdate installs from
it, and apolloupdate.com is built from it. README.md has the full layout
rules (Category / Name / Version / SYS-root, the Info file, cores and ROMs,
startup-script fragments). This file is about how to work in the
repository.

This repository is **public**. Never put any of these in it:
- owners, contributors or source locations (they belong in the team's
  private ApolloSoftware-Sources);
- member (AVL) content;
- tokens or keys;
- an `ApolloUpdate.conf`.

## The workflow does the generated files

On every push to main, `.github/workflows/releases.yml` runs
`.github/scripts/releases.py`:
- **checks** the layout; any error fails the run;
- **rewrites** the table in README.md and `ApolloSoftware.index`, and
  commits them as github-actions[bot];
- **publishes** apolloupdate.com through GitHub Pages: web pages,
  downloads, `ApolloSoftware.tree`, ApolloUpdate-Offline.zip;
- **notifies** ApolloSoftware-Sources.

Consequences:
- **Never edit by hand** the README table (between the `releases:` markers)
  or `ApolloSoftware.index`.
- **Pull before you push.** The bot, and Manager merges by other team
  members, often push in between, so use `git pull --rebase --autostash`.
- **Runs queue in one group.** A newer push replaces a pending run, which
  then shows as *cancelled*. That's harmless: the next run contains your
  commit. Find runs by the **full** commit ID, because
  `gh run list --commit <short>` finds nothing.

## Checking locally

A working folder collects untracked clutter (`.DS_Store`, empty release
folders) that the workflow never sees. Check a clean export instead of the
working folder:

```
D=$(mktemp -d); git archive HEAD | tar -x -C $D
cp .github/scripts/*.py $D/.github/scripts/        # plus any changed files
(cd $D && python3 .github/scripts/releases.py --check --readme README.md --index ApolloSoftware.index)
```

Add `--site <dir>` to build the web pages too.

## Rules

- Keep the scripts identical in ApolloSoftware-AVL. `releases.py`,
  `webpage.py`, `romlink.py` and `prcheck.py` are copies; change both
  repositories together.
- Some code has twins elsewhere; change them together:
  - `releases.py` `version_cmp` = ApolloUpdate `Repo_VersionCmp`;
  - `romlink.py` = the Manager's JavaScript ROM builder;
  - the limits and OS list = the Manager's `app.js`.
- `.gitattributes` is `* -text`: files are stored byte for byte. Never
  convert line endings.
- No migration or compatibility code for older layouts. The project is not
  in production yet: change a layout everywhere at once.
- Entries are normally added through the ApolloSoftware-Manager
  (apolloupdate.com/manager). It opens pull requests, and Maintainers merge
  them.
- Releasing a new ApolloUpdate is done from the ApolloUpdate repository
  (`make release`), which commits `Tools/ApolloUpdate/<version>` here.

## Network share pitfall

Work in a local clone. If a checkout on a network share (the old NAS
copies) says "unable to write new index file":

```
mv .git/index .git/index.stuck-<date>
git reset -q
```

Then add and commit as usual.
