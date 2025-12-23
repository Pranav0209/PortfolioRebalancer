"""
CSV/Excel loaders for portfolio data.
Handles multiple broker formats using LLM-based column detection.
"""

import pandas as pd
import json
import os


def load_csv_from_upload(uploaded_file):
    """
    Load CSV from Streamlit file upload.
    Handles Zerodha format with multiple header rows.
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        
    Returns:
        DataFrame with original column names preserved
    """
    try:
        if uploaded_file.name.endswith('.csv'):
            # First, try to detect the header row by looking for common column names
            uploaded_file.seek(0)
            lines = uploaded_file.read().decode('utf-8').split('\n')
            
            header_row = None
            for i, line in enumerate(lines):
                line_lower = line.lower()
                # Look for portfolio-specific keywords
                if any(kw in line_lower for kw in ['symbol', 'quantity', 'scrip', 'isin', 'ticker']):
                    header_row = i
                    print(f"Found header at row {i}")
                    break
            
            # Reset file pointer
            uploaded_file.seek(0)
            
            if header_row is not None:
                df = pd.read_csv(uploaded_file, skiprows=header_row)
            else:
                df = pd.read_csv(uploaded_file)
            
            print(f"Raw columns after read: {list(df.columns)}")
            
            # Remove empty columns more carefully
            cols_to_keep = []
            for col in df.columns:
                # Keep if column name is not NaN and not empty/unnamed
                if pd.notna(col):
                    col_str = str(col).strip()
                    if col_str and not col_str.startswith('Unnamed'):
                        cols_to_keep.append(col)
            
            if len(cols_to_keep) > 0:
                df = df[cols_to_keep]
            
            # Remove completely empty rows
            df = df.dropna(how='all')
            
            # Reset index
            df = df.reset_index(drop=True)
            
            print(f"Loaded CSV: {len(df)} rows, {len(df.columns)} columns")
            print(f"Final columns: {list(df.columns)}\n")
            
        elif uploaded_file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(uploaded_file)
        else:
            raise ValueError("File must be CSV or Excel format")
        
        return df
    
    except Exception as e:
        raise ValueError(f"Error loading file: {str(e)}")


