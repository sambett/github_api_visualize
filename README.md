# GitHub Activity Dashboard

An interactive dashboard for visualizing GitHub repository activity, built with Python, GitHub API, and Streamlit.

## Features

- **Commit Activity Visualization**: Track commit patterns over time with daily, weekly, and monthly views
- **Repository Comparison**: Compare repositories by stars, forks, and activity level
- **Contributor Insights**: Identify key contributors and their activity patterns
- **Time Pattern Analysis**: Discover when development happens (day of week, hour of day)
- **Commit Content Analysis**: Analyze types of commits (features, bug fixes, refactoring)

## Getting Started

### Prerequisites

- Python 3.8+
- GitHub Personal Access Token (for fetching data from the GitHub API)

### Installation

1. Clone this repository:
```
git clone https://github.com/sambett/github_api_visualize.git
cd github_api_visualize
```

2. Install dependencies:
```
pip install -r requirements.txt
```

### Usage

1. Fetch GitHub data (optional - sample data already included):
```
python fetch_github_data.py
```

2. Run the dashboard:
```
streamlit run dashboard.py
```

## Data Files

- `repositories.csv`: Information about GitHub repositories
- `commits.csv`: Commit history data
- `contributors.csv`: Contributor information

## Technologies Used

- [Streamlit](https://streamlit.io/): For building the interactive dashboard
- [Plotly](https://plotly.com/): For data visualization
- [Pandas](https://pandas.pydata.org/): For data manipulation
- [GitHub API](https://docs.github.com/en/rest): For fetching repository data
