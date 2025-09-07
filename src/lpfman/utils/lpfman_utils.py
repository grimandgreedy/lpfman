import os 
import stat
from listpick.utils.utils import format_size
from datetime import datetime
import hashlib
import mimetypes


def get_size(filename):
    """
    Returns the size of the file if 'filename' is a file,
    or the number of items in the directory if 'filename' is a directory.
    
    Parameters:
    filename (str): The path to the file or directory.
    
    Returns:
    int: The size of the file (in bytes) if it's a file, 
         or the number of items (files and directories) if it's a directory.
    """
    if os.path.isfile(filename):
        size_bytes = os.path.getsize(filename)
        size = format_size(size_bytes)
        return f"{size}"
    elif os.path.isdir(filename):
        try:
            num_items = len(os.listdir(filename))
            return f"{num_items} items"
        except:
            return "? items"
    else:
        raise ValueError(f"'{filename}' is not a valid file or directory")

def get_mtime(filename):
    """
    Returns the last modified date of a file in a human-readable form.
    
    Parameters:
    filename (str): The path to the file.
    
    Returns:
    str: The last modified date in a human-readable format.
    """
    if not os.path.exists(filename):
        return "?"
    
    # Get the last modified time of the file
    last_modified_time = os.path.getmtime(filename)
    
    # Convert the timestamp to a datetime object
    readable_date = datetime.fromtimestamp(last_modified_time).strftime('%Y-%m-%d %H:%M:%S')
    
    return readable_date


def generate_hash(input_string):
    hash_object = hashlib.sha256()
    hash_object.update(input_string.encode('utf-8'))
    hex_digest = hash_object.hexdigest()
    return hex_digest

def get_filetype(filename):
    if os.path.isdir(filename):
        return "directory"
    else:
        mime_type, _ = mimetypes.guess_type(filename)

        if "." in filename.split("/")[-1]:
            return filename.split(".")[-1]
        else:

            result = subprocess.run(['file', '-i', filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode == 0:
                # Extract the MIME type from the command's output
                mime_type = result.stdout.strip().split(':')[1].strip().split(";")[0].strip()
                return mime_type
            else:
                return ""

import subprocess

def get_file_type(filename):
    """
    Determine the file type (MIME type) of a given file by inspecting its contents.
    
    Args:
        filename (str): The path to the file for which you want to determine the MIME type.
        
    Returns:
        str: The MIME type of the file, or "unknown" if it cannot be determined.
    """
    try:
        # Run the 'file -i' command and capture its output
        result = subprocess.run(['file', '-i', filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Check if the command was successful
        if result.returncode == 0:
            # Extract the MIME type from the command's output
            mime_type = result.stdout.strip().split(':')[1].strip()
            return mime_type
        else:
            print(f"Error running 'file -i {filename}': {result.stderr}")
            return "unknown"
    except FileNotFoundError:
        print(f"The file '{filename}' does not exist.")
        return "unknown"


def get_file_permissions(filepath):
    try:
        # Get file status
        file_stat = os.stat(filepath)
        # Convert mode to symbolic representation (e.g., -rw-r--r--)
        permissions = stat.filemode(file_stat.st_mode)
        return permissions

    except Exception as e:
        return ""