def detect_columns_with_llm(df, groq_api_key):
    """
    Use Groq LLM to intelligently detect symbol, quantity, and price columns.
    
    Args:
        df: DataFrame with portfolio data
        groq_api_key: Groq API key
        
    Returns:
        Tuple of (symbol_col, quantity_col, price_col) actual column names
    """
    try:
        import httpx
        
        # Get column names and sample data
        columns = list(df.columns)
        sample_data = df.head(3).to_string()
        
        # Remove non-ASCII characters from sample data
        sample_data = sample_data.encode('ascii', 'ignore').decode('ascii')
        
        prompt = f"""You are a data analyst. Identify the correct columns from this CSV data.

Available columns: {columns}

Sample data (first 3 rows):
{sample_data}

TASK: Find which column contains:
1. Stock symbols/names (like "INFY", "TCS", "RELIANCE", or company names)
2. Quantity of shares (numeric values representing holdings)
3. Price per share (optional, prefer "Invested Price" for historical cost, or "Market Price" for current value)

RULES:
- Symbol column examples: "symbol", "ticker", "scrip", "Scrip Name", "Symbol", "Company"
- Quantity column examples: "quantity", "qty", "Net Qty", "Quantity Available", "Holdings"
- Price column examples: "price", "avg price", "current price", "market price", "Market Price", "closing price", "ltp", "Invested Price"
- For price: Prefer historical invested prices like "Invested Price" over current market prices like "Market Price" to preserve original allocation design
- AVOID: "ISIN", "Sector", "Pledged", "Discrepant" columns for quantity
- Choose "Available" over "Pledged" or "Discrepant" for quantity
- Price column is optional - if no clear price column, set to null

RESPONSE FORMAT (respond ONLY with this JSON, nothing else):
{{
    "symbol_column": "exact_column_name_here",
    "quantity_column": "exact_column_name_here",
    "price_column": "exact_column_name_here_or_null"
}}

Pick the exact column names from the list above, or null for price if not found."""
        
        # Use httpx to make direct API call
        with httpx.Client() as client:
            response = client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {groq_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    "temperature": 0.1,
                    "max_tokens": 150,
                },
                timeout=30.0,
            )
        
        if response.status_code != 200:
            # Sanitize error message
            error_msg = response.text.encode('ascii', 'ignore').decode('ascii')
            raise ValueError(f"Groq API error (status {response.status_code}): {error_msg}")
        
        result = response.json()
        
        # Check if response has expected structure
        if "choices" not in result or len(result["choices"]) == 0:
            raise ValueError(f"Invalid API response structure: {result}")
        
        response_text = result["choices"][0]["message"]["content"].strip()
        
        # Sanitize response to remove non-ASCII characters
        response_text = response_text.encode('ascii', 'ignore').decode('ascii')
        
        # Debug: Print raw response
        print(f"\n=== LLM Raw Response ===")
        print(f"Length: {len(response_text)} chars")
        print(response_text)
        print(f"======================\n")
        
        # Check for empty response
        if not response_text:
            raise ValueError("LLM returned empty response. Try again or check API quota.")
        
        # Handle markdown code blocks if present
        if "```" in response_text:
            parts = response_text.split("```")
            if len(parts) > 1:
                response_text = parts[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
        
        # Try to extract JSON from text if it's embedded
        if '{' in response_text and '}' in response_text:
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            response_text = response_text[start:end]
        else:
            # No JSON found, try manual column detection as fallback
            print("WARNING: No JSON found in response. Using fallback detection.")
            return fallback_column_detection(df)
        
        print(f"=== Extracted JSON ===")
        print(response_text)
        print(f"=====================\n")
        
        parsed = json.loads(response_text)
        
        symbol_col = parsed.get('symbol_column')
        quantity_col = parsed.get('quantity_column')
        price_col = parsed.get('price_column')
        
        print(f"Detected columns: symbol='{symbol_col}', quantity='{quantity_col}', price='{price_col}'")
        print(f"Available columns: {columns}\n")
        
        # Validate columns exist
        if not symbol_col or not quantity_col:
            raise ValueError(f"LLM returned empty columns: symbol={symbol_col}, quantity={quantity_col}")
        
        if symbol_col not in columns or quantity_col not in columns:
            raise ValueError(f"LLM returned columns not in DataFrame. Got symbol='{symbol_col}', quantity='{quantity_col}'. Available columns: {columns}")
        
        if price_col and price_col not in columns:
            price_col = None  # Set to None if not found
        
        return symbol_col, quantity_col, price_col
    
    except json.JSONDecodeError as e:
        error_str = str(e).encode('ascii', 'ignore').decode('ascii')
        print(f"\n!!! JSON Parse Error: {error_str}")
        print(f"!!! Attempting fallback column detection...\n")
        # Use fallback method
        return fallback_column_detection(df)
    except Exception as e:
        # Sanitize error message to remove emojis and non-ASCII characters
        error_str = str(e).encode('ascii', 'ignore').decode('ascii')
        if "fallback" not in error_str.lower():
            print(f"\n!!! Error: {error_str}")
            print(f"!!! Attempting fallback column detection...\n")
            try:
                return fallback_column_detection(df)
            except Exception as fallback_error:
                fallback_str = str(fallback_error).encode('ascii', 'ignore').decode('ascii')
                raise ValueError(f"Both LLM and fallback detection failed. LLM: {error_str}, Fallback: {fallback_str}")
        raise ValueError(f"LLM column detection failed: {error_str}")


def fallback_column_detection(df):
    """
    Fallback method to detect symbol, quantity, and price columns using heuristics.
    
    Args:
        df: DataFrame with portfolio data
        
    Returns:
        Tuple of (symbol_col, quantity_col, price_col)
    """
    print("=== Using Fallback Column Detection ===")
    
    columns = list(df.columns)
    symbol_col = None
    quantity_col = None
    price_col = None
    
    # Common symbol column patterns
    symbol_patterns = ['symbol', 'ticker', 'scrip', 'stock', 'company', 'name', 'isin']
    
    # Common quantity column patterns  
    quantity_patterns = ['quantity', 'qty', 'shares', 'holding', 'available', 'net', 'pledged']
    
    # Common price column patterns
    price_patterns = ['price', 'avg', 'current', 'market', 'closing', 'ltp', 'invested']
    
    # Exclude patterns (non-quantity data + duplicates like long term)
    exclude_patterns = ['discrepant', 'long term', 'short term', 'value', 'p&l', 'pnl', 'unrealized']
    
    # Find symbol column
    for col in columns:
        col_lower = col.lower()
        if any(pattern in col_lower for pattern in symbol_patterns):
            # Avoid numeric or boolean columns
            if df[col].dtype == 'object' or df[col].dtype == 'string':
                symbol_col = col
                print(f"Found symbol column: {col}")
                break
    
    # Find quantity column
    for col in columns:
        col_lower = col.lower()
        # Check if it matches quantity patterns
        if any(pattern in col_lower for pattern in quantity_patterns):
            # Exclude unwanted columns
            if not any(ex in col_lower for ex in exclude_patterns):
                # Prefer numeric columns
                try:
                    pd.to_numeric(df[col], errors='coerce')
                    quantity_col = col
                    print(f"Found quantity column: {col}")
                    break
                except:
                    continue
    
    # Find price column
    for col in columns:
        col_lower = col.lower()
        if any(pattern in col_lower for pattern in price_patterns):
            try:
                pd.to_numeric(df[col], errors='coerce')
                price_col = col
                print(f"Found price column: {col}")
                break
            except:
                continue
    
    if not symbol_col or not quantity_col:
        # Last resort: use first string column and first numeric column
        if not symbol_col:
            for col in columns:
                if df[col].dtype == 'object' or df[col].dtype == 'string':
                    symbol_col = col
                    print(f"Using first text column as symbol: {col}")
                    break
        
        if not quantity_col:
            for col in columns:
                try:
                    pd.to_numeric(df[col], errors='coerce')
                    col_lower = col.lower()
                    if not any(ex in col_lower for ex in exclude_patterns):
                        quantity_col = col
                        print(f"Using first numeric column as quantity: {col}")
                        break
                except:
                    continue
    
    if not symbol_col or not quantity_col:
        raise ValueError(f"Could not auto-detect columns. Available: {columns}")
    
    print(f"========================================\n")
    return symbol_col, quantity_col, price_col


def parse_portfolio_data(df, symbol_col=None, quantity_col=None, groq_api_key=None):
    """
    Parse and validate portfolio data from DataFrame.
    
    Args:
        df: DataFrame with portfolio data
        symbol_col: Name of symbol column (optional, auto-detected if None)
        quantity_col: Name of quantity column (optional, auto-detected if None)
        groq_api_key: Groq API key for LLM detection
        
    Returns:
        Cleaned DataFrame with columns: symbol, quantity, price (if available)
    """
    # Auto-detect columns using LLM if not provided
    if symbol_col is None or quantity_col is None:
        if not groq_api_key:
            raise ValueError("Groq API key required for auto-detecting columns")
        symbol_col, quantity_col, price_col = detect_columns_with_llm(df, groq_api_key)
    else:
        price_col = None  # If columns provided manually, no price detection
    
    # Validate columns exist
    if symbol_col not in df.columns or quantity_col not in df.columns:
        raise ValueError(f"DataFrame must contain '{symbol_col}' and '{quantity_col}' columns")
    
    # Find all quantity-related columns to sum (for brokers that split holdings)
    # Keywords that indicate a quantity column
    quantity_keywords = ['quantity', 'qty', 'holding', 'shares', 'available', 'pledged']
    
    # Keywords to exclude (non-quantity data + duplicates)
    exclude_keywords = ['discrepant', 'long term', 'short term', 'price', 'value', 'average', 'closing', 'p&l', 'pnl', 'unrealized']
    
    quantity_cols_to_sum = []
    for col in df.columns:
        col_lower = col.lower()
        # Check if it's a quantity column
        if any(kw in col_lower for kw in quantity_keywords):
            # Exclude discrepant and non-quantity columns
            if not any(ex in col_lower for ex in exclude_keywords):
                # Verify it's numeric
                try:
                    pd.to_numeric(df[col], errors='coerce')
                    quantity_cols_to_sum.append(col)
                    print(f"  - Found quantity column: {col}")
                except:
                    pass
    
    print(f"\n=== Quantity Column Detection ===")
    print(f"Primary quantity column (detected): {quantity_col}")
    print(f"All quantity columns to sum ({len(quantity_cols_to_sum)}): {quantity_cols_to_sum}")
    
    # If no quantity columns found, use the detected one
    if len(quantity_cols_to_sum) == 0:
        quantity_cols_to_sum = [quantity_col]
        print(f"No multiple quantity columns found, using primary: {quantity_col}")
    
    print(f"================================\n")
    
    # Start with symbol column - keep ALL rows initially
    result = df[[symbol_col]].copy()
    result.columns = ['symbol']
    
    print(f"Starting with {len(result)} rows from source data\n")
    
    # Sum all quantity columns
    print(f"Summing {len(quantity_cols_to_sum)} quantity columns...")
    total_quantity = 0
    for qcol in quantity_cols_to_sum:
        qty_numeric = pd.to_numeric(df[qcol], errors='coerce').fillna(0)
        qty_sum = qty_numeric.sum()
        non_zero = (qty_numeric > 0).sum()
        print(f"  - {qcol}: {qty_sum:.0f} total shares ({non_zero} non-zero entries)")
        total_quantity = total_quantity + qty_numeric
    
    result['quantity'] = total_quantity
    print(f"Grand total: {total_quantity.sum():.0f} shares across all stocks")
    print(f"Stocks with quantity > 0: {(total_quantity > 0).sum()}\n")
    
    # Add price column if detected
    if price_col:
        result['price'] = pd.to_numeric(df[price_col], errors='coerce')
        print(f"Added price column from '{price_col}'")
    else:
        result['price'] = None
        print("No price column detected")
    
    # Clean symbols (uppercase, strip whitespace)
    result['symbol'] = result['symbol'].astype(str).str.strip().str.upper()
    
    # Convert quantity to numeric (if not already)
    result['quantity'] = pd.to_numeric(result['quantity'], errors='coerce')
    
    # Remove rows with invalid symbols or quantities
    result = result.dropna(subset=['quantity'])
    result = result[result['symbol'].str.len() > 0]
    result = result[result['quantity'] > 0]
    
    # Filter out debt instruments (SG prefix - sovereign gold bonds, etc.)
    debt_count = (result['symbol'].str.startswith('SG')).sum()
    if debt_count > 0:
        print(f"Filtering out {debt_count} debt instruments (symbols starting with SGB)")
        result = result[~result['symbol'].str.startswith('SGB')]
    
    # Remove duplicates (keep first occurrence)
    result = result.drop_duplicates(subset=['symbol'], keep='first')
    
    print(f"Final portfolio: {len(result)} stocks with total quantity {result['quantity'].sum():.0f}\n")
    
    return result.reset_index(drop=True)
