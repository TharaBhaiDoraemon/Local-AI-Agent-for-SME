"""
Test script for specific use cases mentioned in the requirements
"""
import pandas as pd
from table_operations import table_ops

# Create sample data that matches the examples given
def create_demo_data():
    # Create sample data similar to yt_data_2023 and yt_data_2024
    yt_2023 = {
        'song_id': [1, 2, 3, 4, 5],
        'song_name': ['Song A', 'Song B', 'Song C', 'Song D', 'Song E'],
        'views': [1500, 800, 12000, 4500, 200],
        'artist': ['Artist 1', 'Artist 2', 'Artist 3', 'Artist 4', 'Artist 5']
    }
    
    yt_2024 = {
        'song_id': [1, 2, 3, 4, 5],
        'song_name': ['Song A', 'Song B', 'Song C', 'Song D', 'Song E'],
        'views': [2000, 1200, 15000, 5000, 400],
        'artist': ['Artist 1', 'Artist 2', 'Artist 3', 'Artist 4', 'Artist 5']
    }
    
    df_2023 = pd.DataFrame(yt_2023)
    df_2024 = pd.DataFrame(yt_2024)
    
    # Save to CSV files in attachments directory
    df_2023.to_csv('attachments/yt_data_2023.csv', index=False)
    df_2024.to_csv('attachments/yt_data_2024.csv', index=False)
    
    print("Demo CSV files created with song data:")
    print("- yt_data_2023.csv (5 songs with views)")
    print("- yt_data_2024.csv (5 songs with views)")
    
    # Create a different table for testing view filtering
    songs_data = {
        'song_id': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'song_name': [f'Song {i}' for i in range(1, 11)],
        'views': [50, 200, 500, 1000, 5000, 10000, 15000, 50000, 8000, 150],
        'artist': [f'Artist {i}' for i in range(1, 11)]
    }
    
    songs_df = pd.DataFrame(songs_data)
    songs_df.to_csv('attachments/songs_data.csv', index=False)
    print("- songs_data.csv (10 songs with various view counts)")

def test_use_cases():
    # Reload tables with updated demo data
    table_ops.load_csv_tables()
    
    print("\nAvailable tables:", table_ops.get_table_names())
    
    # Test Case 1: "fetch yt_data_2023 and yt_data_2024 comparison of its sum"
    print("\n--- Test Case 1: Yearly Data Comparison ---")
    print("Query: 'compare yt_data_2023 and yt_data_2024 sum'")
    result1 = table_ops.execute_query("compare yt_data_2023 and yt_data_2024 sum")
    print(f"Status: {result1['status']}")
    print(f"Message: {result1['message']}")
    print(f"Type: {result1.get('type', 'unknown')}")
    if result1['result'] is not None and isinstance(result1['result'], pd.DataFrame):
        print("Result:")
        print(result1['result'])
        # Save this result for download
        file_path = table_ops.save_result_as_downloadable_file(result1['result'], 'yearly_comparison.csv')
        print(f"Downloadable result saved as: {file_path}")
    
    # Test Case 2: "list songs streamed which have views between 100 and 10000"
    print("\n--- Test Case 2: Filter Songs by View Range ---")
    print("Query: 'list songs which have views between 100 and 10000'")
    result2 = table_ops.execute_query("list songs which have views between 100 and 10000")
    print(f"Status: {result2['status']}")
    print(f"Message: {result2['message']}")
    if result2['result'] is not None and isinstance(result2['result'], pd.DataFrame):
        print("Filtered Songs:")
        print(result2['result'])
        # Save this result for download
        file_path = table_ops.save_result_as_downloadable_file(result2['result'], 'filtered_songs.csv')
        print(f"Downloadable result saved as: {file_path}")
    
    # Additional test: Join functionality
    print("\n--- Test Case 3: Join Tables (if possible) ---")
    print("Query: 'join yt_data_2023 and yt_data_2024 on song_id'")
    result3 = table_ops.execute_query("join yt_data_2023 and yt_data_2024 on song_id")
    print(f"Status: {result3['status']}")
    print(f"Message: {result3['message']}")
    if result3['result'] is not None and isinstance(result3['result'], pd.DataFrame):
        print("Joined Data:")
        print(result3['result'].head())
        # Save this result for download
        file_path = table_ops.save_result_as_downloadable_file(result3['result'], 'joined_data.csv')
        print(f"Downloadable result saved as: {file_path}")
    
    # Additional test: Different aggregation
    print("\n--- Test Case 4: Average Comparison ---")
    print("Query: 'compare yt_data_2023 and yt_data_2024 average'")
    result4 = table_ops.execute_query("compare yt_data_2023 and yt_data_2024 average")
    print(f"Status: {result4['status']}")
    print(f"Message: {result4['message']}")
    if result4['result'] is not None and isinstance(result4['result'], pd.DataFrame):
        print("Average Comparison:")
        print(result4['result'])
    
    print("\n--- All use case tests completed ---")

if __name__ == "__main__":
    create_demo_data()
    test_use_cases()