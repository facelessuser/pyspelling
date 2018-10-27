"""Meta related things."""
from __future__ import unicode_literals
from collections import namedtuple

REL_MAP = {
    ".dev": "",
    ".dev-alpha": "a",
    ".dev-beta": "b",
    ".dev-candidate": "rc",
    "alpha": "a",
    "beta": "b",
    "candidate": "rc",
    "final": ""
}

DEV_STATUS = {
    ".dev": "2 - Pre-Alpha",
    ".dev-alpha": "2 - Pre-Alpha",
    ".dev-beta": "2 - Pre-Alpha",
    ".dev-candidate": "2 - Pre-Alpha",
    "alpha": "3 - Alpha",
    "beta": "4 - Beta",
    "candidate": "4 - Beta",
    "final": "5 - Production/Stable"
}


class Pep440Version(namedtuple("Pep440Version", ["major", "minor", "micro", "release", "pre", "post", "dev"])):
    """
    Get the version (PEP 440).

    Some additional rules are imposed on how we create our versions.

    Version structure which is sorted for comparisons `v1 > v2` etc.
      (major, minor, micro, release type, pre-release build, post-release build)
    Release types are named is such a way they are comparable with ease.

    - You must specify a release type as either `final`, `alpha`, `beta`, or `candidate`.
    - To define a development release, you can use either `.dev`, `.dev-alpha`, `.dev-beta`, or `.dev-candidate`.
      The dot is used to ensure all development specifiers are sorted before `alpha`.
      You can specify a `dev` number for development builds, but do not have to as implicit development releases
      are allowed.
    - You must specify a `pre` value greater than zero if using a prerelease as this project (not PEP 440) does not
      allow implicit prereleases.
    - You can optionally set `post` to value greater zero to make the build a post release. While post releases
      are technically allowed in prereleases, it is strongly discouraged, so we are rejecting them. It should be
      noted that we do not allow `post0` even though PEP 440 does not restrict this. This project specifically
      does not allow implicit post releases.
    - It should be noted that we do not support epochs `1!` or local versions `+some-custom.version-1`.

    Acceptable version releases:

    ```
    Pep440Version(1, 0, 0, "final")                    1.0
    Pep440Version(1, 2, 0, "final")                    1.2
    Pep440Version(1, 2, 3, "final")                    1.2.3
    Pep440Version(1, 2, 0, ".dev-alpha", pre=4)        1.2a4
    Pep440Version(1, 2, 0, ".dev-beta", pre=4)         1.2b4
    Pep440Version(1, 2, 0, ".dev-candidate", pre=4)    1.2rc4
    Pep440Version(1, 2, 0, "final", post=1)            1.2.post1
    Pep440Version(1, 2, 3, ".dev")                     1.2.3.dev0
    Pep440Version(1, 2, 3, ".dev", dev=1)              1.2.3.dev1
    ```

    """

    def __new__(cls, major, minor, micro, release, pre=0, post=0, dev=0):  # pragma: no cover
        """Validate version info."""

        # Ensure all parts are positive integers.
        for value in (major, minor, micro, pre, post):
            if not (isinstance(value, int) and value >= 0):
                raise ValueError("All version parts except 'release' should be integers.")

        if release not in REL_MAP:
            raise ValueError("'{}' is not a valid release type.".format(release))

        # Ensure valid pre-release (we do not allow implicit pre-releases).
        if ".dev-candidate" < release < "final":
            if pre == 0:
                raise ValueError("Implicit pre-releases not allowed.")
            elif dev:
                raise ValueError("Version is not a development release.")
            elif post:
                raise ValueError("Post-releases are not allowed with pre-releases.")

        # Ensure valid development or development/pre release
        elif release < "alpha":
            if release > ".dev" and pre == 0:
                raise ValueError("Implicit pre-release not allowed.")
            elif post:
                raise ValueError("Post-releases are not allowed with pre-releases.")

        # Ensure a valid normal release
        else:
            if pre:
                raise ValueError("Version is not a pre-release.")
            elif dev:
                raise ValueError("Version is not a development release.")

        return super(Pep440Version, cls).__new__(cls, major, minor, micro, release, pre, post, dev)

    def _is_pre(self):
        """Is prerelease."""

        return self.pre > 0

    def _is_dev(self):
        """Is development."""

        return bool(self.release < "alpha")

    def _is_post(self):
        """Is post."""

        return self.post > 0

    def _get_dev_status(self):  # pragma: no cover
        """Get development status string."""

        return DEV_STATUS[self.release]

    def _get_canonical(self):  # pragma: no cover
        """Get the canonical output string."""

        # Assemble major, minor, micro version and append `pre`, `post`, or `dev` if needed..
        if self.micro == 0:
            ver = "{}.{}".format(self.major, self.minor)
        else:
            ver = "{}.{}.{}".format(self.major, self.minor, self.micro)
        if self._is_pre():
            ver += '{}{}'.format(REL_MAP[self.release], self.pre)
        if self._is_post():
            ver += ".post{}".format(self.post)
        if self._is_dev():
            ver += ".dev{}".format(self.dev)

        return ver


__version_info__ = Pep440Version(1, 0, 0, "beta", 2)
__version__ = __version_info__._get_canonical()


if __name__ == "__main__":  # pragma: no cover
    assert Pep440Version(1, 0, 0, "final")._get_canonical() == "1.0"
    assert Pep440Version(1, 2, 0, "final")._get_canonical() == "1.2"
    assert Pep440Version(1, 2, 3, "final")._get_canonical() == "1.2.3"
    assert Pep440Version(1, 2, 0, "alpha", pre=4)._get_canonical() == "1.2a4"
    assert Pep440Version(1, 2, 0, "beta", pre=4)._get_canonical() == "1.2b4"
    assert Pep440Version(1, 2, 0, "candidate", pre=4)._get_canonical() == "1.2rc4"
    assert Pep440Version(1, 2, 0, "final", post=1)._get_canonical() == "1.2.post1"
    assert Pep440Version(1, 2, 3, ".dev-alpha", pre=1)._get_canonical() == "1.2.3a1.dev0"
    assert Pep440Version(1, 2, 3, ".dev")._get_canonical() == "1.2.3.dev0"
    assert Pep440Version(1, 2, 3, ".dev", dev=1)._get_canonical() == "1.2.3.dev1"

    assert Pep440Version(1, 0, 0, "final") < Pep440Version(1, 2, 0, "final")
    assert Pep440Version(1, 2, 0, "alpha", pre=4) < Pep440Version(1, 2, 0, "final")
    assert Pep440Version(1, 2, 0, "final") < Pep440Version(1, 2, 0, "final", post=1)
    assert Pep440Version(1, 2, 3, ".dev-beta", pre=2) < Pep440Version(1, 2, 3, "beta", pre=2)
    assert Pep440Version(1, 2, 3, ".dev") < Pep440Version(1, 2, 3, ".dev-beta", pre=2)
    assert Pep440Version(1, 2, 3, ".dev") < Pep440Version(1, 2, 3, ".dev", dev=1)
