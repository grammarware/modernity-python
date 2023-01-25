import json
import re
import shutil
import tarfile
import zipfile
from traceback import TracebackException
from typing import Any, Iterable, Self
from urllib import request

from pyternity import features
from pyternity.utils import *

# PyPI JSON API reference: https://warehouse.pypa.io/api-reference/json.html
# Ideally we should use the Simple API, but we would also like to get the upload time for each version,
# which is not yet supported (https://peps.python.org/pep-0700)

PYPI_ENDPOINT = "https://pypi.org"

# Currently no support for version schemes like 20171021.0 (e.g. home-assistant-frontend)
MAJOR_VERSION = re.compile(r"\d{1,7}(\.0)*")
MINOR_VERSION = re.compile(r"\d{1,7}\.\d+(\.0)*")  # Also includes MAJOR_VERSIONS


class Release:
    def __init__(self, project_name: str, version: str, files: list[dict[str, Any]]):
        sdist_file = next(file for file in files if file['packagetype'] == "sdist")

        self.project_name = project_name.lower()
        self.version = version
        self.filename: str = sdist_file['filename']
        self.requires_python: str = sdist_file['requires_python'] or ''
        self.upload_date = datetime.fromisoformat(sdist_file['upload_time'])
        self.url: str = sdist_file['url']

    @property
    def is_major(self) -> bool:
        return bool(MAJOR_VERSION.fullmatch(self.version))

    @property
    def is_minor(self) -> bool:
        return bool(MINOR_VERSION.fullmatch(self.version))

    def __lt__(self, other: Self):
        return self.upload_date < other.upload_date

    def download_files(self):
        out_dir = EXAMPLES_DIR / self.project_name / self.version
        if out_dir.exists():
            if not Config.redownload_examples:
                return out_dir

            shutil.rmtree(out_dir)

        logger.info(f"Downloading {self.project_name} {self.version} ...")
        tmp_file = TMP_DIR / self.filename
        request.urlretrieve(self.url, tmp_file)

        # Optimisation: Only keep the Python files
        if tarfile.is_tarfile(tmp_file):
            with tarfile.open(tmp_file) as tar:
                tar.extractall(out_dir, (m for m in tar.getmembers() if is_python_file(m.name)))
        else:
            with zipfile.ZipFile(tmp_file) as tmp_zip:
                tmp_zip.extractall(out_dir, filter(is_python_file, tmp_zip.namelist()))

        tmp_file.unlink()

        return out_dir

    def get_features(self) -> dict[str, dict[str, int]]:
        """
        If features were already calculated before, return that.
        Else download the source of this release, calculate the features and save this result to file.
        :return: Detected Features belonging to this release
        """
        result_path = RESULTS_DIR / self.project_name / (self.version + '.json')
        if result_path.exists() and not Config.recalculate_examples:
            with result_path.open() as result_file:
                try:
                    return json.load(result_file)
                except json.decoder.JSONDecodeError:
                    # Recalculate if there is an error in the file
                    # Should only occur when you prematurely exit the program
                    pass

        download_path = self.download_files()

        try:
            # Sort features such that it is easier to debug when viewing the files
            logger.info(f"Getting features from {self.project_name} {self.version} ...")
            new_sorted_features = sort_features(features.get_features(download_path))

        except (RecursionError, TypeError) as e:
            # Skip releases that give errors, but do save empty {} to file,
            # such that we skip it next time we want to plot using the already calculated data
            new_sorted_features = {}
            logger.error(f"Error occurred for {self.project_name} {self.version}:\n" +
                         ''.join(TracebackException.from_exception(e).format()))

        result_path.parent.mkdir(exist_ok=True)
        with result_path.open('w+') as result_file:
            json.dump(new_sorted_features, result_file, indent=2)

        return new_sorted_features


class PyPIProject:
    def __init__(self, project_name: str):
        with request.urlopen(f"{PYPI_ENDPOINT}/pypi/{project_name}/json") as f:
            meta_data = json.load(f)

            self.name = meta_data['info']['name']

            releases = []
            for version, files in meta_data['releases'].items():
                try:
                    releases.append(Release(self.name, version, files))
                except StopIteration:
                    # Not all releases have a sdist file, skip those
                    continue

            self.releases = sorted(releases)


def get_100_biggest_projects() -> Iterable[str]:
    """
    See: https://pypi.org/stats, refreshes each 24 hours
    :return: 100 biggest PyPI projects
    """
    req = request.Request(f"{PYPI_ENDPOINT}/stats", headers={'accept': 'application/json'})
    with request.urlopen(req) as f:
        res = json.load(f)
        return res['top_packages'].keys()


def get_most_popular_projects(n: int) -> Iterable[str]:
    """
    See: https://github.com/hugovk/top-pypi-packages, updates monthly
    :param n: Amount of project to return.
    :return: The n most popular projects (of previous) on PyPI.
    """
    url = 'https://hugovk.github.io/top-pypi-packages/top-pypi-packages-30-days.min.json'
    with request.urlopen(request.Request(url)) as f:
        res = json.load(f)
        return (row['project'] for row in res['rows'][:n])
