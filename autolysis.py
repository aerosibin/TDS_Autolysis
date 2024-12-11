import os
import sys
import csv
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import json
import requests
import chardet
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer

def detect_file_encoding(filename):
    """
    Detect the file encoding using chardet
    """
    with open(filename, 'rb') as rawdata:
        result = chardet.detect(rawdata.read(10000))
    return result['encoding']

def load_csv(filename):
    """
    Load CSV file with robust encoding detection and handling
    """
    # List of encodings to try
    encodings_to_try = [
        'utf-8', 
        'iso-8859-1', 
        'latin1', 
        'cp1252', 
        'utf-16',
    ]

    # First, try to detect encoding
    detected_encoding = detect_file_encoding(filename)
    encodings_to_try.insert(0, detected_encoding)

    # Remove duplicates while preserving order
    encodings_to_try = list(dict.fromkeys(encodings_to_try))

    # Try different encodings
    for encoding in encodings_to_try:
        try:
            df = pd.read_csv(filename, encoding=encoding, encoding_errors='replace')
            print(f"Successfully loaded file using {encoding} encoding")
            return df
        except Exception as e:
            print(f"Failed to load with {encoding} encoding: {e}")
    
    # If all attempts fail
    raise ValueError(f"Could not load CSV file {filename} with any of the attempted encodings")

def json_serialize_handler(obj):
    """
    Custom JSON serialization handler for non-standard types
    """
    if isinstance(obj, (np.integer, np.floating)):
        return int(obj) if isinstance(obj, np.integer) else float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif hasattr(obj, 'dtype'):
        return str(obj.dtype)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def analyze_data_structure(df):
    """
    Perform basic structural analysis of the dataset
    """
    # Replace problematic characters in column names
    df.columns = df.columns.str.encode('ascii', 'ignore').str.decode('ascii')
    
    analysis = {
        "num_rows": len(df),
        "num_columns": len(df.columns),
        "column_types": {col: str(df[col].dtype) for col in df.columns},
        "missing_values": df.isnull().sum().to_dict(),
        "unique_values": {col: df[col].nunique() for col in df.columns}
    }
    return analysis

def compute_statistical_summaries(df):
    """
    Compute statistical summaries for numeric columns
    """
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    summary = df[numeric_columns].describe().to_dict()
    
    # Correlation matrix for numeric columns
    correlation_matrix = df[numeric_columns].corr()
    
    return {
        "summary_statistics": summary,
        "correlation_matrix": correlation_matrix
    }

def visualize_correlation_matrix(correlation_matrix):
    """
    Create a heatmap visualization of the correlation matrix
    """
    plt.figure(figsize=(10, 8))
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0)
    plt.title("Correlation Heatmap")
    plt.tight_layout()
    plt.savefig('correlation_heatmap.png',dpi=512/8)
    

    plt.close()

def detect_outliers(df):
    """
    Detect outliers using IQR method for numeric columns
    """
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    outliers = {}
    
    for column in numeric_columns:
        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        column_outliers = df[(df[column] < lower_bound) | (df[column] > upper_bound)]
        if len(column_outliers) > 0:
            outliers[column] = {
                "total_outliers": len(column_outliers),
                "percentage": (len(column_outliers) / len(df)) * 100,
                "lower_bound": float(lower_bound),
                "upper_bound": float(upper_bound)
            }
    
    return outliers


def plot_outliers(df, outliers):
    """
    Create box plots for columns with outliers
    """
    if not outliers:
        return
    
    plt.figure(figsize=(16, 6))  # Wider figure
    columns_to_plot = list(outliers.keys())
    for i, column in enumerate(columns_to_plot, 1):
        plt.subplot(1, len(columns_to_plot), i)
        sns.boxplot(data=df, y=column)
        plt.title(f'Outliers in {column}', fontsize=10)
        plt.ylabel(column, fontsize=8)
    
    plt.tight_layout(pad=1.0, w_pad=0.5, h_pad=1.0)  # Adjust layout parameters
    plt.savefig('outliers_boxplot.png', dpi=512/8)
    plt.close()

def create_scatter_plots(df):
    """
    Create scatter plots for numeric column pairs
    """
    # Select numeric columns
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    
    # Create scatter plots for all numeric column pairs
    plt.figure(figsize=(15, 10))
    plot_count = 0
    
    for i in range(len(numeric_columns)):
        for j in range(i+1, len(numeric_columns)):
            plot_count += 1
            plt.subplot(3, 3, plot_count)
            plt.scatter(df[numeric_columns[i]], df[numeric_columns[j]], alpha=0.5)
            plt.xlabel(numeric_columns[i])
            plt.ylabel(numeric_columns[j])
            plt.title(f'{numeric_columns[i]} vs {numeric_columns[j]}')
            
            if plot_count >= 9:
                break
        
        if plot_count >= 9:
            break
    
    plt.tight_layout()
    plt.savefig('scatter_plots.png', dpi=512/8, bbox_inches='tight')
    plt.close()


def print_missing_values_report(df):
    """
    Print a detailed report of missing values
    """
    print("\n--- Missing Values Report ---")
    missing_values = df.isnull().sum()
    missing_percentages = 100 * df.isnull().sum() / len(df)
    missing_table = pd.concat([missing_values, missing_percentages], axis=1, keys=['Missing Values', 'Percentage'])
    print(missing_table[missing_table['Missing Values'] > 0])
    print("-----------------------------\n")


