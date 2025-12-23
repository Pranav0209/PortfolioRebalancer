#!/usr/bin/env python3
"""
Demo script showing LLM column detection in action.
Tests detection on multiple CSV formats.
"""

import pandas as pd
import json
from loaders import detect_columns_with_llm


def demo_bio_growth():
    """Demo with Bio Growth format."""
    print("\n" + "="*60)
    print("🧪 DEMO 1: Bio Growth Format")
    print("="*60)
    
    df = pd.read_csv('bio_growth_clean.csv')
    print("\nColumns:", list(df.columns))
    print("Sample data:")
    print(df.head(3))
    
    return df


def demo_dvc809_style():
    """Demo with DVC809 format."""
    print("\n" + "="*60)
    print("🧪 DEMO 2: DVC809 Format (Simulated)")
    print("="*60)
    
    # Create a DVC809-style DataFrame
    data = {
        'Symbol': ['INFY', 'TCS', 'RELIANCE', 'HDFC'],
        'ISIN': ['INE009A01021', 'INE467B01029', 'INE002A01015', 'INE001A01383'],
        'Sector': ['IT', 'IT', 'Energy', 'Finance'],
        'Quantity Available': [100, 80, 60, 50],
        'Quantity Discrepant': [0, 0, 0, 0],
        'Quantity Pledged (Margin)': [10, 5, 0, 0],
    }
    
    df = pd.DataFrame(data)
    print("\nColumns:", list(df.columns))
    print("Sample data:")
    print(df)
    
    return df


def demo_column_detection(df, groq_api_key, format_name):
    """Demo the column detection."""
    print(f"\n📍 Running LLM column detection on {format_name}...")
    
    try:
        symbol_col, quantity_col = detect_columns_with_llm(df, groq_api_key)
        
        print(f"✅ Detected!")
        print(f"   Symbol column: {symbol_col}")
        print(f"   Quantity column: {quantity_col}")
        
        # Show extraction
        print(f"\n📊 Extracted data:")
        extracted = df[[symbol_col, quantity_col]].head(5)
        print(extracted)
        
        return True
    
    except Exception as e:
        print(f"❌ Detection failed: {str(e)}")
        return False


def main():
    """Run all demos."""
    print("\n" + "="*60)
    print("🤖 Portfolio Rebalancer - LLM Column Detection Demo")
    print("="*60)
    
    # Check for API key
    groq_api_key = input("\n🔑 Enter your Groq API key: ").strip()
    
    if not groq_api_key:
        print("❌ API key required to run demo")
        return
    
    print("\n✅ API key configured")
    
    # Test cases
    test_cases = [
        (demo_bio_growth, "Bio Growth CSV"),
        (demo_dvc809_style, "DVC809 Format"),
    ]
    
    results = []
    
    for demo_func, format_name in test_cases:
        try:
            df = demo_func()
            success = demo_column_detection(df, groq_api_key, format_name)
            results.append((format_name, success))
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            results.append((format_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 Results Summary")
    print("="*60)
    
    for format_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {format_name}")
    
    print("\n" + "="*60)
    print("Demo complete!")
    print("\nNext: Run 'streamlit run streamlit_app.py' to use the full app")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
