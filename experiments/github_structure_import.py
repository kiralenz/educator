import json
import requests

# Fetch repository file tree structure from GitHub API
url = 'https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1'
owner = 'kiralenz'
repo = 'keeprising'
branch = 'main'  # Replace with the desired branch name
response = requests.get(url.format(owner=owner, repo=repo, branch=branch))
repository_tree = response.json()

# Serialize repository file tree structure to JSON
json_data = json.dumps(repository_tree, indent=4)

# Write JSON data to a file
with open('repository_tree.json', 'w') as json_file:
    json_file.write(json_data)