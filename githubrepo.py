import requests
import os
import base64

def login(token):
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get("https://api.github.com/user", headers=headers)

    if response.status_code == 200:
        user_data = response.json()
        print(f"✅ Logged in as: {user_data['login']}")
        return headers, user_data['login']
    else:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        exit(1)

def create_repository(headers):
    repo_name = input("Enter new repository name: ").strip()
    private = input("Private repository? (y/n): ").strip().lower() == 'y'

    data = {
        "name": repo_name,
        "private": private,
        "auto_init": True
    }

    response = requests.post("https://api.github.com/user/repos", headers=headers, json=data)

    if response.status_code == 201:
        print(f"✅ Repository '{repo_name}' created successfully.")
    else:
        print(f"❌ Failed to create repository: {response.json().get('message', response.text)}")

def delete_repository(headers, username):
    repo_name = input("Enter repository name to delete: ").strip()
    confirm = input(f"Are you sure you want to delete '{repo_name}'? (yes/no): ").strip().lower()

    if confirm != 'yes':
        print("🛑 Deletion canceled.")
        return

    url = f"https://api.github.com/repos/{username}/{repo_name}"
    response = requests.delete(url, headers=headers)

    if response.status_code == 204:
        print(f"✅ Repository '{repo_name}' deleted successfully.")
    else:
        print(f"❌ Failed to delete repository: {response.json().get('message', response.text)}")

def get_default_branch(headers, username, repo_name):
    url = f"https://api.github.com/repos/{username}/{repo_name}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("default_branch", "main")
    else:
        print(f"❌ Failed to fetch repository info: {response.json().get('message', response.text)}")
        return "main"

def upload_file(headers, username):
    repo_name = input("Enter repository name to upload to: ").strip()
    local_path = input("Enter local path to file or folder: ").strip()

    branch = get_default_branch(headers, username, repo_name)
    print(f"ℹ️ Using default branch: {branch}")

    if os.path.isfile(local_path):
        upload_single_file(headers, username, repo_name, local_path, branch)
    elif os.path.isdir(local_path):
        upload_folder(headers, username, repo_name, local_path, branch)
    else:
        print("❌ Invalid file or folder path.")

def upload_single_file(headers, username, repo_name, file_path, branch):
    file_name = os.path.basename(file_path)
    github_path = file_name
    url = f"https://api.github.com/repos/{username}/{repo_name}/contents/{github_path}?ref={branch}"

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        confirm = input(f"⚠️ File '{github_path}' already exists. Overwrite? (y/n): ").strip().lower()
        if confirm != 'y':
            print("🛑 Upload canceled.")
            return
        sha = response.json().get('sha')
    else:
        sha = None

    with open(file_path, 'rb') as f:
        content = base64.b64encode(f.read()).decode()

    data = {
        "message": f"Upload {file_name}",
        "content": content,
        "branch": branch
    }
    if sha:
        data["sha"] = sha

    response = requests.put(url, headers=headers, json=data)

    if response.status_code in [200, 201]:
        print(f"✅ Uploaded: {file_name}")
    else:
        print(f"❌ Failed to upload {file_name}: {response.json().get('message', response.text)}")

def upload_folder(headers, username, repo_name, folder_path, branch):
    for root, _, files in os.walk(folder_path):
        for filename in files:
            full_path = os.path.join(root, filename)
            relative_path = os.path.relpath(full_path, folder_path).replace("\\", "/")
            url = f"https://api.github.com/repos/{username}/{repo_name}/contents/{relative_path}?ref={branch}"

            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                confirm = input(f"⚠️ '{relative_path}' exists. Overwrite? (y/n): ").strip().lower()
                if confirm != 'y':
                    print(f"🛑 Skipped: {relative_path}")
                    continue
                sha = response.json().get('sha')
            else:
                sha = None

            with open(full_path, 'rb') as f:
                content = base64.b64encode(f.read()).decode()

            data = {
                "message": f"Upload {relative_path}",
                "content": content,
                "branch": branch
            }
            if sha:
                data["sha"] = sha

            response = requests.put(url, headers=headers, json=data)

            if response.status_code in [200, 201]:
                print(f"✅ Uploaded: {relative_path}")
            else:
                print(f"❌ Failed to upload {relative_path}: {response.json().get('message', response.text)}")

def view_repositories(headers, username):
    url = f"https://api.github.com/users/{username}/repos"
    params = {
        "per_page": 100,
        "sort": "updated"
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        repos = response.json()
        if not repos:
            print("📭 No repositories found.")
            return

        print(f"\n📂 Repositories for '{username}':")
        for i, repo in enumerate(repos, 1):
            visibility = "🔒 Private" if repo['private'] else "🌐 Public"
            print(f"{i}. {repo['name']} ({visibility}) - {repo['html_url']}")
    else:
        print(f"❌ Failed to fetch repositories: {response.json().get('message', response.text)}")

def main():
    print("🔧 GitHub Repository Manager")
    token = os.getenv('GITHUB_TOKEN') or input("Enter your GitHub personal access token: ").strip()
    headers, username = login(token)

    while True:
        print("\n--- Menu ---")
        print("1. Create Repository")
        print("2. Delete Repository")
        print("3. Upload Files or Folder")
        print("4. View My Repositories")
        print("5. Exit")

        choice = input("Enter your choice: ").strip()

        if choice == '1':
            create_repository(headers)
        elif choice == '2':
            delete_repository(headers, username)
        elif choice == '3':
            upload_file(headers, username)
        elif choice == '4':
            view_repositories(headers, username)
        elif choice == '5':
            print("👋 Exiting...")
            break
        else:
            print("❌ Invalid choice. Try again.")

if __name__ == "__main__":
    main()
