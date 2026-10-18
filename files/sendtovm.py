import subprocess

FILES = ["processer.py", "get_data.py", "sendfiles.py", "our_daemon.service"]
LOCAL_DIR = "/home/ysn/Documents/projects/proji_2/files"
REMOTE_DIR = "vmw@newvm:/home/vmw/folder/files/"

def send_all():
    for f in FILES:
        result = subprocess.run(
            ["scp", f"{LOCAL_DIR}/{f}", f"{REMOTE_DIR}{f}"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"Failed to send {f}: {result.stderr}")
            return False
        print(f"Sent {f}")
    return True

def run_on_vm():
    result = subprocess.run(
        ["ssh", "vmw@newvm",
         "/home/vmw/folder/files/.venv/bin/python /home/vmw/folder/files/processer.py"],
        capture_output=True, text=True
    )
    if result.stdout:
        print(result.stdout)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    return True

def main():
    if send_all():
        print("All files sent. Starting processer.py on the VM")
        if run_on_vm():
            print(" Check local files folder for results.")
        else:
            print("Execution failed.")
    else:
        print("iles not sent.")

if __name__ == "__main__":
    main()   