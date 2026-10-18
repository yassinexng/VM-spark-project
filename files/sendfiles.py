import subprocess
import pandas as pd

def send_file(file):
    #the path to the vm's file: /home/vmw/folder/files
    #format: scp /home/username/path/to/file.csv username@name_of_machinb:/home/username/destination/folder/   
    #u need to change it accoridngly for this to work
    #MUST change !! u can also do import os load_dotenv and define the path within the .env path
    try:
        file1 = subprocess.run([
            "scp",
            f"/home/ysn/Documents/projects/proji_2/files/{file}",
            "vmw@newvm:/home/vmw/folder/files/"],
            check=True
        )
        return "Success"
    except Exception as e:
        return f"Error: {e}"

def sendback_file(file):
    try:
        file1 = subprocess.run([
            "scp",
            f"/home/vmw/folder/files/{file}",
            "ysn@ysnslaptop:/home/ysn/Documents/projects/proji_2/files/"
        ],
            check=True
        )
        return "Success"
    except Exception as e:
        return f"Error: {e}"


def send_from_local_tovm():
    if send_file("our_daemon.service") == "Success" and send_file("processer.py") == "Success":
        return True
    else:
        return False


def main_func():
    print("D.. ")


if __name__ == "__main__":
    main_func()   