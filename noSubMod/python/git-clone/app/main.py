import sys
import os
import argparse
import zlib


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    #print("Logs from your program will appear here!")

    # Uncomment this block to pass the first stage
    #
    command = sys.argv[1]
    args = sys.argv[2:]
    if command == "init":
        init()
    elif command == "cat-file":
        catfile(args)
    else:
        raise RuntimeError(f"Unknown command #{command}")

def init():
    os.mkdir(".git")
    os.mkdir(".git/objects")
    os.mkdir(".git/refs")
    with open(".git/HEAD", "w") as f:
        f.write("ref: refs/heads/main\n")
    print("Initialized git directory")

def argparser():
    parser = argparse.ArgumentParser(description="Simple git")
    parser.add_argument("command", help="Command to run")
    return parser.parse_args()

def catfile(args) -> str:
    #print(f"args: {args}")
    returnType = args[0]
    file = args[1]
    if returnType == "-p":
        f = open(f".git/objects/{file[:2]}/{file[2:]}", "rb")
        data = zlib.decompress(f.read())
        data = data.split(b"\x00", 1)
        value = data[1].decode("utf-8").split("\n")[0].strip()      
        print(value.strip(), end='')
    else:
        print("Unknown cat-file option: ", returnType)

if __name__ == "__main__":

    main()
