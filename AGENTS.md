# Changing tehas-standard

This repository holds the standards of the tehas system, each version in a
directory of its own. Read README.md and VERSIONS.md first.

- **Never edit a tagged version directory.** Once `vN/` or `vN.M/` is
  tagged, it is fixed. A correction, an addition, a removal or an undo is a
  new version: copy the latest directory whole to the new one, change it
  there, add its row to VERSIONS.md and its entry to CHANGELOG.md.
- **Each version directory is complete.** `coding.md` is its root and names
  the other files valid with it.
- **Rules use BCP 14 key words** (MUST, SHOULD, MAY) in capitals. Each rule
  says how it is checked and names the patterns it rests on.
- **External APIs only.** Internal APIs of any repository never go into a
  standard.
- **This repository is public.** Never write private repositories' details,
  client names, host names, tokens or session names here.
- **Style:** plain, short sentences, no em dashes. Name things by what they
  are, not how good they are.
- **Commits** say what changed and why, with no tool-generated trailers or
  footers. Every change lands through a pull request.
- **Check before you push:** `python3 -I scripts/check.py` and
  `python3 -I -m unittest discover -s tools -p '*_test.py'`.