def perform_cluster_analysis(df):
    """
    Perform K-means clustering on numeric columns with robust NaN handling
    """
    # Select numeric columns
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    
    # Prepare data for clustering
    X = df[numeric_columns]
    
    # Print missing values report
    print_missing_values_report(X)
    
    # Impute missing values with median strategy
    imputer = SimpleImputer(strategy='median')
    X_imputed = imputer.fit_transform(X)
    
    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_imputed)
    
    # Perform PCA for visualization
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)
    
    # Perform K-means clustering
    kmeans = KMeans(n_clusters=3, random_state=42)
    clusters = kmeans.fit_predict(X_scaled)
    
    # Visualize clusters
    plt.figure(figsize=(10, 6))
    scatter = plt.scatter(X_pca[:, 0], X_pca[:, 1], c=clusters, cmap='viridis', alpha=0.7)
    plt.title('Cluster Analysis (PCA Visualization)')
    plt.xlabel('First Principal Component')
    plt.ylabel('Second Principal Component')
    plt.colorbar(scatter, label='Cluster')
    
    plt.tight_layout()
    plt.savefig('cluster_analysis.png', dpi=512/8, bbox_inches='tight')
    plt.close()
    
    return clusters


def generate_llm_summary(data_summary, outliers, correlation_summary, df, clusters):
    """
    Use OpenAI to generate a narrative summary of the analysis via the AI Proxy endpoint
    """
    AIPROXY_TOKEN = os.environ.get("AIPROXY_TOKEN")
    
    # Check if token is set
    if not AIPROXY_TOKEN:
        raise ValueError("AIPROXY_TOKEN environment variable is not set. Please set it before running the script.")
    BASE_URL = "http://aiproxy.sanand.workers.dev/openai/v1/chat/completions"

    # Use custom JSON serialization to handle non-standard types
    try:
        correlation_str = json.dumps(
            correlation_summary['correlation_matrix'], 
            indent=2, 
            default=json_serialize_handler
        )[:1000]
    except Exception as e:
        correlation_str = f"Error serializing correlation matrix: {e}"
        # Prepare a concise summary of key dataset characteristics

    column_summary = {
        "columns": list(df.columns),
        "numeric_columns": list(df.select_dtypes(include=[np.number]).columns),
        "total_rows": len(df),
        "unique_clusters": len(set(clusters))
    }
    
    # Compute missing value percentages
    missing_percentages = 100 * df.isnull().sum() / len(df)
    missing_columns = missing_percentages[missing_percentages > 0]
    
    # Sample a few rows to give context
    sample_rows = df.head(3).to_dict(orient='records')
    
    # Define the prompt
    prompt = f"""
    Analyze the following dataset summary:
    Data Structure:
    - Total Rows: {column_summary['total_rows']}
    - Columns: {', '.join(column_summary['columns'])}
    - Numeric Columns: {', '.join(column_summary['numeric_columns'])}
    - Number of Clusters Identified: {column_summary['unique_clusters']}
    {json.dumps(data_summary, indent=2, default=json_serialize_handler)}

    Outliers:
    {json.dumps(outliers, indent=2, default=json_serialize_handler)}

    Correlation Summary:
    {correlation_str}

    Missing Data Columns:
    {json.dumps({str(col): f"{pct:.2f}%" for col, pct in missing_columns.items()}, indent=2)}

    Sample Data:
    {json.dumps(sample_rows, indent=2)}

    Please provide a brief, insightful narrative about:    
    1. Describes the data briefly and analysis you carried out
    2. Highlights key insights from the analysis
    3. Suggests potential implications or actions based on the findings (i.e. what to do with the insights)
    4. Use a storytelling approach that makes the data come alive
    5. Keep it concise, under 500 words
    6. Potential patterns or relationships in the data
    7. Significance of the identified clusters
    """

    # Define headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AIPROXY_TOKEN}"
    }

    # Define the request payload
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}]
    }

    # Send the request to the AI Proxy
    try:
        response = requests.post(BASE_URL, headers=headers, json=data)
        response.raise_for_status()
        return response.json().get("choices")[0].get("message").get("content")
    except requests.exceptions.RequestException as e:
        return f"Error generating summary: {e}"


def main():
    
    if len(sys.argv) != 2:
        print("Usage: python autolysis.py <csv_filename>")
        sys.exit(1)
    
    filename = sys.argv[1]
    
    # Load and analyze data
    df = load_csv(filename)
    data_summary = analyze_data_structure(df)
    statistical_summary = compute_statistical_summaries(df)
    outliers = detect_outliers(df)
    
    # Create visualizations
    visualize_correlation_matrix(statistical_summary['correlation_matrix'])
    plot_outliers(df, outliers)
    create_scatter_plots(df)  
    clusters = perform_cluster_analysis(df)
    
    # Generate narrative summary
    narrative = generate_llm_summary(
        data_summary, 
        outliers, 
        statistical_summary,
        df,
        clusters
    )
    
    # Write README.md
    with open('README.md', 'w') as f:
        f.write(narrative)
        f.write("\n\n## Visualizations\n")
        f.write("![Correlation Heatmap](correlation_heatmap.png)\n")
        if outliers:
            f.write("![Outliers Boxplot](outliers_boxplot.png)\n")
        f.write("![Scatter Plots](scatter_plots.png)\n")
        f.write("![Cluster Analysis](cluster_analysis.png)\n")
        
        

if __name__ == "__main__":
    main()