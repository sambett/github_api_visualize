import requests
import csv
import time
import datetime

# ============ CONFIG ============

# GitHub token configuration
# The script will work without a token but with rate limits (60 requests/hour)
TOKEN = ""
HEADERS = {} if TOKEN == "" else {"Authorization": f"token {TOKEN}"}

# Organizations to analyze (expanded list)
ORGS = [
    "microsoft", "google", "facebook", "apple", "amazon", 
    "netflix", "twitter", "linkedin", "airbnb", "uber",
    "square", "stripe", "shopify", "github", "elastic"
]

# Repos & commits limits (increased)
MAX_REPOS = 10
MAX_COMMITS = 200

# ============ FETCH LOGIC ============

def get_repos(org):
    url = f"https://api.github.com/orgs/{org}/repos?per_page={MAX_REPOS}&sort=updated"
    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200:
        print(f"[!] Failed to get repos for {org}: {res.status_code}")
        return []
    return res.json()

def get_commits(org, repo):
    url = f"https://api.github.com/repos/{org}/{repo}/commits?per_page={MAX_COMMITS}"
    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200:
        print(f"[!] Failed to get commits for {org}/{repo}: {res.status_code}")
        return []
    return res.json()

def get_contributors(org, repo, limit=10):
    url = f"https://api.github.com/repos/{org}/{repo}/contributors?per_page={limit}"
    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200:
        print(f"[!] Failed to get contributors for {org}/{repo}: {res.status_code}")
        return []
    return res.json()

# ============ MAIN ============

def fetch_data():
    print("Starting GitHub data extraction...")
    start_time = datetime.datetime.now()
    
    with open("repositories.csv", "w", newline='', encoding='utf-8') as repo_file, \
         open("commits.csv", "w", newline='', encoding='utf-8') as commit_file, \
         open("contributors.csv", "w", newline='', encoding='utf-8') as contributor_file:

        repo_writer = csv.writer(repo_file)
        commit_writer = csv.writer(commit_file)
        contributor_writer = csv.writer(contributor_file)

        # Headers for each CSV file
        repo_writer.writerow([
            "org", "repo_name", "repo_id", "stars", "forks", 
            "open_issues", "watchers", "language", "created_at", 
            "updated_at", "description"
        ])
        
        commit_writer.writerow([
            "org", "repo_name", "commit_sha", "author", 
            "author_email", "message", "date", "day_of_week", 
            "hour_of_day", "additions", "deletions"
        ])
        
        contributor_writer.writerow([
            "org", "repo_name", "contributor_login", 
            "contributor_id", "contributions"
        ])

        repos_fetched = 0
        commits_fetched = 0
        contributors_fetched = 0

        for org in ORGS:
            print(f"Fetching repos for organization: {org}")
            repos = get_repos(org)

            for repo in repos:
                repo_name = repo["name"]
                
                # More detailed repository data
                repo_writer.writerow([
                    org,
                    repo_name,
                    repo["id"],
                    repo["stargazers_count"],
                    repo["forks_count"],
                    repo.get("open_issues_count", 0),
                    repo.get("watchers_count", 0),
                    repo.get("language", ""),
                    repo["created_at"],
                    repo["updated_at"],
                    repo.get("description", "").replace("\n", " ") if repo.get("description") else ""
                ])
                repos_fetched += 1

                print(f"Fetching commits for repo: {org}/{repo_name}")
                commits = get_commits(org, repo_name)
                for commit in commits:
                    # Get commit details
                    commit_sha = commit["sha"]
                    commit_data = commit["commit"]
                    author = commit_data["author"]["name"]
                    author_email = commit_data["author"]["email"]
                    message = commit_data["message"].replace("\n", " ")
                    date = commit_data["committer"]["date"]
                    
                    # Calculate day of week and hour of day from commit date
                    commit_date = datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
                    day_of_week = commit_date.strftime('%A')
                    hour_of_day = commit_date.hour
                    
                    # For additions/deletions, we'd need another API call per commit
                    # But that would hit rate limits quickly, so use placeholders
                    additions = 0
                    deletions = 0

                    commit_writer.writerow([
                        org,
                        repo_name,
                        commit_sha,
                        author,
                        author_email,
                        message,
                        date,
                        day_of_week,
                        hour_of_day,
                        additions,
                        deletions
                    ])
                    commits_fetched += 1

                # Get top contributors
                print(f"Fetching contributors for repo: {org}/{repo_name}")
                contributors = get_contributors(org, repo_name)
                for contributor in contributors:
                    contributor_writer.writerow([
                        org,
                        repo_name,
                        contributor["login"],
                        contributor["id"],
                        contributor["contributions"]
                    ])
                    contributors_fetched += 1

                time.sleep(1)  # Rate limit safety

        end_time = datetime.datetime.now()
        duration = end_time - start_time
        
        print("\n=== GitHub Data Extraction Summary ===")
        print(f"Total organizations: {len(ORGS)}")
        print(f"Total repositories: {repos_fetched}")
        print(f"Total commits: {commits_fetched}")
        print(f"Total contributors: {contributors_fetched}")
        print(f"Duration: {duration}")
        print("Files saved:")
        print("- repositories.csv")
        print("- commits.csv")
        print("- contributors.csv")

# Run the script
if __name__ == "__main__":
    fetch_data()
