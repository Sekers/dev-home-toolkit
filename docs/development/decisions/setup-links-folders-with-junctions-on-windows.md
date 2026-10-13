# Setup links folders with junctions on Windows

**Decision:** on Windows, setup makes every folder link as a directory junction; on macOS and
Linux, which have no junctions, as a symbolic link. Python makes a junction with
`_winapi.CreateJunction`, part of Python on Windows though not documented for general use;
Python's own tests make junctions with it, and it starts no process.

**Why:** a junction needs no admin rights and no Developer Mode, so every Windows PC gets the
same kind of link, with no branch to write, test, or explain. The Python link was already
always a junction. On macOS and Linux, any user can make a symbolic link, so it's the same
choice there: the one kind of link that needs no special rights. Setup checks only where a link
points, so a symbolic link made by an older setup keeps working.

**Options set aside:**

- A symbolic link where Developer Mode is on, and a junction otherwise, as `setup.ps1` did:
  links that differ between PCs, for no gain.
- Making the junction with `cmd /c mklink /J`: a process each time, and cmd parses its
  arguments again.

**Look again if:** someone keeps dev-home on a network share, which a junction can't point to.
