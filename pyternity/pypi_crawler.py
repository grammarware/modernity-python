import json
import re
import shutil
import tarfile
import zipfile
from datetime import datetime
from typing import Any, Iterable
from urllib import request

from pyternity import features
from pyternity.utils import *

# PyPI JSON API reference: https://warehouse.pypa.io/api-reference/json.html
# Ideally we should use the Simple API, but we would also like to get the upload time for each version,
# which is not yet supported (https://peps.python.org/pep-0700)

PYPI_ENDPOINT = "https://pypi.org"

MAJOR_VERSION = re.compile(r"\d+[.0]+")
MINOR_VERSION = re.compile(r"\d+\.\d+")  # Also includes MAJOR_VERSIONS


class Release:
    def __init__(self, project_name: str, version: str, files: list[dict[str, Any]]):
        sdist_file = next(file for file in files if file['packagetype'] == "sdist")

        self.project_name = project_name.lower()
        self.version = version
        self.filename: str = sdist_file['filename']
        self.requires_python: str = sdist_file['requires_python']
        self.upload_date = datetime.fromisoformat(sdist_file['upload_time']).date()
        self.url: str = sdist_file['url']

    def download_files(self):
        out_dir = EXAMPLES_DIR / self.project_name / self.version
        if out_dir.exists():
            if not Config.redownload_examples:
                return out_dir

            shutil.rmtree(out_dir)

        tmp_file = TMP_DIR / self.filename
        request.urlretrieve(self.url, tmp_file)

        # TODO optimize: We only have to keep python files
        if tarfile.is_tarfile(tmp_file):
            with tarfile.open(tmp_file) as tar:
                tar.extractall(out_dir)
        else:
            with zipfile.ZipFile(tmp_file) as tmp_zip:
                tmp_zip.extractall(out_dir)

        tmp_file.unlink()

        return out_dir

    @property
    def is_major(self) -> bool:
        return bool(MAJOR_VERSION.fullmatch(self.version))

    @property
    def is_minor(self) -> bool:
        return bool(MINOR_VERSION.fullmatch(self.version))

    def get_features(self) -> Features:
        result_path = RESULTS_DIR / self.project_name / (self.version + '.json')
        if result_path.exists() and not Config.recalculate_examples:
            with result_path.open() as result_file:
                try:
                    return json.load(result_file)
                except json.decoder.JSONDecodeError:
                    # Recalculate if there is an error in the file
                    pass

        download_path = self.download_files()
        new_features = features.get_features(download_path)

        result_path.parent.mkdir(exist_ok=True)
        with result_path.open('w+') as result_file:
            json.dump(new_features, result_file)

        return new_features


class PyPIProject:
    def __init__(self, project_name: str):
        with request.urlopen(f"{PYPI_ENDPOINT}/pypi/{project_name}/json") as f:
            meta_data = json.load(f)

            self.name = meta_data['info']['name']
            self.releases = []

            for version, files in meta_data['releases'].items():
                try:
                    self.releases.append(Release(self.name, version, files))
                except StopIteration:
                    # Not all releases have a tar file, skip those
                    continue


def get_most_popular_projects() -> Iterable[str]:
    """
    See: https://pypi.org/stats, refreshes each 24 hours
    :return: 100 most Popular PyPI projects
    """
    req = request.Request(f"{PYPI_ENDPOINT}/stats", headers={"accept": "application/json"})
    with request.urlopen(req) as f:
        res = json.load(f)
        return res["top_packages"].keys()
