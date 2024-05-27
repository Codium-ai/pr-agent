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

def modify_toml_key(file_path, key_path, new_value):
    """
    Modify a key in a TOML file and save the changes.

    :param file_path: Path to the TOML file
    :param key_path: The key to modify, specified as a list of nested keys
    :param new_value: The new value to set for the key
    """
    # Read the existing data from the TOML file
    try:
        with open(file_path, 'r') as file:
            toml_data = toml.load(file)
    except FileNotFoundError:
        print(f"Error: The file {file_path} does not exist.")
        return
    except toml.TomlDecodeError as e:
        print(f"Error parsing TOML file: {e}")
        return

    # Navigate to the key to modify
    d = toml_data
    if key_path[1] != "private_key":
        for key in key_path[:-1]:
            d = d.get(key, {})
            print(d)
        d[key_path[-1]] = new_value

    # Write the modified data back to the TOML file
    try:
        with open("pr_agent/settings/.secrets.toml", 'w') as file:
            toml.dump(toml_data, file)
        print(f"Successfully updated {key_path} in {file_path}.")
    except Exception as e:
        print(f"Error writing to TOML file: {e}")
        
    if key_path[1] == "private_key":
        with open("pr_agent/settings/.secrets.toml", 'r') as file:
            file_contents = file.read()

        modified_contents = re.sub("<GITHUB PRIVATE KEY>", new_value, file_contents)
        modified_contents=modified_contents.replace('private_key = "-----BEGIN RSA PRIVATE KEY-----\\n', '''private_key = """\\\n-----BEGIN RSA PRIVATE KEY-----''') 
        modified_contents=modified_contents.replace('\\n-----END RSA PRIVATE KEY-----\\n', '''\n-----END RSA PRIVATE KEY-----\n""''') 

        with open("pr_agent/settings/.secrets.toml", 'w') as file:
            file.write(modified_contents)


secret_dict = json.loads(get_aws_secrets(secret_name,region_name))
modify_toml_key("pr_agent/settings/.secrets_template.toml", ['openai', 'key'], secret_dict.get('open_ai_gpt4_token'))
modify_toml_key("pr_agent/settings/.secrets.toml", ['github', 'app_id'], int(secret_dict.get('app_id')))
modify_toml_key("pr_agent/settings/.secrets.toml", ['github', 'webhook_secret'], secret_dict.get('webhook_secret'))
modify_toml_key("pr_agent/settings/.secrets.toml", ['github', 'private_key'], secret_dict.get('private_key').replace(" ","\n"))

subprocess.run(['python', 'pr_agent/servers/github_app.py'])
