# GitHub Activity Dashboard

An interactive dashboard for visualizing GitHub repository activity, built with Python, GitHub API, and Streamlit.


## Features

- **Commit Activity Visualization**: Track commit patterns over time with daily, weekly, and monthly views
- **Repository Comparison**: Compare repositories by stars, forks, and activity level
- **Contributor Insights**: Identify key contributors and their activity patterns
- **Time Pattern Analysis**: Discover when development happens (day of week, hour of day)
- **Commit Content Analysis**: Analyze types of commits (features, bug fixes, refactoring)

## Quick Start

### Prerequisites

- Python 3.8+
- GitHub Personal Access Token (optional, for higher API rate limits)

### Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/github-activity-dashboard.git
   cd github-activity-dashboard
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

### Running the Dashboard

1. Launch the dashboard:
   ```
   streamlit run dashboard.py
   ```
   
   The dashboard will open automatically in your browser at http://localhost:8501

2. Use the sidebar controls to:
   - Select an organization
   - Choose repositories to analyze
   - Filter by date range
   - Apply additional filters (language, commit type)

### Generating Fresh Data (Optional)

The repository includes sample data, but you can fetch fresh data:

1. Optionally add your GitHub token in `fetch_github_data.py` (increases API rate limit):
   ```python
   # Find this line in fetch_github_data.py
   TOKEN = "your_github_token_here"
   ```

2. Run the data collection script:
   ```
   python fetch_github_data.py
   ```

## Dashboard Sections

1. **Key Metrics**: High-level statistics about repositories and commits
2. **Commit Activity**: Visualize commit patterns over time
3. **Repository Analysis**: Compare repositories by popularity and activity
4. **Contributor Insights**: Analyze contributor behavior and engagement
5. **Time Patterns**: Discover when development happens (day/hour heatmaps)
6. **Commit Content**: Analyze the types of changes being made

## Customization

You can modify `fetch_github_data.py` to:
- Change target organizations (ORGS list)
- Adjust the number of repositories (MAX_REPOS)
- Change the number of commits per repository (MAX_COMMITS)

## Project Structure

- `dashboard.py`: Streamlit application with interactive visualizations
- `fetch_github_data.py`: Script for collecting data from GitHub API
- Data files:
  - `repositories.csv`: Repository metadata (stars, forks, etc.)
  - `commits.csv`: Detailed commit information
  - `contributors.csv`: Contributor statistics

## Technologies Used

- [Streamlit](https://streamlit.io/): Interactive dashboard framework
- [Plotly](https://plotly.com/): Data visualization library
- [Pandas](https://pandas.pydata.org/): Data analysis and manipulation
- [GitHub API](https://docs.github.com/en/rest): Data source
