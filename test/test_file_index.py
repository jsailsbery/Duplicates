import os
import sys
import shutil
import tempfile
import pytest

sys.path.append("/app")
from duplicates.file_index import FileIndex


# Define the test directory and index file for testing
TEST_DIRECTORY = "test_directory"
TEST_INDEX_FILE = "test_file_index.json"
TEST_DIRS_FILE = "test_scanned_dirs.json"

# Create a fixture for initializing and cleaning up the FileIndex object
@pytest.fixture
def file_index():
    # Create a test directory with a few files
    os.makedirs(TEST_DIRECTORY, exist_ok=True)
    with open(os.path.join(TEST_DIRECTORY, "test_file1.txt"), "w") as f:
        f.write("Test content 1")
    with open(os.path.join(TEST_DIRECTORY, "test_file2.txt"), "w") as f:
        f.write("Test content 2")

    # Initialize the FileIndex object
    file_index = FileIndex(TEST_INDEX_FILE, TEST_DIRS_FILE)
    yield file_index  # Provide the fixture to the tests

    # Clean up: Remove the test directory and index file
    try:
        os.remove(TEST_INDEX_FILE)
        os.remove(TEST_DIRS_FILE)
        shutil.rmtree(TEST_DIRECTORY, ignore_errors=True)
    except FileNotFoundError:
        pass

# Create a fixture for a temporary test file
@pytest.fixture
def temp_test_file():
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(b"Test content")
        temp_file_path = temp_file.name
        yield temp_file_path  # Provide the fixture to the tests

        # Clean up: Remove the temporary test file
        os.remove(temp_file_path)

# Define a fixture for creating a temporary directory
@pytest.fixture
def temp_directory():
    temp_dir = tempfile.mkdtemp()
    with open(os.path.join(temp_dir, "test_file1.txt"), "w") as f:
        f.write("Test content 1")
    with open(os.path.join(temp_dir, "test_file2.txt"), "w") as f:
        f.write("Test content 2")

    yield temp_dir
    shutil.rmtree(temp_dir)

# Define a fixture for creating a second temporary directory
@pytest.fixture
def second_temp_directory():
    temp_dir = tempfile.mkdtemp()
    with open(os.path.join(temp_dir, "test_file1.txt"), "w") as f:
        f.write("Test content 1")
    with open(os.path.join(temp_dir, "test_file2.txt"), "w") as f:
        f.write("Test content 2")

    yield temp_dir
    shutil.rmtree(temp_dir)

def test_get_hash(file_index, temp_test_file):
    test_hash = file_index.calculate_md5(temp_test_file)
    file_index.set_hash(temp_test_file)
    retrieved_hash = file_index.get_hash(temp_test_file)
    assert retrieved_hash == test_hash

def test_set_hash(file_index, temp_test_file):
    test_hash = file_index.calculate_md5(temp_test_file)
    file_index.set_hash(temp_test_file)
    retrieved_hash = file_index.get_hash(temp_test_file)
    assert retrieved_hash == test_hash

def test_file_index_creation(file_index):
    assert isinstance(file_index, FileIndex)

def test_file_index_loading(file_index):
    loaded_index = file_index.load_file_index()
    assert isinstance(loaded_index, dict)

def test_file_index_saving(file_index):
    file_index.file_index = {"test_file.txt": "hash123"}
    file_index.save_file_index()
    loaded_index = file_index.load_file_index()
    assert "test_file.txt" in loaded_index
    assert loaded_index["test_file.txt"] == "hash123"

def test_calculate_md5(file_index):
    test_file_path = os.path.join(TEST_DIRECTORY, "test_file.txt")
    with open(test_file_path, "w") as f:
        f.write("Test content")
    md5_hash = file_index.calculate_md5(test_file_path)
    assert isinstance(md5_hash, str)
    assert len(md5_hash) == 32

def test_compare_hashes(file_index, temp_test_file):
    file_index.set_hash(temp_test_file)
    actual_hash = file_index.calculate_md5(temp_test_file)

    assert file_index.compare_hashes(temp_test_file, actual_hash)
    assert not file_index.compare_hashes(temp_test_file, "invalid_hash")

def test_compare_hash_to_dictionary(file_index, temp_test_file):
    
    file_index.set_hash(temp_test_file)
    actual_hash = file_index.calculate_md5(temp_test_file)

    matching_files = file_index.compare_hash_to_dictionary(actual_hash)
    non_matching_files = file_index.compare_hash_to_dictionary("invalid_hash")

    assert temp_test_file in matching_files
    assert not non_matching_files

