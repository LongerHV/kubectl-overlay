#!/usr/bin/env python
import json
import logging
import os
import subprocess
from dataclasses import dataclass
from functools import partial
from itertools import groupby
from typing import Iterable, Mapping

from dacite import from_dict
from packaging.version import Version
from requests import Session

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
} | ({"Authorization": f"Bearer {GITHUB_TOKEN}"} if GITHUB_TOKEN else {})


def run(cmd: list[str]) -> str:
    return subprocess.run(cmd, capture_output=True, text=True).stdout.strip()


def nix_prefetch_sha256(version: Version) -> str:
    logging.info(f"Prefetching sources for kubectl {version}")
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

    def as_dict(self) -> dict[str, str]:
        return {
            "version": str(self.version),
            "hash": self.hash,
        }


@dataclass
class ResponseRelease:
    tag_name: str


def dump_versions(versions: Mapping[str, VersionArgs]):
    with open("./versions.json", "w") as f:
        json.dump({k: v.as_dict() for k, v in versions.items()}, f, indent=2)


def fetch_available_versions(http: Session) -> Iterable[Version]:
    url = "https://api.github.com/repos/kubernetes/kubernetes/releases"
    response = http.get(url, params={"per_page": 100})
    response.raise_for_status()
    releases = map(partial(from_dict, ResponseRelease), response.json())
    return map(lambda release: Version(release.tag_name), releases)


def filter_versions(versions: Iterable[Version]) -> Iterable[Version]:
    return filter(
        lambda v: not (v.is_devrelease or v.is_postrelease or v.is_prerelease),
        versions,
    )


def get_latest_bugfixes(versions: Iterable[Version]) -> Iterable[Version]:
    grouped_versions = groupby(
        sorted(versions, reverse=True),
        key=lambda v: (v.major, v.minor),
    )
    return map(lambda x: max(x[1]), grouped_versions)


def get_final_versions(versions: Iterable[Version]) -> dict[str, VersionArgs]:
    final_versions = {
        f"kubectl_{v.major}_{v.minor}": VersionArgs(v, nix_prefetch_sha256(v))
        for v in get_latest_bugfixes(versions)
    }
    latest = {"kubectl_latest": max(final_versions.values(), key=lambda v: v.version)}
    return latest | final_versions


def log_versions(versions: Mapping[str, VersionArgs]):
    for package, version in versions.items():
        logging.info(f"{package} -> {version.version} -> {version.hash}")


def main():
    logging.basicConfig(level=logging.INFO)
    with Session() as http:
        http.headers.update(HEADERS)
        available_versions = filter_versions(fetch_available_versions(http))
    final_versions = get_final_versions(available_versions)
    log_versions(final_versions)
    dump_versions(final_versions)


if __name__ == "__main__":
    main()
