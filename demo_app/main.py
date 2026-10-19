# demo_app/main.py
"""Simple entry point that exercises the demo modules.

Running this file will trigger the intentional issues above, which is
useful if you ever want to run the code locally to see the behaviour.
"""

if __name__ == "__main__":
    from .core import get_user_data, process_all_users
    from .utils import hash_password, read_file_safely, dummy_s3_upload

    # Demo calls
    print(get_user_data(42))
    process_all_users()
    print(hash_password("mysecret"))
    # Uncomment the next line only if you have a file named "test.txt" in the cwd
    # print(read_file_safely("test.txt"))
    dummy_s3_upload(b"hello world")