#!/usr/bin/env python
import json
import subprocess
from dataclasses import dataclass
from functools import partial
from typing import Iterable, Mapping

from dacite import from_dict
from packaging.version import Version
from requests import Session

HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def run(cmd: list[str]) -> str:
    return subprocess.run(cmd, capture_output=True, text=True).stdout.strip()


def nix_prefetch_sha256(version):
    url = (
        f"https://github.com/kubernetes/kubernetes/archive/refs/tags/v{version}.tar.gz"
    )
    hash = run(["nix-prefetch-url", "--type", "sha256", "--unpack", url])
    return run(["nix", "hash", "to-sri", f"sha256:{hash}"])


@dataclass
class VersionArgs:
    version: Version
    hash: str

    def __post_init__(self):
        if isinstance(self.version, str):
            self.version = Version(self.version)

    def as_dict(self):
        return {
            "version": str(self.version),
            "hash": self.hash,
        }


@dataclass
class ResponseRelease:
    tag_name: str


def load_versions() -> Mapping[str, VersionArgs]:
    with open("./versions.json", "r") as f:
        versions = json.load(f)
    return {k: VersionArgs(**v) for k, v in versions.items()}


def dump_versions(versions: Mapping[str, VersionArgs]):
    with open("./versions.json", "w") as f:
        json.dump({k: v.as_dict() for k, v in versions.items()}, f, indent=2)


def fetch_available_versions(http: Session) -> Iterable[Version]:
    url = "https://api.github.com/repos/kubernetes/kubernetes/releases"
    response = http.get(url, params={"per_page": 100})
    response.raise_for_status()
    releases = map(partial(from_dict, ResponseRelease), response.json())
    return map(lambda release: Version(release.tag_name), releases)


def filter_matching(version: Version, versions: list[Version]) -> Iterable[Version]:
    def match(v: Version) -> bool:
        return all(
            [
                not v.is_prerelease,
                not v.is_postrelease,
                not v.is_devrelease,
                v.major == version.major,
                v.minor == version.minor,
            ]
        )

    return filter(match, versions)


def update(version: VersionArgs, available_versions: list[Version]) -> VersionArgs:
    matching_versions = filter_matching(version.version, available_versions)
    latest_bugfix = max(matching_versions)
    if latest_bugfix <= version.version:
        return version
    print(version.version, "->", latest_bugfix)
    return VersionArgs(
        version=latest_bugfix,
        hash=nix_prefetch_sha256(latest_bugfix),
    )


def update_all(
    versions: Mapping[str, VersionArgs], available_versions: list[Version]
) -> Mapping[str, VersionArgs]:
    return {name: update(v, available_versions) for name, v in versions.items()}


def main():
    versions = load_versions()
    with Session() as http:
        http.headers.update(HEADERS)
        available_versions = list(fetch_available_versions(http))
    updated_versions = update_all(versions, available_versions)
    dump_versions(updated_versions)


if __name__ == "__main__":
    main()
