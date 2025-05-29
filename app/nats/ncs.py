import subprocess
import os
from nats.aio.client import Client as NATS
import asyncio

from dotenv import load_dotenv

load_dotenv()

NSC_PATH = "nsc"  # giả định nsc đã được cài và trong $PATH
ACCOUNT_NAME = "chat"
USER_NAME = "alice"
CREDS_FOLDER = f"~/.local/share/nats/nsc/keys/creds/org-alpha/chat-app/"

def run_ncs_command(args, capture_output=False):
    try:
        if capture_output:
            result = subprocess.run([NSC_PATH] + args, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        else:
            subprocess.run([NSC_PATH] + args, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running nsc command: {e}")
        return None

def add_operator(operator_name):
    print(f"Adding operator {operator_name}...")
    run_ncs_command(["add", "operator", "--name", operator_name])

def get_operators():
    output = run_ncs_command(["list", "operators"], capture_output=True)
    if output:
        operators = output.splitlines()
        return operators
    else:
        return []

def create_account(account_name):
    print(f"Creating account {account_name}...")
    run_ncs_command(["add", "account", "--name", account_name])
    print(f"Account {account_name} created successfully.")

def get_creds_path(username):
    creds_folder = os.path.expanduser(CREDS_FOLDER)
    if not os.path.exists(creds_folder):
        os.makedirs(creds_folder)
    return os.path.join(creds_folder, f"{username}.creds")

def get_accounts():
    output = run_ncs_command(["list", "accounts"], capture_output=True)
    if output:
        accounts = output.splitlines()
        return accounts
    else:
        return []

def create_user(username, account):
    print(f"Creating user {username} in account {account}...")
    run_ncs_command(["add", "user", username, "--account", account])
    print(f"User {username} created successfully.")

def get_users(account):
    output = run_ncs_command(["list", "users", "--account", account], capture_output=True)
    if output:
        users = output.splitlines()
        return users
    else:
        return []

def export_creds(username, account, output_file):
    print(f"Exporting credentials for user {username} in account {account}...")
    with open(output_file, 'w') as f:
        run_ncs_command(["export", "creds", username, "--account", account, "--output", output_file], capture_output=True)
    print(f"Credentials exported to {output_file}.")

def edit_permissions(user, allowed_subjects=None, denied_subjects=None, allow_publish=False, denied_publish=False):
    print(f"Editing permissions for user {user}...")
    args = ["edit", "user", user]
    if allowed_subjects:
        args.append(f"--allow-sub={','.join(allowed_subjects)}")
    if denied_subjects:
        args.append(f"--deny-sub={','.join(denied_subjects)}")
    if allow_publish:
        args.append("--allow-pub")
    if denied_publish:
        args.append("--deny-pub")
    run_ncs_command(args)
    print(f"Permissions updated for user {user}.")

def describe_user(username):
    print(f"Describing user {username}...")
    output = run_ncs_command(["describe", "user", "--name", username], capture_output=True)
    if output:
        print(output)
    else:
        print(f"No details found for user {username}.")
