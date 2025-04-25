import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import numpy as np
from collections import Counter
import re

# Set page title and layout
st.set_page_config(
    page_title="GitHub Analytics Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #0e1117;
        margin-bottom: 1rem;
        background: linear-gradient(90deg, #4d7eff, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #0e1117;
        margin-top: 1rem;
        padding-bottom: 0.3rem;
        border-bottom: 2px solid #e6e6e6;
    }
    .chart-header {
        font-size: 1.2rem;
        font-weight: 600;
        color: #0e1117;
        margin-top: 0.5rem;
    }
    .chart-description {
        font-size: 0.9rem;
        color: #555;
        font-style: italic;
        margin-bottom: 1rem;
        background-color: #f9f9f9;
        padding: 0.5rem;
        border-left: 2px solid #4d7eff;
    }
    .metric-card {
        background-color: white;
        border-radius: 5px;
        padding: 1rem;
        box-shadow: 0 0 15px rgba(0,0,0,0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 5px 20px rgba(0,0,0,0.15);
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #4d7eff;
    }
    .metric-label {
        font-size: 1rem;
        color: #7c7c7c;
        margin-top: 0.5rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: white;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #e6f3ff;
        border-bottom: 2px solid #4da6ff;
    }
    .insight-box {
        background-color: #f0f7ff;
        border-radius: 5px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 0 10px rgba(0,0,0,0.05);
    }
    .insight-title {
        font-weight: 600;
        color: #0e1117;
        margin-bottom: 0.5rem;
    }
    .insight-value {
        font-size: 1.1rem;
        font-weight: 500;
        color: #4d7eff;
    }
</style>
""", unsafe_allow_html=True)

# Check if the CSV files exist
required_files = ["repositories.csv", "commits.csv"]
missing_files = [f for f in required_files if not os.path.exists(f)]

if missing_files:
    st.error(f"Missing data files: {', '.join(missing_files)}")
    st.info("Please run simple_data_generator.py first to create sample data.")
    st.stop()

# Function to load data
@st.cache_data(ttl=3600)
def load_data():
    # Try to load from main directory first, then from github_data if that fails
    try:
        repos_df = pd.read_csv("repositories.csv")
        commits_df = pd.read_csv("commits.csv")
        
        # Check if contributors file exists
        if os.path.exists("contributors.csv"):
            contributors_df = pd.read_csv("contributors.csv")
        else:
            contributors_df = None
            
    except:
        # Try github_data directory as fallback
        if os.path.exists("github_data/repositories.csv") and os.path.exists("github_data/commits.csv"):
            repos_df = pd.read_csv("github_data/repositories.csv")
            commits_df = pd.read_csv("github_data/commits.csv")
            
            if os.path.exists("github_data/contributors.csv"):
                contributors_df = pd.read_csv("github_data/contributors.csv")
            else:
                contributors_df = None
        else:
            raise FileNotFoundError("Could not find data files in either main directory or github_data directory")
    
    # Convert date strings to datetime
    repos_df['created_at'] = pd.to_datetime(repos_df['created_at'])
    repos_df['updated_at'] = pd.to_datetime(repos_df['updated_at'])
    commits_df['date'] = pd.to_datetime(commits_df['date'])
    
    # Extract additional date information for analysis
    commits_df['year'] = commits_df['date'].dt.year
    commits_df['month'] = commits_df['date'].dt.month
    commits_df['month_name'] = commits_df['date'].dt.month_name()
    
    # Ensure day_of_week and hour_of_day exist
    if 'day_of_week' not in commits_df.columns:
        commits_df['day_of_week'] = commits_df['date'].dt.day_name()
    if 'hour_of_day' not in commits_df.columns:
        commits_df['hour_of_day'] = commits_df['date'].dt.hour
    
    return repos_df, commits_df, contributors_df

# Function to extract patterns from commit messages
@st.cache_data
def analyze_commit_messages(commits_df):
    # Don't analyze if no message column
    if 'message' not in commits_df.columns:
        return commits_df
        
    # Common patterns to look for in commit messages
    patterns = {
        'feature': r'(?i)add|new|feature|implement|support',
        'bug_fix': r'(?i)fix|bug|issue|problem|error|crash',
        'refactor': r'(?i)refactor|clean|improve|enhance|optimize|update',
        'docs': r'(?i)doc|comment|readme|changelog',
        'test': r'(?i)test|spec|unittest',
        'style': r'(?i)style|format|whitespace|indent',
        'merge': r'(?i)merge|pull request|PR'
    }
    
    # Initialize columns for each pattern
    for pattern_name in patterns:
        commits_df[pattern_name] = False
    
    # Detect patterns in commit messages
    for idx, row in commits_df.iterrows():
        message = str(row['message'])
        for pattern_name, regex in patterns.items():
            if re.search(regex, message):
                commits_df.at[idx, pattern_name] = True
    
    return commits_df

# Try to load the data
try:
    repos_df, commits_df, contributors_df = load_data()
    
    # Analyze commit messages if applicable
    if 'message' in commits_df.columns:
        commits_df = analyze_commit_messages(commits_df)
        
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.info("Make sure the CSV files are properly formatted.")
    st.stop()

# Dashboard title
st.markdown('<div class="main-header">GitHub Analytics Dashboard</div>', unsafe_allow_html=True)
st.markdown("""
This interactive dashboard provides comprehensive visual analytics of GitHub repository activity. Explore commit patterns, 
contributor engagement, repository statistics, and development trends to gain deeper insights into software development activity.
""")

# Sidebar filters
st.sidebar.title("Analytics Controls")

# Organization filter
orgs = sorted(repos_df['org'].unique())
selected_org = st.sidebar.selectbox(
    "Organization", 
    orgs,
    help="Select a GitHub organization to analyze"
)

# Time period filter
min_date = commits_df['date'].min().date()
max_date = commits_df['date'].max().date()

time_filter = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    help="Filter commit data to a specific date range"
)

if len(time_filter) == 2:
    start_date, end_date = time_filter
    date_filtered_commits = commits_df[
        (commits_df['date'].dt.date >= start_date) & 
        (commits_df['date'].dt.date <= end_date)
    ]
else:
    start_date, end_date = min_date, max_date
    date_filtered_commits = commits_df

# Filter repos by selected organization
org_repos_df = repos_df[repos_df['org'] == selected_org]
repo_names = sorted(org_repos_df['repo_name'].unique())

st.sidebar.markdown("---")
st.sidebar.markdown("### Repository Selection")

# Select all button
all_repos_selected = st.sidebar.checkbox("Select All Repositories", value=True)

if all_repos_selected:
    selected_repos = repo_names
else:
    # Default to first 3 repos or all if fewer than 3
    default_repos = repo_names[:3] if len(repo_names) > 3 else repo_names
    selected_repos = st.sidebar.multiselect(
        "Select Repositories", 
        repo_names, 
        default=default_repos,
        help="Choose specific repositories to analyze"
    )

if not selected_repos:
    st.warning("Please select at least one repository.")
    st.stop()

# Additional filters in sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### Advanced Filters")

# Language filter - only show if we have language data
if 'language' in repos_df.columns:
    # Get list of languages used in the selected organization
    org_languages = repos_df[repos_df['org'] == selected_org]['language'].dropna().unique()
    
    if len(org_languages) > 0:
        languages = ['All'] + sorted(org_languages.tolist())
        selected_language = st.sidebar.selectbox("Programming Language", languages)
    else:
        selected_language = 'All'
        st.sidebar.info("No language data for selected organization")
else:
    selected_language = 'All'
    st.sidebar.info("Language data not available in repositories")

# Commit type filter if we have message analysis
has_patterns = all(col in commits_df.columns for col in ['feature', 'bug_fix', 'refactor', 'docs', 'test'])
if has_patterns:
    commit_types = ['All', 'Features', 'Bug Fixes', 'Refactoring', 'Documentation', 'Tests']
    selected_commit_type = st.sidebar.selectbox("Commit Type", commit_types)
else:
    selected_commit_type = 'All'

# Filter data based on selections
filtered_repos = repos_df[(repos_df['org'] == selected_org) & (repos_df['repo_name'].isin(selected_repos))]
filtered_commits = date_filtered_commits[
    (date_filtered_commits['org'] == selected_org) & 
    (date_filtered_commits['repo_name'].isin(selected_repos))
]

# Apply language filter if not 'All' and we have language data
if selected_language != 'All' and 'language' in repos_df.columns:
    language_repos = repos_df[(repos_df['org'] == selected_org) & 
                             (repos_df['language'] == selected_language)]['repo_name'].unique()
    
    # Only filter if we have repos with this language
    if len(language_repos) > 0:
        filtered_repos = filtered_repos[filtered_repos['language'] == selected_language]
        filtered_commits = filtered_commits[filtered_commits['repo_name'].isin(language_repos)]
    else:
        st.warning(f"No repositories found with language: {selected_language}")

# Apply commit type filter if not 'All'
if selected_commit_type != 'All' and has_patterns:
    filter_map = {
        'Features': 'feature',
        'Bug Fixes': 'bug_fix',
        'Refactoring': 'refactor',
        'Documentation': 'docs',
        'Tests': 'test'
    }
    if selected_commit_type in filter_map:
        filtered_commits = filtered_commits[filtered_commits[filter_map[selected_commit_type]] == True]

# Filter contributors data if available
if contributors_df is not None:
    filtered_contributors = contributors_df[
        (contributors_df['org'] == selected_org) & 
        (contributors_df['repo_name'].isin(selected_repos))
    ]
    
    # Apply language filter to contributors if applicable
    if selected_language != 'All' and 'language' in repos_df.columns and len(language_repos) > 0:
        filtered_contributors = filtered_contributors[filtered_contributors['repo_name'].isin(language_repos)]
else:
    filtered_contributors = None

# Top-level metrics
st.markdown("## Key Metrics")
st.markdown("""
<div class="chart-description">
These metrics provide a high-level overview of the selected repositories and their activity during the specified time period.
They help you quickly assess the scale and intensity of development efforts.
</div>
""", unsafe_allow_html=True)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-value">{len(selected_repos)}</div>', unsafe_allow_html=True)
    st.markdown('<div class="metric-label">Repositories</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    total_commits = len(filtered_commits)
    st.markdown(f'<div class="metric-value">{total_commits:,}</div>', unsafe_allow_html=True)
    st.markdown('<div class="metric-label">Total Commits</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    total_contributors = len(filtered_commits['author'].unique())
    st.markdown(f'<div class="metric-value">{total_contributors:,}</div>', unsafe_allow_html=True)
    st.markdown('<div class="metric-label">Unique Contributors</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col4:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    days_diff = max(1, (end_date - start_date).days)
    avg_commits_per_day = round(total_commits / days_diff, 1)
    st.markdown(f'<div class="metric-value">{avg_commits_per_day}</div>', unsafe_allow_html=True)
    st.markdown('<div class="metric-label">Commits/Day</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col5:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    if filtered_repos.empty or 'stars' not in filtered_repos.columns:
        total_stars = 0
    else:
        total_stars = filtered_repos['stars'].sum()
    st.markdown(f'<div class="metric-value">{total_stars:,}</div>', unsafe_allow_html=True)
    st.markdown('<div class="metric-label">Total Stars</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Create tabs for different visualizations
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💻 Commit Activity", 
    "📊 Repository Analysis", 
    "👨‍💻 Contributor Insights", 
    "🕒 Time Patterns",
    "📝 Commit Content"
])

# Tab 1: Commit Activity Over Time
with tab1:
    st.markdown('<div class="sub-header">Commit Activity Over Time</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="chart-description">
    This section reveals how development activity has changed over time. These visualizations help you identify:
    • Periods of high and low development activity
    • Project milestones and release cycles
    • Long-term trends in project maintenance
    • Seasonal patterns in development work
    </div>
    """, unsafe_allow_html=True)
    
    # Line chart of commits over time
    if not filtered_commits.empty:
        # Group commits by date
        commit_counts = filtered_commits.groupby([pd.Grouper(key='date', freq='D'), 'repo_name']).size().reset_index(name='count')
        
        st.markdown('<div class="chart-header">Daily Commit Activity</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="chart-description">
        <strong>What this shows:</strong> The number of commits per day for each repository. Spikes indicate periods of intensive development,
        while flat periods may represent code freezes, holidays, or reduced team capacity. This is useful for tracking when
        major development efforts occurred and when teams were most active.
        </div>
        """, unsafe_allow_html=True)
        
        # Create time series chart
        fig = px.line(commit_counts, x='date', y='count', color='repo_name',
                     title=f"Daily Commit Activity - {selected_org}",
                     labels={"date": "Date", "count": "Number of Commits", "repo_name": "Repository"})
        
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Number of Commits",
            legend_title="Repository",
            height=500,
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Add a moving average trend line
        st.markdown('<div class="chart-header">Commit Trends (7-Day Moving Average)</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="chart-description">
        <strong>What this shows:</strong> A smoothed version of commit activity that helps identify the underlying trends. The 7-day moving
        average filters out daily fluctuations (like weekends) to show the general direction of development effort. An
        upward trend indicates increasing development activity, while a downward trend suggests project wind-down or maturation.
        </div>
        """, unsafe_allow_html=True)
        
        # Calculate overall commit trend
        overall_commits = commit_counts.groupby('date')['count'].sum().reset_index()
        overall_commits.set_index('date', inplace=True)
        
        # Only calculate rolling average if we have enough data
        if len(overall_commits) >= 7:
            overall_commits['rolling_avg'] = overall_commits['count'].rolling(window=7).mean()
            
            # Plot the moving average
            fig2 = px.line(overall_commits.reset_index(), x='date', y=['count', 'rolling_avg'],
                          title="7-Day Moving Average of Commits",
                          labels={"date": "Date", "value": "Number of Commits", "variable": "Metric"},
                          color_discrete_map={"count": "lightgrey", "rolling_avg": "blue"})
            
            fig2.update_layout(
                xaxis_title="Date",
                yaxis_title="Commits",
                height=400,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            # Rename the legend items
            fig2.for_each_trace(lambda t: t.update(name = {
                "count": "Daily Commits",
                "rolling_avg": "7-Day Moving Average"
            }.get(t.name, t.name)))
            
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Not enough data points to calculate a 7-day moving average.")
        
        # Monthly commit activity chart
        st.markdown('<div class="chart-header">Monthly Development Activity</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="chart-description">
        <strong>What this shows:</strong> Commit activity aggregated by month, revealing longer-term development cycles and seasonal patterns.
        This view is particularly useful for identifying quarterly release cycles, seasonal development pushes, and how
        development resources are allocated throughout the year.
        </div>
        """, unsafe_allow_html=True)
        
        # Add month_year column for better grouping
        filtered_commits['month_year'] = filtered_commits['date'].dt.strftime('%Y-%m')
        
        # Group by month
        monthly_commits = filtered_commits.groupby(['month_year', 'repo_name']).size().reset_index(name='count')
        monthly_commits.columns = ['month', 'repo_name', 'count']
        
        fig3 = px.bar(monthly_commits, x='month', y='count', color='repo_name',
                    title=f"Monthly Commit Activity - {selected_org}",
                    labels={"month": "Month", "count": "Number of Commits", "repo_name": "Repository"},
                    barmode='group')
        
        fig3.update_layout(
            xaxis_title="Month",
            yaxis_title="Number of Commits",
            height=400,
            xaxis={'categoryorder':'category ascending'}
        )
        
        st.plotly_chart(fig3, use_container_width=True)
        
        # Cumulative commits over time
        st.markdown('<div class="chart-header">Cumulative Development Progress</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="chart-description">
        <strong>What this shows:</strong> The accumulated commit count over time, providing a clear visualization of the overall
        development momentum. Steeper slopes indicate periods of rapid development, while plateaus suggest reduced activity.
        This chart helps you see the growth trajectory of different repositories and identify when projects reach maturity
        or are being actively maintained.
        </div>
        """, unsafe_allow_html=True)
        
        # Create dataframe with cumulative commits
        cumulative_df = filtered_commits.sort_values('date')
        cumulative_df['cumulative_commits'] = cumulative_df.groupby('repo_name').cumcount() + 1
        
        # Group by date and repo for the chart
        cumulative_chart = cumulative_df.groupby(['date', 'repo_name'])['cumulative_commits'].max().reset_index()
        
        fig4 = px.line(cumulative_chart, x='date', y='cumulative_commits', color='repo_name',
                      title=f"Cumulative Commits Over Time - {selected_org}",
                      labels={"date": "Date", "cumulative_commits": "Total Commits", "repo_name": "Repository"})
        
        fig4.update_layout(
            xaxis_title="Date",
            yaxis_title="Cumulative Number of Commits",
            height=500
        )
        
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("No commit data available for the selected repositories.")

# Tab 2: Repository Analysis
with tab2:
    st.markdown('<div class="sub-header">Repository Statistics & Comparison</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="chart-description">
    This section compares different repositories and their characteristics. These visualizations help you understand:
    • Which repositories are most popular or actively maintained
    • The relative health and community engagement of different projects
    • Programming language distribution across the organization's portfolio
    • Historical development of the organization's codebase
    </div>
    """, unsafe_allow_html=True)
    
    # Repository comparison
    col1, col2 = st.columns(2)
    
    with col1:
        # Bar chart of stars per repository
        if not filtered_repos.empty and 'stars' in filtered_repos.columns:
            st.markdown('<div class="chart-header">Repository Popularity (Stars)</div>', unsafe_allow_html=True)
            st.markdown("""
            <div class="chart-description">
            <strong>What this shows:</strong> The number of stars each repository has received, which is a direct indicator of its
            popularity in the community. Stars often correlate with usefulness, quality, or novelty. Repositories with
            more stars typically have higher visibility and generate more interest from potential contributors.
            </div>
            """, unsafe_allow_html=True)
            
            stars_df = filtered_repos.sort_values('stars', ascending=False)
            stars_fig = px.bar(stars_df, x='repo_name', y='stars', 
                             title=f"Stars per Repository - {selected_org}",
                             labels={"repo_name": "Repository", "stars": "Stars"},
                             color='repo_name')
            
            stars_fig.update_layout(
                xaxis_title="Repository",
                yaxis_title="Number of Stars",
                height=400,
                showlegend=False
            )
            
            st.plotly_chart(stars_fig, use_container_width=True)
        else:
            st.info("No star data available for the repositories.")
    
    with col2:
        # Bar chart of forks per repository
        if not filtered_repos.empty and 'forks' in filtered_repos.columns:
            st.markdown('<div class="chart-header">Community Engagement (Forks)</div>', unsafe_allow_html=True)
            st.markdown("""
            <div class="chart-description">
            <strong>What this shows:</strong> The number of times each repository has been forked by other developers. Forks indicate
            active usage and modification of the code by the community. A high fork count suggests that many developers
            are building upon or adapting the codebase for their own needs, which is a strong indicator of project utility.
            </div>
            """, unsafe_allow_html=True)
            
            forks_df = filtered_repos.sort_values('forks', ascending=False)
            forks_fig = px.bar(forks_df, x='repo_name', y='forks', 
                              title=f"Forks per Repository - {selected_org}",
                              labels={"repo_name": "Repository", "forks": "Forks"},
                              color='repo_name')
            
            forks_fig.update_layout(
                xaxis_title="Repository",
                yaxis_title="Number of Forks",
                height=400,
                showlegend=False
            )
            
            st.plotly_chart(forks_fig, use_container_width=True)
        else:
            st.info("No fork data available for the repositories.")
    
    # Most active repositories
    st.markdown('<div class="chart-header">Development Activity by Repository</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="chart-description">
    <strong>What this shows:</strong> Repositories ranked by the number of commits they've received during the selected time period.
    This visualization reveals which projects are currently receiving the most development attention. High commit counts
    may indicate active development of new features, intensive bug fixing, or significant refactoring efforts. Note that
    commit volume alone doesn't necessarily indicate code quality or complexity.
    </div>
    """, unsafe_allow_html=True)
    
    if not filtered_commits.empty:
        # Count commits per repository
        repo_activity = filtered_commits.groupby('repo_name').size().reset_index(name='commit_count')
        repo_activity = repo_activity.sort_values('commit_count', ascending=False)
        
        fig = px.bar(repo_activity, x='repo_name', y='commit_count',
                   title=f"Repositories by Commit Activity - {selected_org}",
                   labels={"repo_name": "Repository", "commit_count": "Number of Commits"},
                   color='repo_name')
        
        fig.update_layout(
            xaxis_title="Repository",
            yaxis_title="Number of Commits",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Calculate commit density (commits per day) for each repository
        st.markdown('<div class="chart-header">Development Intensity (Commits per Day)</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="chart-description">
        <strong>What this shows:</strong> The average number of commits per day for each repository during the selected period.
        This normalizes the commit count by time, providing a measure of development intensity rather than just total activity.
        Repositories with high commit density are being actively and intensively developed, regardless of their age or total
        commit count.
        </div>
        """, unsafe_allow_html=True)
        
        # Calculate days of activity for each repo
        repo_days = {}
        for repo in repo_activity['repo_name']:
            repo_commits = filtered_commits[filtered_commits['repo_name'] == repo]
            if not repo_commits.empty:
                min_date = repo_commits['date'].min().date()
                max_date = repo_commits['date'].max().date()
                days = max(1, (max_date - min_date).days + 1)  # Add 1 to include both start and end dates
                repo_days[repo] = days
        
        # Calculate commit density
        repo_activity['active_days'] = repo_activity['repo_name'].map(repo_days)
        repo_activity['commits_per_day'] = repo_activity['commit_count'] / repo_activity['active_days']
        repo_activity = repo_activity.sort_values('commits_per_day', ascending=False)
        
        fig = px.bar(repo_activity, x='repo_name', y='commits_per_day',
                   title=f"Development Intensity - {selected_org}",
                   labels={"repo_name": "Repository", "commits_per_day": "Commits per Day"},
                   color='repo_name')
        
        fig.update_layout(
            xaxis_title="Repository",
            yaxis_title="Average Commits per Day",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No commit data available.")

    # Repository creation timeline
    st.markdown('<div class="chart-header">Repository Timeline</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="chart-description">
    <strong>What this shows:</strong> When each repository was created, showing the organization's project history over time.
    This timeline helps identify periods of expansion when many new projects were started, as well as revealing which
    repositories are newer or more established. The creation pattern can reveal organizational shifts in development
    priorities over time.
    </div>
    """, unsafe_allow_html=True)
    
    if not filtered_repos.empty:
        # Sort repositories by creation date
        timeline_data = filtered_repos[['repo_name', 'created_at']].sort_values('created_at')
        
        # Create a scatter plot for the timeline
        fig = px.scatter(timeline_data, x='created_at', y='repo_name',
                      title=f"Repository Creation Timeline - {selected_org}",
                      color='repo_name', size=[20] * len(timeline_data))
        
        fig.update_traces(marker=dict(symbol='diamond', opacity=0.8))
        fig.update_layout(
            xaxis_title="Creation Date",
            yaxis_title="Repository",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No repository creation data available.")
    
    # Programming languages
    if 'language' in filtered_repos.columns and not filtered_repos['language'].isna().all():
        st.markdown('<div class="chart-header">Technology Stack (Programming Languages)</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="chart-description">
        <strong>What this shows:</strong> The distribution of programming languages used across the selected repositories.
        This chart reveals the technical stack and expertise of the organization. A diverse set of languages may indicate
        a versatile team or a microservices architecture, while a focused distribution suggests specialization in particular
        technologies.
        </div>
        """, unsafe_allow_html=True)
        
        # Count languages and replace NaN with "Unknown"
        filtered_repos['language'] = filtered_repos['language'].fillna("Unknown")
        language_counts = filtered_repos['language'].value_counts().reset_index()
        language_counts.columns = ['language', 'count']
        
        if not language_counts.empty:
            fig = px.pie(language_counts, values='count', names='language',
                       title=f"Programming Languages Used - {selected_org}")
            
            fig.update_layout(height=400)
            fig.update_traces(textposition='inside', textinfo='percent+label')
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No language data available for the selected repositories.")

# Tab 3: Contributor Insights
with tab3:
    st.markdown('<div class="sub-header">Contributor Analysis</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="chart-description">
    This section explores the human side of development. These visualizations help you understand:
    • Who contributes most frequently to the codebase
    • How contributor activity changes over time
    • The distribution of contributors across different repositories
    • The balance between core team members and occasional contributors
    </div>
    """, unsafe_allow_html=True)
    
    if not filtered_commits.empty:
        # Get top contributors based on commit count
        st.markdown('<div class="chart-header">Top Contributors</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="chart-description">
        <strong>What this shows:</strong> The most active contributors ranked by their total number of commits. This helps identify
        the core development team and key maintainers of the projects. A balanced distribution suggests a healthy collaborative
        environment, while a top-heavy distribution might indicate knowledge concentration or maintenance by a small core team.
        </div>
        """, unsafe_allow_html=True)
        
        top_contributors = filtered_commits['author'].value_counts().reset_index()
        top_contributors.columns = ['author', 'commits']
        top_contributors = top_contributors.head(20)
        
        fig = px.bar(top_contributors, x='author', y='commits',
                   title=f"Top 20 Contributors by Commit Count - {selected_org}",
                   labels={"author": "Contributor", "commits": "Number of Commits"},
                   color='commits', color_continuous_scale=px.colors.sequential.Viridis)
        
        fig.update_layout(
            xaxis_title="Contributor",
            yaxis_title="Number of Commits",
            xaxis={'categoryorder':'total descending'},
            height=500,
            xaxis_tickangle=-45
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Contribution distribution analysis
        st.markdown('<div class="chart-header">Contribution Distribution</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="chart-description">
        <strong>What this shows:</strong> How evenly distributed the contributions are across all contributors. This chart helps
        identify whether development is primarily driven by a small core team or distributed across many contributors.
        A steep curve indicates that a small number of contributors make most of the commits, while a flatter curve
        suggests more balanced participation.
        </div>
        """, unsafe_allow_html=True)
        
        # Calculate cumulative percentage of commits
        all_contributors = filtered_commits['author'].value_counts().reset_index()
        all_contributors.columns = ['author', 'commits']
        all_contributors = all_contributors.sort_values('commits', ascending=False)
        
        all_contributors['cum_commits'] = all_contributors['commits'].cumsum()
        all_contributors['percent_total'] = 100 * all_contributors['cum_commits'] / all_contributors['commits'].sum()
        all_contributors['contributor_rank'] = range(1, len(all_contributors) + 1)
        all_contributors['contributor_percentile'] = 100 * all_contributors['contributor_rank'] / len(all_contributors)
        
        # Create Pareto chart
        fig = px.line(all_contributors, x='contributor_percentile', y='percent_total',
                     title="Contribution Distribution (Pareto Analysis)",
                     labels={'contributor_percentile': 'Percentage of Contributors', 
                             'percent_total': 'Percentage of Total Commits'})
        
        # Add reference line for equal distribution
        x = np.linspace(0, 100, 100)
        y = x  # Perfect equality line
        fig.add_trace(go.Scatter(x=x, y=y, mode='lines', name='Equal Distribution',
                                line=dict(color='red', dash='dash')))
        
        # Add annotation for 80/20 rule if applicable
        if len(all_contributors) > 5:
            try:
                # Find point closest to 20% of contributors
                idx_20pct = (all_contributors['contributor_percentile'] - 20).abs().idxmin()
                pct_at_20 = all_contributors.loc[idx_20pct, 'percent_total']
                
                fig.add_annotation(
                    x=20, y=pct_at_20,
                    text=f"Top 20% of contributors<br>make {pct_at_20:.0f}% of commits",
                    showarrow=True,
                    arrowhead=1
                )
            except:
                pass
        
        fig.update_layout(
            xaxis_title="Percentage of Contributors",
            yaxis_title="Percentage of Total Commits",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Contributor activity over time
        st.markdown('<div class="chart-header">Contributor Activity Over Time</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="chart-description">
        <strong>What this shows:</strong> How the activity of top contributors changes over time. This visualization helps track when
        specific contributors joined or left projects, their periods of most intense activity, and how the overall team
        composition has evolved. Changes in the pattern may indicate team rotation, shifting priorities, or changes in project
        leadership.
        </div>
        """, unsafe_allow_html=True)
        
        # Get top 5 contributors for time series
        top5_contributors = top_contributors.head(5)['author'].tolist()
        top5_activity = filtered_commits[filtered_commits['author'].isin(top5_contributors)]
        
        if not top5_activity.empty:
            # Group by date and author
            activity_ts = top5_activity.groupby([pd.Grouper(key='date', freq='W'), 'author']).size().reset_index(name='commits')
            
            fig = px.line(activity_ts, x='date', y='commits', color='author',
                        title=f"Weekly Commit Activity of Top 5 Contributors - {selected_org}",
                        labels={"date": "Date", "commits": "Number of Commits", "author": "Contributor"})
            
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Number of Commits",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough contributor data available for time series.")
        
        # Contributor distribution per repository
        st.markdown('<div class="chart-header">Contributors per Repository</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="chart-description">
        <strong>What this shows:</strong> How many unique contributors have worked on each repository. This metric is a key
        indicator of community engagement and the "bus factor" of a project (how many people would need to be unavailable 
        before a project stalls). Repositories with many contributors often have broader ownership and knowledge sharing.
        </div>
        """, unsafe_allow_html=True)
        
        # Count unique contributors per repository
        contributors_per_repo = filtered_commits.groupby('repo_name')['author'].nunique().reset_index()
        contributors_per_repo.columns = ['repo_name', 'contributor_count']
        contributors_per_repo = contributors_per_repo.sort_values('contributor_count', ascending=False)
        
        fig = px.bar(contributors_per_repo, x='repo_name', y='contributor_count',
                    title=f"Number of Unique Contributors per Repository - {selected_org}",
                    labels={"repo_name": "Repository", "contributor_count": "Number of Contributors"},
                    color='repo_name')
        
        fig.update_layout(
            xaxis_title="Repository",
            yaxis_title="Number of Contributors",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Contributor overlap across repositories
        if len(selected_repos) > 1:
            st.markdown('<div class="chart-header">Contributor Overlap Between Repositories</div>', unsafe_allow_html=True)
            st.markdown("""
            <div class="chart-description">
            <strong>What this shows:</strong> How many contributors work on multiple repositories. A high overlap indicates knowledge 
            sharing and cross-pollination between projects, while low overlap suggests specialized teams focused on individual
            repositories. This metric helps understand the organization's team structure and potential for knowledge transfer.
            </div>
            """, unsafe_allow_html=True)
            
            # Create a matrix of contributors by repo
            contributors_by_repo = {}
            for repo in selected_repos:
                repo_commits = filtered_commits[filtered_commits['repo_name'] == repo]
                contributors_by_repo[repo] = set(repo_commits['author'].unique())
            
            # Calculate overlap matrix
            overlap_matrix = []
            for repo1 in selected_repos:
                row = []
                for repo2 in selected_repos:
                    if repo1 == repo2:
                        # Diagonal shows total contributors for that repo
                        row.append(len(contributors_by_repo[repo1]))
                    else:
                        # Off-diagonal shows overlap
                        overlap = len(contributors_by_repo[repo1].intersection(contributors_by_repo[repo2]))
                        row.append(overlap)
                overlap_matrix.append(row)
            
            # Create heatmap
            fig = go.Figure(data=go.Heatmap(
                z=overlap_matrix,
                x=selected_repos,
                y=selected_repos,
                colorscale='Viridis',
                text=overlap_matrix,
                texttemplate="%{text}",
                textfont={"size":12},
                hovertemplate='%{y} ∩ %{x}: %{z} contributors<extra></extra>'
            ))
            
            fig.update_layout(
                title=f"Contributor Overlap Between Repositories - {selected_org}",
                height=500,
                xaxis_title="Repository",
                yaxis_title="Repository"
            )
            
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No contributor data available.")

# Tab 4: Time Patterns
with tab4:
    st.markdown('<div class="sub-header">Development Time Patterns</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="chart-description">
    This section reveals when development happens. These visualizations help you understand:
    • Weekly development patterns and work schedules
    • Daily cycles of development activity
    • Geographic distribution of the development team
    • Balance between weekday and weekend development
    </div>
    """, unsafe_allow_html=True)
    
    if not filtered_commits.empty:
        # Extract day of week and hour of day if not already in the data
        filtered_commits['day_of_week'] = filtered_commits['date'].dt.day_name()
        filtered_commits['hour_of_day'] = filtered_commits['date'].dt.hour
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Activity by day of week
            st.markdown('<div class="chart-header">Development Activity by Day of Week</div>', unsafe_allow_html=True)
            st.markdown("""
            <div class="chart-description">
            <strong>What this shows:</strong> The distribution of commits across different days of the week. This pattern reveals
            the work schedule of the development team. A concentration on weekdays suggests a professional team working
            standard business hours, while significant weekend activity might indicate hobbyist contributors, global
            distribution, or occasional sprints/hackathons.
            </div>
            """, unsafe_allow_html=True)
            
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            day_counts = filtered_commits['day_of_week'].value_counts().reindex(day_order).reset_index()
            day_counts.columns = ['day', 'commits']
            
            fig = px.bar(day_counts, x='day', y='commits',
                       title=f"Commits by Day of Week - {selected_org}",
                       labels={"day": "Day", "commits": "Number of Commits"},
                       color='day')
            
            # Calculate percentage of weekday vs weekend
            weekday_mask = filtered_commits['day_of_week'].isin(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'])
            weekday_commits = weekday_mask.sum()
            weekend_commits = (~weekday_mask).sum()
            weekday_pct = 100 * weekday_commits / (weekday_commits + weekend_commits)
            
            fig.update_layout(
                xaxis_title="Day of Week",
                yaxis_title="Number of Commits",
                height=400,
                annotations=[
                    dict(
                        text=f"Weekday: {weekday_pct:.1f}%, Weekend: {100-weekday_pct:.1f}%",
                        x=0.5,
                        y=1.05,
                        xref="paper",
                        yref="paper",
                        showarrow=False,
                        font=dict(size=12)
                    )
                ]
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Activity by hour of day
            st.markdown('<div class="chart-header">Development Activity by Hour of Day</div>', unsafe_allow_html=True)
            st.markdown("""
            <div class="chart-description">
            <strong>What this shows:</strong> The distribution of commits across different hours of the day (in UTC). This pattern
            reveals the working hours of the development team and can indicate geographic distribution. Peaks during standard
            business hours in a specific time zone suggest localized teams, while a more distributed pattern might indicate
            global contributors or developers with flexible work schedules.
            </div>
            """, unsafe_allow_html=True)
            
            hour_counts = filtered_commits['hour_of_day'].value_counts().sort_index().reset_index()
            hour_counts.columns = ['hour', 'commits']
            
            # Calculate business hours vs non-business hours (simplified)
            # Assume 9am-5pm is business hours in some standard time zone
            business_mask = filtered_commits['hour_of_day'].between(9, 17)
            business_commits = business_mask.sum()
            nonbusiness_commits = (~business_mask).sum()
            business_pct = 100 * business_commits / (business_commits + nonbusiness_commits)
            
            fig = px.bar(hour_counts, x='hour', y='commits',
                       title=f"Commits by Hour of Day - {selected_org} (UTC)",
                       labels={"hour": "Hour (UTC)", "commits": "Number of Commits"},
                       color='commits', color_continuous_scale=px.colors.sequential.Viridis)
            
            fig.update_layout(
                xaxis_title="Hour of Day (UTC)",
                yaxis_title="Number of Commits",
                height=400,
                annotations=[
                    dict(
                        text=f"9am-5pm: {business_pct:.1f}%, Other hours: {100-business_pct:.1f}%",
                        x=0.5,
                        y=1.05,
                        xref="paper",
                        yref="paper",
                        showarrow=False,
                        font=dict(size=12)
                    )
                ]
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Heatmap of commit activity by day and hour
        st.markdown('<div class="chart-header">Development Activity Heatmap</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="chart-description">
        <strong>What this shows:</strong> A comprehensive view of development patterns combining both day of week and hour of day.
        This heatmap reveals when the team is most active and can help identify core working hours, global distribution,
        and unique work patterns. Dark areas indicate peak development times, while lighter areas show periods of reduced
        activity. This information can be valuable for scheduling meetings, planning releases, or understanding team dynamics.
        </div>
        """, unsafe_allow_html=True)
        
        # Create a pivot table for the heatmap
        pivot_data = filtered_commits.groupby(['day_of_week', 'hour_of_day']).size().reset_index(name='count')
        pivot_table = pivot_data.pivot_table(values='count', index='day_of_week', columns='hour_of_day', fill_value=0)
        
        # Reorder days to start with Monday
        if set(day_order).issubset(set(pivot_table.index)):
            pivot_table = pivot_table.reindex(day_order)
        
        # Create the heatmap
        fig = go.Figure(data=go.Heatmap(
            z=pivot_table.values,
            x=[f"{h}:00" for h in range(24)],
            y=pivot_table.index,
            colorscale='Viridis',
            hovertemplate='Day: %{y}<br>Hour: %{x}<br>Commits: %{z}<extra></extra>'
        ))
        
        fig.update_layout(
            title=f"Commit Activity Heatmap - {selected_org}",
            xaxis_title="Hour of Day (UTC)",
            yaxis_title="Day of Week",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No time pattern data available.")

# Tab 5: Commit Content
with tab5:
    st.markdown('<div class="sub-header">Commit Content Analysis</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="chart-description">
    This section analyzes the content and nature of commits. These visualizations help you understand:
    • The types of development work being done (features, bug fixes, refactoring)
    • Common patterns in commit messages
    • How development focus changes over time
    • The balance between different types of work
    </div>
    """, unsafe_allow_html=True)
    
    if not filtered_commits.empty and 'message' in filtered_commits.columns:
        # Check if we have pattern columns from analysis
        has_patterns = all(col in filtered_commits.columns for col in ['feature', 'bug_fix', 'refactor'])
        
        if has_patterns:
            # Commit types breakdown
            st.markdown('<div class="chart-header">Development Focus (Commit Types)</div>', unsafe_allow_html=True)
            st.markdown("""
            <div class="chart-description">
            <strong>What this shows:</strong> The distribution of different types of development work based on commit message analysis.
            This chart helps understand what kind of work is prioritized in the project - whether the focus is on adding new
            features, fixing bugs, improving documentation, or refactoring existing code. The balance between these activities
            provides insights into project maturity and health.
            </div>
            """, unsafe_allow_html=True)
            
            # Count commit types
            commit_types = {
                'Features': filtered_commits['feature'].sum(),
                'Bug Fixes': filtered_commits['bug_fix'].sum(),
                'Refactoring': filtered_commits['refactor'].sum(),
                'Documentation': filtered_commits['docs'].sum(),
                'Tests': filtered_commits['test'].sum(),
                'Style Changes': filtered_commits['style'].sum(),
                'Merges': filtered_commits['merge'].sum()
            }
            
            # Some commits might match multiple patterns or none
            # Count commits that don't match any pattern
            no_match = len(filtered_commits[~(
                filtered_commits['feature'] | 
                filtered_commits['bug_fix'] | 
                filtered_commits['refactor'] | 
                filtered_commits['docs'] | 
                filtered_commits['test'] | 
                filtered_commits['style'] | 
                filtered_commits['merge']
            )])
            
            commit_types['Other/Unclassified'] = no_match
            
            # Create dataframe for plotting
            commit_types_df = pd.DataFrame({
                'type': list(commit_types.keys()),
                'count': list(commit_types.values())
            }).sort_values('count', ascending=False)
            
            fig = px.bar(commit_types_df, x='type', y='count',
                       title=f"Commit Types - {selected_org}",
                       labels={"type": "Commit Type", "count": "Number of Commits"},
                       color='type')
            
            fig.update_layout(
                xaxis_title="Commit Type",
                yaxis_title="Number of Commits",
                height=400,
                xaxis={'categoryorder':'total descending'}
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Commit type trends over time
            st.markdown('<div class="chart-header">Development Focus Over Time</div>', unsafe_allow_html=True)
            st.markdown("""
            <div class="chart-description">
            <strong>What this shows:</strong> How the focus of development changes over time. This visualization reveals how priorities
            shift throughout the project lifecycle - for example, from initial feature development to bug fixing and maintenance.
            These patterns can help identify development phases and predict future needs based on historical trends.
            </div>
            """, unsafe_allow_html=True)
            
            # Group by month and count commit types
            filtered_commits['month_year'] = filtered_commits['date'].dt.strftime('%Y-%m')
            
            # Calculate monthly counts for each type
            monthly_types = []
            for month in sorted(filtered_commits['month_year'].unique()):
                month_commits = filtered_commits[filtered_commits['month_year'] == month]
                for commit_type, column in [
                    ('Features', 'feature'), 
                    ('Bug Fixes', 'bug_fix'),
                    ('Refactoring', 'refactor'),
                    ('Documentation', 'docs')
                ]:
                    monthly_types.append({
                        'month': month,
                        'type': commit_type,
                        'count': month_commits[column].sum()
                    })
            
            types_df = pd.DataFrame(monthly_types)
            
            if not types_df.empty:
                fig = px.line(types_df, x='month', y='count', color='type',
                            title=f"Development Focus Trends - {selected_org}",
                            labels={"month": "Month", "count": "Number of Commits", "type": "Commit Type"})
                
                fig.update_layout(
                    xaxis_title="Month",
                    yaxis_title="Number of Commits",
                    height=400,
                    xaxis={'categoryorder':'category ascending'}
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Not enough data for monthly trends analysis.")
            
            # Commit type distribution by repository
            st.markdown('<div class="chart-header">Development Focus by Repository</div>', unsafe_allow_html=True)
            st.markdown("""
            <div class="chart-description">
            <strong>What this shows:</strong> How different repositories focus on different types of development work. This
            comparison reveals which repositories are in active feature development versus maintenance mode, which ones
            require the most bug fixing, and which have a focus on code quality (refactoring and tests). These differences
            can help understand the lifecycle stage and health of each project.
            </div>
            """, unsafe_allow_html=True)
            
            # Calculate proportions for each repository
            repo_focus = []
            for repo in selected_repos:
                repo_commits = filtered_commits[filtered_commits['repo_name'] == repo]
                if len(repo_commits) > 0:
                    total = len(repo_commits)
                    for commit_type, column in [
                        ('Features', 'feature'), 
                        ('Bug Fixes', 'bug_fix'),
                        ('Refactoring', 'refactor'),
                        ('Documentation', 'docs')
                    ]:
                        count = repo_commits[column].sum()
                        proportion = 100 * count / total
                        repo_focus.append({
                            'repository': repo,
                            'type': commit_type,
                            'proportion': proportion
                        })
            
            repo_focus_df = pd.DataFrame(repo_focus)
            
            if not repo_focus_df.empty:
                fig = px.bar(repo_focus_df, x='repository', y='proportion', color='type', barmode='group',
                           title=f"Development Focus by Repository - {selected_org}",
                           labels={"repository": "Repository", "proportion": "Percentage of Commits", "type": "Commit Type"})
                
                fig.update_layout(
                    xaxis_title="Repository",
                    yaxis_title="Percentage of Commits",
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Not enough data for repository focus analysis.")
        
        # Display sample of recent commit messages
        st.markdown('<div class="chart-header">Recent Commit Messages</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="chart-description">
        <strong>What this shows:</strong> The most recent commit messages from the selected repositories, providing a snapshot
        of current development activities. These messages help understand what the team is currently working on and the
        latest changes to the codebase.
        </div>
        """, unsafe_allow_html=True)
        
        recent_commits = filtered_commits.sort_values('date', ascending=False).head(10)[['date', 'repo_name', 'author', 'message']]
        
        for idx, commit in recent_commits.iterrows():
            with st.expander(f"{commit['date'].strftime('%Y-%m-%d %H:%M')} - {commit['repo_name']}"):
                st.write(f"**Author:** {commit['author']}")
                st.write(f"**Message:** {commit['message']}")
    else:
        st.info("No commit message data available for content analysis.")

# Footer with summary insights
st.markdown('<div class="sub-header">Summary Insights</div>', unsafe_allow_html=True)
st.markdown("""
<div class="chart-description">
Key findings from the data analysis, highlighting the most active components and patterns. These insights
provide a quick overview of the development activity to help understand focus areas and patterns.
</div>
""", unsafe_allow_html=True)

if not filtered_commits.empty:
    # Create two columns of insights
    insight_col1, insight_col2 = st.columns(2)
    
    with insight_col1:
        # Most active repository
        most_active_repo = filtered_commits['repo_name'].value_counts().idxmax()
        most_active_repo_commits = filtered_commits['repo_name'].value_counts().max()
        most_active_pct = 100 * most_active_repo_commits / len(filtered_commits)
        
        st.markdown(f"""
        <div class="insight-box">
            <div class="insight-title">Most Active Repository</div>
            <div class="insight-value">{most_active_repo}</div>
            <p>{most_active_repo_commits:,} commits ({most_active_pct:.1f}% of total)</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Most prolific contributor
        most_active_contributor = filtered_commits['author'].value_counts().idxmax()
        most_active_contributor_commits = filtered_commits['author'].value_counts().max()
        contributor_pct = 100 * most_active_contributor_commits / len(filtered_commits)
        
        st.markdown(f"""
        <div class="insight-box">
            <div class="insight-title">Most Active Contributor</div>
            <div class="insight-value">{most_active_contributor}</div>
            <p>{most_active_contributor_commits:,} commits ({contributor_pct:.1f}% of total)</p>
        </div>
        """, unsafe_allow_html=True)
    
    with insight_col2:
        # Most active day
        day_activity = filtered_commits['day_of_week'].value_counts()
        most_active_day = day_activity.idxmax()
        most_active_day_commits = day_activity.max()
        day_pct = 100 * most_active_day_commits / len(filtered_commits)
        
        st.markdown(f"""
        <div class="insight-box">
            <div class="insight-title">Most Active Day of Week</div>
            <div class="insight-value">{most_active_day}</div>
            <p>{most_active_day_commits:,} commits ({day_pct:.1f}% of total)</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Most active hour
        hour_activity = filtered_commits['hour_of_day'].value_counts()
        most_active_hour = hour_activity.idxmax()
        most_active_hour_commits = hour_activity.max()
        hour_pct = 100 * most_active_hour_commits / len(filtered_commits)
        
        st.markdown(f"""
        <div class="insight-box">
            <div class="insight-title">Most Active Hour of Day (UTC)</div>
            <div class="insight-value">{most_active_hour}:00</div>
            <p>{most_active_hour_commits:,} commits ({hour_pct:.1f}% of total)</p>
        </div>
        """, unsafe_allow_html=True)

# Credits and final notes
st.markdown("---")
st.markdown("GitHub Analytics Dashboard | Data fetched using GitHub API")
