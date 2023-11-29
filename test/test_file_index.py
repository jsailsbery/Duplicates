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
    file_index = FileIndex(TEST_INDEX_FILE)
    yield file_index  # Provide the fixture to the tests

    # Clean up: Remove the test directory and index file
    try:
        os.remove(TEST_INDEX_FILE)
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

