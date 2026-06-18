import pandas as pd
import glob
import os
import warnings
warnings.filterwarnings('ignore')

print("="*60)
print("AFGHANISTAN DISPLACEMENT DATA PROCESSOR")
print("="*60)

# Get current directory
current_dir = os.getcwd()
print(f"\nCurrent directory: {current_dir}")

# Search for files in current directory AND all subdirectories
csv_files = []
xlsx_files = []

# Walk through all subdirectories
for root, dirs, files in os.walk(current_dir):
    for file in files:
        if file.startswith('afghanistan_conflict_displacements_') and file.endswith('.csv'):
            csv_files.append(os.path.join(root, file))
        elif file.startswith('afghanistan_conflict_displacements_') and file.endswith('.xlsx'):
            xlsx_files.append(os.path.join(root, file))

print(f"\nFound {len(csv_files)} CSV files and {len(xlsx_files)} Excel files")
print("-"*60)

# Function to clean date format
def clean_date(date_val):
    if pd.isna(date_val):
        return pd.NaT
    if isinstance(date_val, pd.Timestamp):
        return date_val
    if isinstance(date_val, str):
        date_val = date_val.strip()
        if '-' in date_val:
            parts = date_val.split('-')
            if len(parts) == 3:
                if len(parts[0]) == 4:
                    try:
                        return pd.to_datetime(date_val)
                    except:
                        pass
                else:
                    try:
                        return pd.to_datetime(date_val, format='%d-%m-%y')
                    except:
                        pass
        if '/' in date_val:
            try:
                return pd.to_datetime(date_val, format='%d/%m/%Y')
            except:
                pass
    try:
        return pd.to_datetime(date_val)
    except:
        return pd.NaT

all_files = []

# Process CSV files
for file in csv_files:
    try:
        print(f"Reading: {os.path.basename(file)}")
        df = pd.read_csv(file, skiprows=1)
        df.columns = df.columns.str.strip()
        
        if all(col in df.columns for col in ['ORIG_PROV_NAME', 'DISP_DATE', 'DISP_IND']):
            df_temp = df[['ORIG_PROV_NAME', 'DISP_DATE', 'DISP_IND']].copy()
            df_temp['date'] = df_temp['DISP_DATE'].apply(clean_date)
            df_temp['location'] = df_temp['ORIG_PROV_NAME'].astype(str).str.strip()
            df_temp['displaced'] = pd.to_numeric(df_temp['DISP_IND'], errors='coerce').fillna(0)
            df_temp = df_temp[df_temp['date'].notna()]
            df_temp = df_temp[['location', 'date', 'displaced']]
            all_files.append(df_temp)
            print(f"  ✓ Added {len(df_temp):,} rows")
        else:
            print(f"  ✗ Missing required columns")
    except Exception as e:
        print(f"  ✗ Error: {e}")

# Process Excel files
for file in xlsx_files:
    try:
        print(f"Reading: {os.path.basename(file)}")
        try:
            df = pd.read_excel(file, sheet_name='Data', skiprows=1)
        except:
            try:
                df = pd.read_excel(file, sheet_name=0, skiprows=1)
            except:
                df = pd.read_excel(file, skiprows=1)
        
        df.columns = df.columns.str.strip()
        
        if all(col in df.columns for col in ['ORIG_PROV_NAME', 'DISP_DATE', 'DISP_IND']):
            df_temp = df[['ORIG_PROV_NAME', 'DISP_DATE', 'DISP_IND']].copy()
            df_temp['date'] = df_temp['DISP_DATE'].apply(clean_date)
            df_temp['location'] = df_temp['ORIG_PROV_NAME'].astype(str).str.strip()
            df_temp['displaced'] = pd.to_numeric(df_temp['DISP_IND'], errors='coerce').fillna(0)
            df_temp = df_temp[df_temp['date'].notna()]
            df_temp = df_temp[['location', 'date', 'displaced']]
            all_files.append(df_temp)
            print(f"  ✓ Added {len(df_temp):,} rows")
        else:
            print(f"  ✗ Missing required columns")
    except Exception as e:
        print(f"  ✗ Error: {e}")

if all_files:
    print("\n" + "="*60)
    print("COMBINING DATA...")
    print("="*60)
    
    combined_df = pd.concat(all_files, ignore_index=True)
    print(f"\nTotal raw records: {len(combined_df):,}")
    
    combined_df = combined_df[combined_df['location'].notna()]
    combined_df = combined_df[combined_df['location'] != 'nan']
    combined_df = combined_df[combined_df['location'] != '']
    
    print(f"After cleaning missing locations: {len(combined_df):,}")
    
    aggregated_df = combined_df.groupby(['location', 'date'], as_index=False)['displaced'].sum()
    aggregated_df = aggregated_df.rename(columns={'displaced': 'total_outflow_migration'})
    aggregated_df = aggregated_df.sort_values(['date', 'location']).reset_index(drop=True)
    
    print(f"\nFinal aggregated records: {len(aggregated_df):,}")
    print(f"Unique locations: {aggregated_df['location'].nunique()}")
    print(f"Date range: {aggregated_df['date'].min()} to {aggregated_df['date'].max()}")
    
    output_csv = 'afghanistan_displacement_combined.csv'
    output_excel = 'afghanistan_displacement_combined.xlsx'
    
    aggregated_df.to_csv(output_csv, index=False)
    aggregated_df.to_excel(output_excel, index=False, sheet_name='Displacement Data')
    
    print(f"\n✓ Saved to: {output_csv}")
    print(f"✓ Saved to: {output_excel}")
    
    print("\n" + "="*60)
    print("SAMPLE DATA (First 20 rows):")
    print("="*60)
    print(aggregated_df.head(20).to_string())
    
    print("\n" + "="*60)
    print("TOP 10 LOCATIONS BY TOTAL DISPLACEMENT:")
    print("="*60)
    top_locations = aggregated_df.groupby('location')['total_outflow_migration'].sum().sort_values(ascending=False).head(10)
    print(top_locations.to_string())
    
else:
    print("\n❌ No data was loaded!")
    print("\nSearching in these locations:")
    print(f"  - {current_dir}")
    print("\nLooking for files starting with: afghanistan_conflict_displacements_")
    print("\nCheck that your files are in the correct folder.")
    print(f"\nFiles found in this folder and subfolders:")
    for root, dirs, files in os.walk(current_dir):
        for file in files:
            if 'afghanistan' in file.lower() or 'displacement' in file.lower():
                print(f"  - {os.path.join(root, file)}")