import sys

sys.path.append("/app")
from duplicates.file_index import FileIndex

def main(directory1, directory2):
    # Create FileIndex objects for each directory
    file_index1 = FileIndex()
    file_index2 = FileIndex()

    # Create indices for both directories
    file_index1.create_file_index(directory1)
    file_index2.create_file_index(directory2)

    # Find duplicates between the two indices
    duplicates = file_index1.find_duplicates(file_index2)

    # Print the duplicate entries
    for duplicate_pair in duplicates:
        print(f"Duplicate found: {duplicate_pair[0]} and {duplicate_pair[1]}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python find_duplicates.py <directory1> <directory2>")
        sys.exit(1)

    directory1 = sys.argv[1]
    directory2 = sys.argv[2]

    main(directory1, directory2)

