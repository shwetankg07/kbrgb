# Releasing kbrgb

Every registry keys off a GitHub release tag, so cut that first and fan out
from it. Run these from a clean checkout of `main`.

**Currently published: the AUR and PyPI.** Section 5 (COPR) is written and the
recipe should work, but nothing has been uploaded there and the spec has never
been built. `packaging/rpm/kbrgb.spec` is kept because it costs nothing to
carry and means Fedora is one build away if a user ever asks for it.

## 0. One time setup

**AUR.** Make an account at <https://aur.archlinux.org>, add your SSH public
key under My Account, then:

```
Host aur.archlinux.org
  User aur
  IdentityFile ~/.ssh/id_ed25519
```

in `~/.ssh/config`. Clone the two package repos somewhere outside this one:

```bash
git clone ssh://aur@aur.archlinux.org/kbrgb.git      ~/aur/kbrgb
git clone ssh://aur@aur.archlinux.org/kbrgb-git.git  ~/aur/kbrgb-git
```

Both will be empty on first clone. That is normal: pushing creates them.

**PyPI.** Account at <https://pypi.org>, then an API token scoped to the
`kbrgb` project (after the first upload) or to the whole account (before it).
Put it in `~/.pypirc` or export `TWINE_PASSWORD`.

**COPR.** Log in at <https://copr.fedorainfracloud.org> with a Fedora Account
System account, create a project named `kbrgb`, and enable the Fedora releases
you care about plus `x86_64`. Optionally `pip install copr-cli` and drop the
API token from the site into `~/.config/copr`.

## 1. Bump the version

Four places, all of which must agree:

- `kbrgb.py`: `__version__`
- `packaging/aur/PKGBUILD`: `pkgver` (and reset `pkgrel=1`)
- `packaging/rpm/kbrgb.spec`: `Version` (and reset `Release`), plus a new
  `%changelog` entry
- `packaging/aur/PKGBUILD.git`: nothing. It derives its version from git.

## 2. Tag and release

```bash
git commit -am "release: 0.X.0"
git tag -a v0.X.0 -m "kbrgb 0.X.0"
git push origin main
git push origin v0.X.0
gh release create v0.X.0 --generate-notes
```

## 3. AUR

The release tarball has to exist before this, because `updpkgsums` downloads
it to compute the checksum.

```bash
cd ~/aur/kbrgb
cp ~/kbrgb/packaging/aur/PKGBUILD ~/kbrgb/packaging/aur/kbrgb.install .
updpkgsums                          # fills sha256sums from the live tarball
makepkg -f                          # must succeed before you push
namcap PKGBUILD kbrgb-*.pkg.tar.zst # should be quiet
makepkg --printsrcinfo > .SRCINFO   # required, AUR rejects pushes without it
git add PKGBUILD kbrgb.install .SRCINFO
git commit -m "kbrgb 0.X.0"
git push
```

Then the git package, which only needs redoing when the PKGBUILD itself
changes, not on every release:

```bash
cd ~/aur/kbrgb-git
cp ~/kbrgb/packaging/aur/PKGBUILD.git PKGBUILD
cp ~/kbrgb/packaging/aur/kbrgb.install .
makepkg -f                          # this rewrites pkgver from git describe
makepkg --printsrcinfo > .SRCINFO
git add PKGBUILD kbrgb.install .SRCINFO
git commit -m "kbrgb-git 0.X.0"
git push
```

`updpkgsums` and `namcap` come from `pacman -S pacman-contrib namcap`.

## 4. PyPI

```bash
cd ~/kbrgb
rm -rf dist
python -m build
python -m twine check dist/*
python -m twine upload dist/*
```

Sanity check in a throwaway environment:

```bash
pipx install kbrgb && kbrgb --version && sudo kbrgb install-udev
```

## 5. COPR

Web UI: your project, New Build, method **SCM**.

- Clone URL: `https://github.com/shwetankg07/kbrgb`
- Committish: `v0.X.0`
- Spec file: `packaging/rpm/kbrgb.spec`
- Source build method: `rpkg`

Or from the terminal:

```bash
copr-cli build kbrgb \
  --scm-url https://github.com/shwetankg07/kbrgb \
  --commit v0.X.0 \
  --spec packaging/rpm/kbrgb.spec
```

Users then get it with:

```bash
sudo dnf copr enable shwetankg07/kbrgb
sudo dnf install kbrgb
```

## Notes

The udev rule text lives in exactly one place, `UDEV_RULE` in `kbrgb.py`. The
PKGBUILD and the spec both generate their packaged copy with
`kbrgb.py install-udev --print` at build time, and `pipx` users get the same
text from `sudo kbrgb install-udev`. If you edit the rule, edit it there and
everything else follows.
