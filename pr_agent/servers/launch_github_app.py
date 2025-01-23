import subprocess
import re
import boto3
import json
import toml
from botocore.exceptions import ClientError

secret_name = "devops/github/pr-agent-bot"
region_name = "eu-west-1"

def get_aws_secrets(secret_name, region_name):
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        raise e

    secret = get_secret_value_response['SecretString']
    return secret

def create_toml_file(file_path, secret_content):
    try:
        with open("pr_agent/settings/.secrets.toml", 'w') as file:
            file.write(secret_content)
        print(f"Successfully updated in {file_path}.")
    except Exception as e:
        print(f"Error writing to TOML file: {e}")

secret_dict = json.loads(get_aws_secrets(secret_name,region_name))
secret_toml=secret_dict.get('secret_file')
create_toml_file("pr_agent/settings/.secrets.toml",secret_toml)
subprocess.run(["python", "-m", "gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-c", "pr_agent/servers/gunicorn_config.py", "--forwarded-allow-ips", "*", "pr_agent.servers.github_app:app"])
