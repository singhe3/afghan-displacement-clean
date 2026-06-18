#!/usr/bin/env python
"""
Afghanistan Displacement Analysis - Main Entry Point
"""

import sys
import pandas as pd
from pathlib import Path
import logging

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
    
    # Train/test split
    from sklearn.model_selection import train_test_split
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import mean_squared_error, r2_score
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Train model
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    rmse = mean_squared_error(y_test, y_pred) ** 0.5
    
    print(f"\n📊 Results:")
    print(f"  R² Score:  {r2:.4f}")
    print(f"  RMSE:      {rmse:,.0f}")
    
    # Feature importance
    importance = pd.DataFrame({
        'Feature': X.columns,
        'Coefficient': model.coef_
    }).sort_values('Coefficient', ascending=False)
    
    print(f"\n📈 Top 5 Features:")
    for i, row in importance.head(5).iterrows():
        print(f"  {row['Feature']}: {row['Coefficient']:.4f}")
    
    # Save results
    output_dir = Path("outputs/results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {
        'model': 'Linear Regression',
        'r2': r2,
        'rmse': rmse,
        'features': X.columns.tolist(),
        'coefficients': model.coef_.tolist()
    }
    
    import json
    with open(output_dir / 'regression_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Results saved to: {output_dir / 'regression_results.json'}")
    print(f"✓ Model summary saved")

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
