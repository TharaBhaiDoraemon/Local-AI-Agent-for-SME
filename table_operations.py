"""
Module for handling table operations, joins, and intelligent data analysis.
This module provides functionality to join CSV tables, perform queries, and generate downloadable results.
"""
import pandas as pd
import re
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from io import StringIO
import json

class TableOperations:
    """
    Class to handle table operations including joins and queries
    """
    
    def __init__(self, attachments_dir: str = "attachments"):
        self.attachments_dir = Path(attachments_dir)
        self.tables = {}
        self.load_csv_tables()
    
    def load_csv_tables(self):
        """
        Load all CSV files from the attachments directory into DataFrames
        """
        for file_path in self.attachments_dir.glob("*.csv"):
            try:
                df = pd.read_csv(file_path)
                table_name = file_path.stem  # Use filename without extension as table name
                self.tables[table_name] = {
                    'dataframe': df,
                    'file_path': str(file_path)
                }
                print(f"Loaded table '{table_name}' with {len(df)} rows and {len(df.columns)} columns")
            except Exception as e:
                print(f"Error loading CSV file {file_path}: {e}")
    
    def get_table_names(self) -> List[str]:
        """
        Get all available table names
        """
        return list(self.tables.keys())
    
    def get_column_names(self, table_name: str) -> List[str]:
        """
        Get column names for a specific table
        """
        if table_name in self.tables:
            return list(self.tables[table_name]['dataframe'].columns)
        return []
    
    def find_matching_tables(self, query: str) -> List[str]:
        """
        Find tables that might be relevant based on the query
        """
        query_lower = query.lower()
        matching_tables = []
        
        for table_name in self.tables:
            # Check if table name is in query
            if table_name.lower() in query_lower:
                matching_tables.append(table_name)
                continue
                
            # Check if any column names are in query
            for col in self.tables[table_name]['dataframe'].columns:
                if col.lower() in query_lower:
                    matching_tables.append(table_name)
                    break
        
        # If no tables found, return all tables (for general queries)
        if not matching_tables:
            return list(self.tables.keys())
        
        return matching_tables
    
    def extract_table_names_from_query(self, query: str) -> List[str]:
        """
        Extract potential table names from the query using various patterns
        """
        query_lower = query.lower()
        found_tables = []
        
        # Look for patterns like "table1 and table2", "table1 with table2", "compare table1 and table2"
        for table_name in self.tables:
            table_lower = table_name.lower()
            # Check if table name is in query (with word boundaries to avoid partial matches)
            if re.search(r'\b' + re.escape(table_lower) + r'\b', query_lower):
                found_tables.append(table_name)
                continue
                
            # Check if any column names are in query
            for col in self.tables[table_name]['dataframe'].columns:
                if re.search(r'\b' + re.escape(col.lower()) + r'\b', query_lower):
                    found_tables.append(table_name)
                    break
        
        # Additional pattern matching for common table operation expressions
        patterns = [
            r"join\s+(\w+)",  # "join table_name"
            r"compare\s+(\w+)\s+and\s+(\w+)",  # "compare table1 and table2"
            r"(\w+)\s+(and|with|vs|versus)\s+(\w+)",  # "table1 and table2", "table1 with table2", "table1 vs table2"
            r"(\w+)\s*(?:\s+|,\s*)(\w+)(?:\s+|,\s*)(\w+)",  # "table1 table2 table3" or "table1, table2, table3"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, query_lower)
            for match in matches:
                for item in match:
                    # If it's a tuple (from multiple groups), extract individual items
                    if isinstance(item, tuple):
                        for sub_item in item:
                            clean_item = sub_item.strip('\'".,!?;').lower()
                            # Find table that matches this item
                            for table_name in self.tables:
                                if table_name.lower() == clean_item:
                                    if table_name not in found_tables:
                                        found_tables.append(table_name)
                                    break
                    else:
                        clean_item = item.strip('\'".,!?;').lower()
                        # Find table that matches this item
                        for table_name in self.tables:
                            if table_name.lower() == clean_item:
                                if table_name not in found_tables:
                                    found_tables.append(table_name)
                                break
        
        # Remove duplicates while preserving order
        unique_tables = []
        for table in found_tables:
            if table not in unique_tables:
                unique_tables.append(table)
        
        return unique_tables

    def detect_join_intent(self, query: str) -> bool:
        """
        Detect if the user wants to join tables based on the query
        """
        query_lower = query.lower()
        
        # Keywords that indicate a join operation
        join_keywords = [
            'join', 'merge', 'combine', 'together', 'with', 'and', 'compare',
            'between', 'vs', 'versus', 'against', 'alongside', 'relate'
        ]
        
        # Check for join-related keywords
        for keyword in join_keywords:
            if keyword in query_lower:
                return True
        
        # Check for patterns that suggest joining
        join_patterns = [
            r'join\s+\w+\s+with\s+\w+',  # "join table1 with table2"
            r'compare\s+\w+\s+and\s+\w+',  # "compare table1 and table2"
            r'\w+\s+(and|with|vs|versus)\s+\w+',  # "table1 and table2", "table1 with table2"
        ]
        
        for pattern in join_patterns:
            if re.search(pattern, query_lower):
                return True
        
        # Check for comparison words with multiple potential table names
        comparison_words = ['compare', 'difference', 'between', 'versus', 'vs']
        for word in comparison_words:
            if word in query_lower:
                # Check if multiple tables are mentioned
                tables_in_query = self.extract_table_names_from_query(query)
                if len(tables_in_query) >= 2:
                    return True
        
        return False
    
    def detect_filter_intent(self, query: str) -> bool:
        """
        Detect if the user wants to filter a table based on the query
        """
        query_lower = query.lower()
        
        # Keywords that indicate a filter operation
        filter_keywords = [
            'filter', 'where', 'with', 'between', 'greater than', 'less than',
            'more than', 'above', 'below', 'under', 'over', 'from', 'to',
            'is', 'are', 'has', 'have', 'contain', 'contains', 'listing',
            'list', 'show', 'find', 'get', 'retrieve', 'songs', 'records'
        ]
        
        # Check for filter-related keywords
        for keyword in filter_keywords:
            if keyword in query_lower:
                # Check if specific range is mentioned
                if 'between' in query_lower:
                    # Check if it follows the pattern "between X and Y"
                    range_pattern = r'between\s+\d+(?:\.\d+)?\s+and\s+\d+(?:\.\d+)?'
                    if re.search(range_pattern, query_lower):
                        return True
                
                # Check for range operators
                if any(op in query_lower for op in ['>', '<', '>=', '<=', 'greater than', 'less than', 'more than', 'above', 'below', 'under', 'over']):
                    return True
        
        # Check for patterns that suggest filtering
        filter_patterns = [
            r'list\s+\w+\s+where',  # "list items where"
            r'show\s+\w+\s+with',   # "show items with"
            r'find\s+\w+\s+between', # "find items between"
            r'list.*views.*between', # "list songs with views between"
        ]
        
        for pattern in filter_patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return True
        
        return False
    
    def identify_join_columns(self, table1: str, table2: str) -> Optional[str]:
        """
        Identify potential column names that could be used for joining two tables
        """
        df1 = self.tables[table1]['dataframe']
        df2 = self.tables[table2]['dataframe']
        
        # Find common column names
        common_cols = set(df1.columns) & set(df2.columns)
        if common_cols:
            # Return the first common column as a potential join key
            return list(common_cols)[0]
        
        # Look for potential foreign key relationships (e.g., id, name)
        potential_keys = ['id', 'name', 'date', 'category', 'code']
        for key in potential_keys:
            if key in df1.columns and key in df2.columns:
                return key
        
        # Look for columns with similar names
        for col1 in df1.columns:
            for col2 in df2.columns:
                if col1.lower() == col2.lower():
                    return col1
        
        return None
    
    def perform_join(self, table1: str, table2: str, join_column: str, join_type: str = 'inner') -> pd.DataFrame:
        """
        Perform a join operation between two tables
        """
        if table1 not in self.tables or table2 not in self.tables:
            raise ValueError(f"One or both tables '{table1}', '{table2}' not found")
        
        df1 = self.tables[table1]['dataframe']
        df2 = self.tables[table2]['dataframe']
        
        # Check if the join column exists in both DataFrames
        if join_column not in df1.columns or join_column not in df2.columns:
            raise ValueError(f"Join column '{join_column}' not found in both tables")
        
        # Perform the join
        result_df = pd.merge(df1, df2, on=join_column, how=join_type, suffixes=('', '_right'))
        
        return result_df
    
    def find_comparable_columns(self, table1: str, table2: str) -> List[str]:
        """
        Find columns that can be compared between two tables (same data type if possible)
        """
        df1 = self.tables[table1]['dataframe']
        df2 = self.tables[table2]['dataframe']
        
        comparable_cols = []
        
        # Find columns with the same name
        common_cols = set(df1.columns) & set(df2.columns)
        
        for col in common_cols:
            # Check if both columns have compatible data types
            if df1[col].dtype == df2[col].dtype:
                comparable_cols.append(col)
        
        return comparable_cols
    
    def extract_comparison_request(self, query: str) -> Dict[str, Any]:
        """
        Extract comparison request details from the query
        """
        query_lower = query.lower()
        
        # Look for aggregation requests (sum, average, etc.)
        aggregation = None
        if 'sum' in query_lower:
            aggregation = 'sum'
        elif 'average' in query_lower or 'mean' in query_lower:
            aggregation = 'mean'
        elif 'count' in query_lower:
            aggregation = 'count'
        elif 'max' in query_lower:
            aggregation = 'max'
        elif 'min' in query_lower:
            aggregation = 'min'
        
        # Look for comparison between years or time periods
        years = re.findall(r'\b(20\d{2})\b', query)
        months = re.findall(r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\b', query_lower)
        
        # Look for range filters (e.g., between 100 and 10000)
        range_pattern = r'between\s+(\d+(?:\.\d+)?)\s+and\s+(\d+(?:\.\d+)?)'
        range_match = re.search(range_pattern, query_lower)
        range_values = None
        if range_match:
            range_values = (float(range_match.group(1)), float(range_match.group(2)))
        
        # Look for column names to filter on
        # This is a simplified approach - in a real implementation you'd want more sophisticated NLP
        column_indicators = ['where', 'with', 'having', 'filter']
        filter_column = None
        for indicator in column_indicators:
            if indicator in query_lower:
                # Extract what comes after the indicator
                parts = query_lower.split(indicator)
                if len(parts) > 1:
                    after_indicator = parts[1].strip()
                    # Look for column names in the tables
                    for table_name in self.tables:
                        for col in self.tables[table_name]['dataframe'].columns:
                            if col.lower() in after_indicator:
                                filter_column = col
                                break
                        if filter_column:
                            break
                break
        
        return {
            'aggregation': aggregation,
            'years': years,
            'months': months,
            'range_values': range_values,
            'filter_column': filter_column
        }
    
    def execute_query(self, query: str) -> Dict[str, Any]:
        """
        Execute a query on the loaded tables
        """
        # Determine if this is primarily a join operation
        is_join_intent = self.detect_join_intent(query)
        is_filter_intent = self.detect_filter_intent(query)
        
        # Find relevant tables from the query
        table_names = self.extract_table_names_from_query(query)
        
        if not table_names:
            return {
                'status': 'error',
                'message': 'No tables found relevant to the query',
                'result': None
            }
        
        try:
            if len(table_names) == 1:
                # Single table operation
                table_name = table_names[0]
                df = self.tables[table_name]['dataframe']
                
                # Check if it's a filter operation
                filter_request = self.extract_comparison_request(query)
                
                if filter_request['range_values']:
                    # Apply range filter
                    if filter_request['filter_column']:
                        col = filter_request['filter_column']
                        if col in df.columns:
                            min_val, max_val = filter_request['range_values']
                            filtered_df = df[(df[col] >= min_val) & (df[col] <= max_val)]
                            return {
                                'status': 'success',
                                'message': f'Filtered table {table_name} based on {col} between {min_val} and {max_val}',
                                'result': filtered_df,
                                'type': 'filter'
                            }
                        else:
                            # Try to find similar column names
                            similar_cols = [c for c in df.columns if filter_request['filter_column'].lower() in c.lower()]
                            if similar_cols:
                                col = similar_cols[0]
                                min_val, max_val = filter_request['range_values']
                                filtered_df = df[(df[col] >= min_val) & (df[col] <= max_val)]
                                return {
                                    'status': 'success',
                                    'message': f'Filtered table {table_name} based on {col} (similar to {filter_request["filter_column"]}) between {min_val} and {max_val}',
                                    'result': filtered_df,
                                    'type': 'filter'
                                }
                            else:
                                return {
                                    'status': 'error',
                                    'message': f'Column {filter_request["filter_column"]} not found in table {table_name}',
                                    'result': None
                                }
                    else:
                        # If no specific column mentioned, try to use common numeric columns
                        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                        if numeric_cols:
                            col = numeric_cols[0]  # Use first numeric column
                            min_val, max_val = filter_request['range_values']
                            filtered_df = df[(df[col] >= min_val) & (df[col] <= max_val)]
                            return {
                                'status': 'success',
                                'message': f'Filtered table {table_name} based on {col} between {min_val} and {max_val}',
                                'result': filtered_df,
                                'type': 'filter'
                            }
                
                # Return the full table if no specific operation requested
                return {
                    'status': 'success',
                    'message': f'Retrieved table {table_name}',
                    'result': df,
                    'type': 'full_table'
                }
            
            elif len(table_names) >= 2:
                # Multiple table operation (join or comparison)
                table1, table2 = table_names[0], table_names[1]
                
                # Check first if this is a filter operation (more specific than join)
                is_filter_intent = self.detect_filter_intent(query)
                
                if is_filter_intent:
                    # Handle filter operations first
                    filter_request = self.extract_comparison_request(query)
                    if filter_request['range_values']:
                        # Find the most appropriate table for filtering
                        table_name = table_names[0]  # Use first table, or find the most relevant one
                        df = self.tables[table_name]['dataframe']
                        
                        # If no specific column mentioned, try to find one based on the query
                        if not filter_request['filter_column']:
                            # Look for columns that might match the context (e.g. "views" if the query mentions views)
                            possible_cols = []
                            query_lower = query.lower()
                            
                            for col in df.columns:
                                col_lower = col.lower()
                                # If the column name is mentioned in the query or sounds related
                                if any(keyword in col_lower for keyword in ['view', 'play', 'stream', 'count', 'rating', 'score', 'size']):
                                    possible_cols.append(col)
                            
                            if possible_cols:
                                filter_request['filter_column'] = possible_cols[0]
                            else:
                                # Use first numeric column as fallback
                                numeric_cols = df.select_dtypes(include=['number']).columns
                                if len(numeric_cols) > 0:
                                    filter_request['filter_column'] = numeric_cols[0]
                        
                        if filter_request['filter_column'] and filter_request['filter_column'] in df.columns:
                            min_val, max_val = filter_request['range_values']
                            filtered_df = df[(df[filter_request['filter_column']] >= min_val) & 
                                         (df[filter_request['filter_column']] <= max_val)]
                            
                            return {
                                'status': 'success',
                                'message': f'Filtered {table_name} for records with {filter_request["filter_column"]} between {min_val} and {max_val}',
                                'result': filtered_df,
                                'type': 'filter'
                            }
                
                # Now check if user wants aggregation of comparable columns (like sum comparison)
                comparison_request = self.extract_comparison_request(query)
                
                if comparison_request['aggregation']:
                    # Check if this is a comparison between years or specific tables (like yt_data_2023 and yt_data_2024)
                    if comparison_request['years']:
                        # Handle year comparison (e.g., "compare yt_data_2023 and yt_data_2024 sum")
                        year_tables = [t for t in table_names if any(year in t for year in comparison_request['years'])]
                        if len(year_tables) >= 2:
                            # Compare based on years in table names
                            result_data = {}
                            agg = comparison_request['aggregation']
                            
                            for table_name in year_tables:
                                df = self.tables[table_name]['dataframe']
                                numeric_df = df.select_dtypes(include=['number'])
                                if not numeric_df.empty:
                                    if agg == 'sum':
                                        agg_result = numeric_df.sum()
                                    elif agg == 'mean':
                                        agg_result = numeric_df.mean()
                                    elif agg == 'count':
                                        agg_result = numeric_df.count()
                                    elif agg == 'max':
                                        agg_result = numeric_df.max()
                                    elif agg == 'min':
                                        agg_result = numeric_df.min()
                                    else:
                                        continue  # Skip if unknown aggregation
                                    
                                    # Only include numeric results (skip strings that can't be aggregated)
                                    for col in agg_result.index:
                                        # Check if the original column in the dataframe is numeric
                                        if pd.api.types.is_numeric_dtype(df[col]):
                                            try:
                                                float(agg_result[col])  # Try to convert to number
                                                result_data[f'{table_name}_{col}'] = [agg_result[col]]
                                            except (ValueError, TypeError):
                                                # Skip non-numeric results
                                                continue
                            
                            if result_data:
                                result_df = pd.DataFrame(result_data)
                                return {
                                    'status': 'success',
                                    'message': f'Aggregated comparison of tables {year_tables} by {agg}',
                                    'result': result_df,
                                    'type': 'yearly_comparison'
                                }
                    
                    # Check for comparable columns and apply aggregation
                    comparable_cols = self.find_comparable_columns(table1, table2)
                    if comparable_cols:
                        # Only use numeric columns for aggregation
                        numeric_comparable_cols = []
                        for col in comparable_cols:
                            df1 = self.tables[table1]['dataframe']
                            df2 = self.tables[table2]['dataframe']
                            if pd.api.types.is_numeric_dtype(df1[col]) and pd.api.types.is_numeric_dtype(df2[col]):
                                numeric_comparable_cols.append(col)
                        
                        if numeric_comparable_cols:
                            result_data = {}
                            agg = comparison_request['aggregation']
                            
                            for col in numeric_comparable_cols:
                                df1_col = self.tables[table1]['dataframe'][col]
                                df2_col = self.tables[table2]['dataframe'][col]
                                
                                if agg == 'sum':
                                    result_data[f'{table1}_{col}'] = [df1_col.sum()]
                                    result_data[f'{table2}_{col}'] = [df2_col.sum()]
                                elif agg == 'mean':
                                    result_data[f'{table1}_{col}'] = [df1_col.mean()]
                                    result_data[f'{table2}_{col}'] = [df2_col.mean()]
                                elif agg == 'count':
                                    result_data[f'{table1}_{col}'] = [df1_col.count()]
                                    result_data[f'{table2}_{col}'] = [df2_col.count()]
                                elif agg == 'max':
                                    result_data[f'{table1}_{col}'] = [df1_col.max()]
                                    result_data[f'{table2}_{col}'] = [df2_col.max()]
                                elif agg == 'min':
                                    result_data[f'{table1}_{col}'] = [df1_col.min()]
                                    result_data[f'{table2}_{col}'] = [df2_col.min()]
                            
                            if result_data:
                                result_df = pd.DataFrame(result_data)
                                return {
                                    'status': 'success',
                                    'message': f'Comparison of {table1} and {table2} by {agg}',
                                    'result': result_df,
                                    'type': 'comparison'
                                }
                
                # If it's a join intent, proceed with joining
                if is_join_intent:
                    # Try to find a join column
                    join_column = self.identify_join_columns(table1, table2)
                    
                    if join_column:
                        # Perform join
                        result_df = self.perform_join(table1, table2, join_column)
                        
                        if comparison_request['aggregation']:
                            agg = comparison_request['aggregation']
                            # Apply aggregation to numeric columns
                            numeric_df = result_df.select_dtypes(include=['number'])
                            if not numeric_df.empty:
                                if agg == 'sum':
                                    agg_result = numeric_df.sum()
                                elif agg == 'mean':
                                    agg_result = numeric_df.mean()
                                elif agg == 'count':
                                    agg_result = numeric_df.count()
                                elif agg == 'max':
                                    agg_result = numeric_df.max()
                                elif agg == 'min':
                                    agg_result = numeric_df.min()
                                else:
                                    agg_result = numeric_df  # Default to no aggregation
                            
                                return {
                                    'status': 'success',
                                    'message': f'Joined {table1} and {table2} on {join_column}, aggregated by {agg}',
                                    'result': pd.DataFrame(agg_result).T,  # Transpose to make it a proper DataFrame
                                    'type': 'aggregated_join'
                                }
                        
                        return {
                            'status': 'success',
                            'message': f'Joined {table1} and {table2} on {join_column}',
                            'result': result_df,
                            'type': 'join'
                        }
                    else:
                        return {
                            'status': 'error',
                            'message': f'Cannot join {table1} and {table2}, no common join column found',
                            'result': None
                        }
                
                # If not a join intent but multiple tables, return comparison of aggregations
                else:
                    # Return both tables separately if no clear operation
                    df1 = self.tables[table1]['dataframe']
                    df2 = self.tables[table2]['dataframe']
                    
                    return {
                        'status': 'success',
                        'message': f'Found tables {table1} and {table2} (no join requested)',
                        'result': {'table1': df1, 'table2': df2},
                        'type': 'multiple_tables'
                    }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error executing query: {str(e)}',
                'result': None
            }
    
    def export_result_to_csv(self, result_df: pd.DataFrame) -> str:
        """
        Export a DataFrame to CSV format and return as string
        """
        buffer = StringIO()
        result_df.to_csv(buffer, index=False)
        csv_string = buffer.getvalue()
        buffer.close()
        return csv_string

    def save_result_as_downloadable_file(self, result_df: pd.DataFrame, filename: str = None) -> str:
        """
        Save a DataFrame as a CSV file in the downloads directory for user download
        """
        import tempfile
        from pathlib import Path
        
        # Create a downloads directory if it doesn't exist
        downloads_dir = Path("downloads")
        downloads_dir.mkdir(exist_ok=True)
        
        # Generate filename if not provided
        if filename is None:
            import time
            timestamp = int(time.time())
            filename = f"query_result_{timestamp}.csv"
        
        # Ensure the filename has a .csv extension
        if not filename.lower().endswith('.csv'):
            filename += '.csv'
        
        file_path = downloads_dir / filename
        
        # Save the DataFrame to CSV
        result_df.to_csv(file_path, index=False)
        
        return str(file_path)

# Global instance for use in other modules
table_ops = TableOperations()