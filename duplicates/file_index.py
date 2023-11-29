import os
import hashlib
import logging
import json
import tempfile

class FileIndex:
    #def __init__(self, index_file="file_index.json",directories_file="scanned_dirs.json", force_update=False, deep_scan=False):
        #self.index_file = index_file
        #self.directories_file = directories_file

    def __init__(self, index_file: str="", directories_file: str="", force_update: bool=False, deep_scan: bool=False):

        # Create a temporary file for the index of directory1
        with tempfile.NamedTemporaryFile(suffix="_index.json", mode="w", delete=False) as temp_file:
            json.dump({}, temp_file)
            self.temp_index_file = temp_file.name
        with tempfile.NamedTemporaryFile(suffix="_dirs.json", mode="w", delete=False) as temp_file:
            json.dump([], temp_file)
            self.temp_dirs_file = temp_file.name

	# set json files
        self.index_file = index_file if index_file else self.temp_index_file
        self.directories_file = directories_file if directories_file else self.temp_dirs_file

        # load previous data
        self.scanned_directories = self.load_scanned_directories()
        self.file_index = self.load_file_index()

        # Configure logging
        logging.basicConfig(filename='file_index.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

        if force_update:
            self.update(deep_scan)

    def __del__(self):
        """Destructor: Save the file index when the class is destroyed."""
        self.save_file_index()
        self.save_scanned_directories()
        if os.path.exists(self.temp_index_file):
            os.remove(self.temp_index_file)
        if os.path.exists(self.temp_dirs_file):
            os.remove(self.temp_dirs_file)

    def load_file_index(self):
        """Load the file index from the JSON file."""
        if os.path.exists(self.index_file):
            with open(self.index_file, 'r') as f:
                return json.load(f)
        else:
            return {}

    def save_file_index(self):
        """Save the file index to the JSON file."""
        with open(self.index_file, 'w') as f:
            json.dump(self.file_index, f)

    def load_scanned_directories(self):
        """Load the scanned directories from a JSON file."""
        if os.path.exists(self.directories_file):
            with open(self.directories_file, 'r') as f:
                return json.load(f)
        else:
            return []

    def save_scanned_directories(self):
        """Save the scanned directories to a JSON file."""
        with open(self.directories_file, 'w') as f:
            json.dump(self.scanned_directories, f)

    def calculate_md5(self, file_path, block_size=65536):
        """Calculate the MD5 hash of a file."""
        md5_hash = hashlib.md5()
        with open(file_path, "rb") as f:
            for block in iter(lambda: f.read(block_size), b""):
                md5_hash.update(block)
        return md5_hash.hexdigest()

    def get_hash(self, file_path):
        """Get the MD5 hash of a file from the index."""
        return self.file_index.get(file_path)

    def set_hash(self, file_path):
        """Calculate and set the MD5 hash of a file in the index."""
        md5_checksum = self.calculate_md5(file_path)
        self.file_index[file_path] = md5_checksum

    def compare_hashes(self, file_path, hash_to_compare):
        """Compare an MD5 hash from the index to a given hash."""
        stored_hash = self.get_hash(file_path)
        return stored_hash == hash_to_compare

    def compare_hash_to_dictionary(self, hash_to_compare):
        """Scan the file index for any matching hash and return the filename(s)."""
        matching_files = []
        for file_path, stored_hash in self.file_index.items():
            if stored_hash == hash_to_compare:
                matching_files.append(file_path)
        return matching_files

    def create_file_index(self, directory):
        """Create or update the file index with files from the directory."""
        self.scanned_directories.append(directory)  # Track the scanned directory
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.abspath(os.path.join(root, file))
                if file_path not in self.file_index:
                    md5_checksum = self.calculate_md5(file_path)
                    self.file_index[file_path] = md5_checksum

    def update(self, deep_scan: bool = False):
        """
        Update the file index by performing the following steps:

        Args:
            deep_scan (bool, optional): If True, recalculate MD5 values for all existing files. Default is False.

        Returns:
            None
        """
        logging.info("Step 1: Check and remove directories that no longer exist")
        self.scanned_directories = [d for d in self.scanned_directories if os.path.exists(d)]

        logging.info("Step 2: Scan all files in file_index and remove non-existent files")
        self.file_index = {f:h for f,h in self.file_index.items() if os.path.exists(f)}

        logging.info("Step 3: Scan all existing directories for new files and add their hashes")
        for directory in self.scanned_directories:
            for root, _, files in os.walk(directory):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    if file_path not in self.file_index and os.path.isfile(file_path):
                        self.set_hash(file_path)

        if deep_scan:
            logging.info("Step 4: Recalculate MD5 values for existing files")
            for file_path in self.file_index.keys():
                self.set_hash(file_path)

        # Save the updated list of scanned directories and file index
        self.save_scanned_directories()
        self.save_file_index()

    def add(self, file_index: 'FileIndex'):
        """
        Add the scanned directories and file index from another FileIndex object to this FileIndex.

        Args:
            file_index (FileIndex): The FileIndex object to absorb.

        Returns:
            None
        """
        # Merge scanned directories (no duplicates)
        self.scanned_directories.extend([d for d in file_index.scanned_directories if d not in self.scanned_directories])

        # Merge file index (overwrite if file already exists)
        self.file_index.update(file_index.file_index)

        # Save the updated global index
        self.save_scanned_directories()
        self.save_file_index()

    def find_duplicates(self, local_file_index: 'FileIndex'):
        """
        Find duplicate files in a FileIndex compared to this FileIndex.

        Args:
            local_file_index (FileIndex): The FileIndex object to compare against the global index.

        Returns:
            list: A list of tuples containing duplicate file pairs.
        """
        duplicates = []
        for file_path1, hash1 in local_file_index.file_index.items():
            for matching_file in self.compare_hash_to_dictionary(hash1):
                if matching_file != file_path1:
                    duplicates.append((file_path1, matching_file))

        return duplicates

