#!/usr/bin/env python
"""
Afghanistan Displacement Analysis - Main Entry Point
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def process_data():
    """Process raw displacement data."""
    print("\n" + "="*60)
    print("DATA PROCESSING")
    print("="*60)
    
    data_dir = Path("data/raw")
    files = list(data_dir.glob("*.csv")) + list(data_dir.glob("*.xlsx"))
    
    if not files:
        print("❌ No data files found in data/raw/")
        print("Please add your data files to data/raw/")
        return None
    
    print(f"\nFound {len(files)} files:")
    all_data = []
    
    for file in files:
        try:
            if file.suffix == '.csv':
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)
            
            # Check if this is displacement data
            if 'location' in df.columns and 'date' in df.columns:
                if 'total_outflow_migration' in df.columns:
                    df = df[['location', 'date', 'total_outflow_migration']].copy()
                    df.columns = ['PROVINCE', 'DATE', 'DISPLACED']
                    df['DATE'] = pd.to_datetime(df['DATE'])
                    all_data.append(df)
                    print(f"  ✓ Loaded {len(df):,} rows from {file.name}")
                else:
                    print(f"  ⚠ Skipping {file.name} - not displacement data")
            else:
                print(f"  ⚠ Skipping {file.name} - columns don't match")
        except Exception as e:
            print(f"  ✗ Error loading {file.name}: {e}")
    
    if not all_data:
        print("\n❌ No valid data loaded!")
        return None
    
    # Combine
    combined = pd.concat(all_data, ignore_index=True)
    print(f"\n✓ Combined: {len(combined):,} records")
    
    # Save
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "processed_data.csv"
    combined.to_csv(output_file, index=False)
    print(f"✓ Saved to: {output_file}")
    
    # Show summary
    print(f"\n📊 Data Summary:")
    print(f"  Provinces: {combined['PROVINCE'].nunique()}")
    print(f"  Date range: {combined['DATE'].min().date()} to {combined['DATE'].max().date()}")
    print(f"  Total displaced: {combined['DISPLACED'].sum():,.0f}")
    
    return combined

def run_regression():
    """Run regression model."""
    print("\n" + "="*60)
    print("REGRESSION MODEL")
    print("="*60)
    
    data_file = Path("data/processed/processed_data.csv")
    if not data_file.exists():
        print("❌ No processed data found. Run option 1 first.")
        return
    
    df = pd.read_csv(data_file)
    print(f"✓ Loaded {len(df):,} records")
    
    # Prepare features
    df['YEAR'] = pd.to_datetime(df['DATE']).dt.year
    df['MONTH'] = pd.to_datetime(df['DATE']).dt.month
    
    # Create dummies
    province_dummies = pd.get_dummies(df['PROVINCE'], prefix='prov', drop_first=True)
    
    # Features
    X = pd.concat([df[['YEAR', 'MONTH']], province_dummies], axis=1)
    y = df['DISPLACED']
    
    from sklearn.model_selection import train_test_split
    from sklearn.linear_model import LinearRegression
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import mean_squared_error, r2_score
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Try multiple models
    models = {
        'Linear Regression': LinearRegression(),
        'Random Forest': RandomForestRegressor(n_estimators=100, random_state=42)
    }
    
    results = []
    print("\n📊 Training Models...")
    
    for name, model in models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        r2 = r2_score(y_test, y_pred)
        rmse = mean_squared_error(y_test, y_pred) ** 0.5
        
        results.append({
            'Model': name,
            'R²': round(r2, 4),
            'RMSE': round(rmse, 0)
        })
        
        print(f"  {name}: R²={r2:.4f}, RMSE={rmse:,.0f}")
    
    # Best model
    best = max(results, key=lambda x: x['R²'])
    print(f"\n🏆 Best Model: {best['Model']} (R²={best['R²']:.4f})")
    
    # Save results
    output_dir = Path("outputs/results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    pd.DataFrame(results).to_csv(output_dir / 'regression_results.csv', index=False)
    print(f"\n✓ Results saved to: {output_dir / 'regression_results.csv'}")
    
    return results

def run_did():
    """Run Difference-in-Differences model."""
    print("\n" + "="*60)
    print("DID MODEL")
    print("="*60)
    print("📝 Coming soon - Difference-in-Differences analysis")

def main():
    """Main menu."""
    while True:
        print("\n" + "="*60)
        print("AFGHANISTAN DISPLACEMENT ANALYSIS")
        print("="*60)
        print("\nOptions:")
        print("  1. Process raw data")
        print("  2. Run Regression model")
        print("  3. Run DiD model")
        print("  4. Run all")
        print("  5. Exit")
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == "1":
            process_data()
        elif choice == "2":
            run_regression()
        elif choice == "3":
            run_did()
        elif choice == "4":
            process_data()
            run_regression()
            run_did()
        elif choice == "5":
            print("\nGoodbye!")
            sys.exit(0)
        else:
            print("Invalid choice. Please enter 1-5.")

if __name__ == "__main__":
    main()
