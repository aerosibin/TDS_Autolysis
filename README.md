# TDS Autolysis: Automated Data Science Analysis Pipeline

## Overview
This is a powerful Python-based data analysis tool designed to automate comprehensive exploratory data analysis (EDA) for CSV datasets. The script performs a robust, multi-faceted analysis that transforms raw data into actionable insights through statistical computations, visualization, and AI-powered narrative generation.

## Key Features

### 1. Robust Data Loading
- Supports multiple file encodings
- Intelligent encoding detection
- Handles various CSV file formats

### 2. Comprehensive Data Analysis
- Structural analysis of datasets
- Statistical summaries
- Outlier detection
- Correlation matrix generation
- Clustering analysis

### 3. Advanced Visualizations
- Correlation heatmap
- Outlier boxplots
- Scatter plots for numeric columns
- Cluster analysis visualization (PCA)

### 4. AI-Powered Insights
- Generates a narrative summary using OpenAI's language model
- Translates complex statistical findings into human-readable insights
- Provides potential implications and recommendations

## Technical Components
- Uses pandas for data manipulation
- Leverages scikit-learn for advanced analytics
- Incorporates matplotlib and seaborn for visualization
- Utilizes K-means clustering and PCA
- Implements AI-assisted summarization

## Use Cases
- Rapid exploratory data analysis
- Quick insights generation
- Data preprocessing and understanding
- Research and academic data analysis
- Business intelligence workflows

## Usage
```bash
uv run autolyis.py your_dataset.set or python autolysis.py your_dataset.csv 
```

Generates:
- README.md with narrative insights
- Visualization images
- Detailed statistical report
