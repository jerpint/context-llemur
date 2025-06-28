import subprocess
import os

def run_git_command(args):
    subprocess.run("git", args)

def gid_init(path):
    if os.path.exists(path):
        print("gid exists, skipping.")
        return
    
    print(f"initializing gid in {path}")
    
    subprocess.run(["cp", "-r", "template", path])
    os.chdir(path)

    subprocess.run(["git", "init"])
    subprocess.run(["git", "add", "-A"])
    subprocess.run(["git", "commit", "-m", "first commit"])

    print("gid initialized!")

def get_token_count():
    pass

def create_file(filename):
	pass

def edit_file(filename):
    pass

def delete_file(filename):
    pass

def new_idea(idea: str):
    pass

def new_branch():
    pass


def main():
    folder = "my_memories"
    gid_init("my_memories")


if __name__ == "__main__":
    main()
