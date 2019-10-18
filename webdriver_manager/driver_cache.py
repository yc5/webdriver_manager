import datetime
import glob
import json
import os

from webdriver_manager.archive import extract_zip, extract_tar_file
from webdriver_manager.utils import write_file, get_filename_from_response, console, get_date_diff


class DriverCache(object):

    def __init__(self, root_dir=None):
        if root_dir is None:
            self._root_dir = os.path.join(os.path.expanduser("~"), ".wdm")
        self._drivers_root = "drivers"
        self._drivers_json_path = os.path.join(self._root_dir, "drivers.json")
        self._date_format = "%d/%m/%Y"

    def create_cache_dir_for_driver(self, driver_path):
        path = os.path.join(self._root_dir, driver_path)

        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        return os.path.exists(path)

    def find_file_if_exists(self, os_type, name, version):
        console("Looking for driver {} {} {} in cache ".format(os_type, name, version))
        if len(name) == 0 or len(version) == 0:
            return None

        paths = [f for f in glob.glob(os.path.join(self._root_dir, self._drivers_root, name, version, os_type) + "/**",
                                      recursive=True)]

        if len(paths) == 0:
            return None

        for path in paths:
            if os.path.isfile(path) and path.endswith(name):
                console("File found by path [{}]".format(path))
                return path
        return None

    def save_driver_to_cache(self, response, driver_name, version, os_type):
        driver_path = os.path.join(self._root_dir, self._drivers_root, driver_name, version, os_type)
        filename = get_filename_from_response(response, driver_name)
        self.create_cache_dir_for_driver(driver_path)
        file_path = os.path.join(driver_path, filename)
        write_file(response.content, file_path)
        files = self.__unpack(file_path)
        return os.path.join(driver_path, files[0])

    def save_latest_driver_version_number_to_cache(self, name, version, date=None):
        if date is None:
            date = datetime.date.today()

        metadata = self.read_metadata()
        new = {name: {"latest_version": version, "timestamp": date.strftime(self._date_format)}}
        metadata.update(new)
        with open(self._drivers_json_path, 'w+') as outfile:
            json.dump(metadata, outfile, indent=4)

    def is_valid_cache(self, driver_name):
        metadata = self.read_metadata()
        if driver_name in metadata:
            driver_data = metadata[driver_name]
            dates_diff = get_date_diff(driver_data['timestamp'], datetime.date.today(), self._date_format)
            return dates_diff < 1

        return False

    def get_latest_cached_driver_version(self, driver_name):
        if not self.is_valid_cache(driver_name):
            return None

        return self.read_metadata()[driver_name]["latest_version"]

    def read_metadata(self):
        if os.path.exists(self._drivers_json_path):
            with open(self._drivers_json_path, 'r') as outfile:
                return json.load(outfile)
        return {}

    def __unpack(self, path, to_directory=None):
        console("Unpack archive {}".format(path))
        if not to_directory:
            to_directory = os.path.dirname(path)
        if path.endswith(".zip"):
            return extract_zip(path, to_directory)
        else:
            file_list = extract_tar_file(path, to_directory)
            return [x.name for x in file_list]