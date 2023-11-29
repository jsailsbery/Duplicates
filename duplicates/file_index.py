import os
import hashlib
import logging
import json

class FileIndex:
    def __init__(self, index_file="file_index.json",directories_file="scanned_directories.json", force_update=False, deep_scan=False):
        self.index_file = index_file
        self.directories_file = directories_file
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

    def update(self, deep_scan=False):
        # Step 1: Check and remove directories that no longer exist
        logging.info("Step 1: Check and remove directories that no longer exist")
        
        existing_directories = []
        for directory in self.scanned_directories:
            if os.path.exists(directory):
                existing_directories.append(directory)
        self.scanned_directories = existing_directories

        # Step 2: Scan all files in file_index and remove if they no longer exist
        logging.info("Step 2: Scan all files in file_index and remove non-existent files")
        existing_files = {}
        for file_path, hash_value in self.file_index.items():
            if os.path.exists(file_path):
                existing_files[file_path] = hash_value
        self.file_index = existing_files

        # Step 3: Recalculate MD5 values for existing files
        if deep_scan:
            logging.info("Step 3: Recalculate MD5 values for existing files")
            for file_path in self.file_index.keys():
                self.file_index[file_path] = self.calculate_md5(file_path)

        # Save the updated list of scanned directories and file index
        self.save_scanned_directories()
        self.save_file_index()