def test_create_file_index(file_index):
    # Ensure the test directory is empty initially
    file_index_new = FileIndex(index_file="temp1.json")
    assert len(file_index_new.file_index) == 0

    # Create the file index for the test directory
    file_index_new.create_file_index(TEST_DIRECTORY)

    # Check if files in the test directory have been added to the index
    assert len(file_index_new.file_index) > 0

    # Check if the file index contains the expected files
    expected_files = {
        os.path.abspath(os.path.join(TEST_DIRECTORY, "test_file1.txt")),
        os.path.abspath(os.path.join(TEST_DIRECTORY, "test_file2.txt")),
    }
    for file_path in expected_files:
        assert file_path in file_index_new.file_index

    # Check that the file index doesn't contain unexpected files
    unexpected_files = {
        os.path.abspath(TEST_INDEX_FILE),
        os.path.abspath(__file__),
    }
    for file_path in unexpected_files:
        assert file_path not in file_index_new.file_index

    del file_index_new
    os.remove("temp1.json")

def test_load_scanned_directories_empty(file_index):
    assert file_index.scanned_directories == []

def test_save_and_load_scanned_directories(file_index):
    # Add some scanned directories
    scanned_dirs = ["/dir1", "/dir2", "/dir3"]
    file_index.scanned_directories = scanned_dirs

    # Save the scanned directories to the file
    file_index.save_scanned_directories()

    # Clear the in-memory scanned directories
    file_index.scanned_directories = []

    # Load the scanned directories from the file
    test_scanned_dirs = file_index.load_scanned_directories()

    # Check if the loaded scanned directories match the saved ones
    assert test_scanned_dirs == scanned_dirs

def test_update(file_index):
    # Add test directories and files to the index
    test_directory1 = "test_dir1"
    test_directory2 = "test_dir2"
    test_file1 = "test_dir1/test_file1.txt"
    test_file2 = "test_dir2/test_file2.txt"

    file_index.scanned_directories.extend([test_directory1, test_directory2])
    file_index.file_index[test_file1] = "hash1"
    file_index.file_index[test_file2] = "hash2"

    # Create test directories and files
    os.makedirs(test_directory1, exist_ok=True)
    os.makedirs(test_directory2, exist_ok=True)
    with open(test_file1, "w") as f:
        f.write("Test content 1")
    with open(test_file2, "w") as f:
        f.write("Test content 2")

    # Run the update method with deep_scan=True
    file_index.update(deep_scan=True)

    # Check if the scanned directories and index have been updated correctly
    assert test_directory1 in file_index.scanned_directories
    assert test_directory2 in file_index.scanned_directories
    assert test_file1 in file_index.file_index
    assert test_file2 in file_index.file_index
    assert file_index.file_index[test_file1] != "hash1"  # Hash should be updated
    assert file_index.file_index[test_file2] != "hash2"  # Hash should be updated


# Test the add method
def test_add(temp_directory):
    # Create two FileIndex objects
    file_index1 = FileIndex(index_file=os.path.join(temp_directory, "index1.json"))
    file_index2 = FileIndex(index_file=os.path.join(temp_directory, "index2.json"))

    # Populate file_index1 with some data
    file_index1.create_file_index(temp_directory)
    file_index1.save_file_index()

    # Populate file_index2 with different data
    temp_subdirectory = os.path.join(temp_directory, "subdirectory")
    os.mkdir(temp_subdirectory)
    file_index2.create_file_index(temp_subdirectory)
    file_index2.save_file_index()

    # Create a GlobalFileIndex object and add both file_index1 and file_index2
    global_index = FileIndex()
    global_index.add(file_index1)
    global_index.add(file_index2)

    # Check if scanned directories and file index are merged correctly
    assert temp_directory in global_index.scanned_directories
    assert temp_subdirectory in global_index.scanned_directories
    assert len(global_index.file_index) == len(file_index1.file_index) + len(file_index2.file_index)

# Test the find_duplicates method
def test_find_duplicates(temp_directory, second_temp_directory):
    # Create two FileIndex objects
    local_file_index = FileIndex(index_file=os.path.join(temp_directory, "local_index.json"))
    global_file_index = FileIndex(index_file=os.path.join(temp_directory, "global_index.json"))

    # Populate local_file_index with some data
    local_file_index.create_file_index(temp_directory)
    local_file_index.save_file_index()
    assert len(local_file_index.file_index) > 0

    # Populate global_file_index with some different data
    global_file_index.create_file_index(second_temp_directory)
    global_file_index.save_file_index()
    assert len(global_file_index.file_index) > 0

    # Create a GlobalFileIndex object and add global_file_index
    global_index = FileIndex()
    global_index.add(global_file_index)

    # Find duplicates between local_file_index and global_index
    duplicates = global_index.find_duplicates(local_file_index)

    # Check if duplicates are found correctly
    assert len(duplicates) > 0

