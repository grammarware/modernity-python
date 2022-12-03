import json
import re
import shutil
import tarfile
import urllib
from dataclasses import dataclass
from functools import cached_property
from itertools import count
from urllib import request
from typing import Iterable

from pyternity.utils import *

GITHUB_API_URL = "https://api.github.com"
TAGS_PER_PAGE = 100  # https://docs.github.com/en/rest/repos/repos#list-repository-tags

IS_MAJOR_VERSION = re.compile(r"\d+[.0]+")


# Not all projects use GitHub's releases (e.g. Django), so use Tags instead
@dataclass
class Tag:
    name: str
    zipball_url: str
    tarball_url: str
    commit_url: str

    @cached_property
    def commit_date(self) -> str:
        commit = make_json_request(self.commit_url)
        return commit["commit"]["author"]["date"]

    @property
    def is_major_version(self) -> bool:
        return bool(IS_MAJOR_VERSION.fullmatch(self.name))

    def download_tarball(self, project_name: str, clean_download=True):
        out_dir = EXAMPLES_DIR / project_name / self.name
        if out_dir.exists():
            if not clean_download:
                return
            shutil.rmtree(out_dir)

        tmp_file = TMP_DIR / f"{project_name}-{self.name}.tar.gz"
        urllib.request.urlretrieve(self.tarball_url, tmp_file)

        with tarfile.open(tmp_file, "r") as tar:
            tar.extractall(out_dir)

        tmp_file.unlink()


@dataclass
class GitHubProject:
    tags: list[Tag]


def make_json_request(url: str):
    with request.urlopen(url) as f:
        return json.loads(f.read())


def get_all_tags(owner: str, repo: str) -> Iterable[Tag]:
    for page in count(1):
        url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/tags?per_page={TAGS_PER_PAGE}&page={page}"
        new_tags = make_json_request(url)

        for tag in new_tags:
            yield Tag(tag["name"], tag["zipball_url"], tag["tarball_url"], tag["commit"]["url"])

        # Continue until no new more tags can be found
        if len(new_tags) < TAGS_PER_PAGE:
            break
