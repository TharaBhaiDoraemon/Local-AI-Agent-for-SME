"""
Test script for table operations functionality
"""
import pandas as pd
from table_operations import table_ops

# Create sample test data for demonstration
def create_sample_data():
    # Create sample CSV files for testing
    data1 = {
        'id': [1, 2, 3, 4, 5],
        'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
        'views_2023': [1000, 2000, 1500, 3000, 2500]
    }
    
    data2 = {
        'id': [1, 2, 3, 4, 5],
        'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
        'views_2024': [1200, 1800, 2000, 2800, 3000]
    }
    
    df1 = pd.DataFrame(data1)
    df2 = pd.DataFrame(data2)
    
    # Save to CSV files in attachments directory
    df1.to_csv('attachments/yt_data_2023.csv', index=False)
    df2.to_csv('attachments/yt_data_2024.csv', index=False)
    
    print("Sample CSV files created:")
    print("- yt_data_2023.csv")
    print("- yt_data_2024.csv")
    print("Each with columns: id, name, and year-specific views")

def test_table_operations():
    # Refresh the table operations with new test data
    table_ops.load_csv_tables()
    
    print("\nAvailable tables:", table_ops.get_table_names())
    
    # Test 1: Simple table preview
    print("\n--- Test 1: Table Preview ---")
    preview_2023 = table_ops.tables.get('yt_data_2023', {}).get('dataframe', pd.DataFrame())
    if not preview_2023.empty:
        print("yt_data_2023 preview (first 3 rows):")
        print(preview_2023.head(3))
    
    # Test 2: Query to join and compare
    print("\n--- Test 2: Join and Compare Query ---")
    query_result = table_ops.execute_query("compare yt_data_2023 and yt_data_2024 sum")
    print(f"Query result status: {query_result['status']}")
    print(f"Message: {query_result['message']}")
    print(f"Type: {query_result.get('type', 'unknown')}")
    if query_result['result'] is not None and isinstance(query_result['result'], pd.DataFrame):
        print("Result DataFrame:")
        print(query_result['result'])
    
    # Test 3: Another query to list with range filter
    print("\n--- Test 3: Filter Query ---")
    filter_result = table_ops.execute_query("list yt_data_2023 where views_2023 between 1000 and 2500")
    print(f"Filter query result status: {filter_result['status']}")
    print(f"Message: {filter_result['message']}")
    if filter_result['result'] is not None and isinstance(filter_result['result'], pd.DataFrame):
        print("Filtered DataFrame:")
        print(filter_result['result'])
    
    # Test 4: Save result as downloadable file
    print("\n--- Test 4: Downloadable Result ---")
    if query_result['result'] is not None and isinstance(query_result['result'], pd.DataFrame):
        file_path = table_ops.save_result_as_downloadable_file(query_result['result'], 'test_comparison.csv')
        print(f"Downloadable file saved at: {file_path}")
    
    print("\n--- All tests completed ---")

if __name__ == "__main__":
    create_sample_data()
    test_table_operations()