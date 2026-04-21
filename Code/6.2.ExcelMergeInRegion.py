import os.path

import numpy as np
import pandas as pd

continent_cities_dict = {
    'NorthAfrica': ['Alexandria', 'Casablanca', 'Cairo'],   # 3
    'America': ['SaoPaulo', 'PortoAlegre', 'Port-au-Prince', 'Caracas', 'Rio_de_Janeiro'],  # 5
    'EastSouthAsia': ['MetroManila', 'Jakarta', 'Surabaya'],    # 3
    'SouthAsia': ['Lahore', 'Delhi', 'Hyderabad', 'Mumbai', 'Karachi', 'Dhaka'],    # 6
    'SouthAfrica': ['Dar_es_Salaam', 'Kigali', 'Kampala', 'Mwanza', 'Morogoro', 'AddisAbaba', 'Accra', 'Abuja', 'Ouagadougou',
                    'Gauteng', 'Durban', 'Maputo', 'Windhoek', 'Gqeberha', 'Luanda', 'Lilongwe', 'Lusaka', 'Blantyre',
                    'Nairobi', 'CapeTown'],     # 20
    'All': ['Dar_es_Salaam', 'Kigali', 'Kampala', 'Mwanza', 'Morogoro', 'AddisAbaba', 'Accra', 'Abuja', 'Ouagadougou',
                    'Gauteng', 'Durban', 'Maputo', 'Windhoek', 'Gqeberha', 'Luanda', 'Lilongwe', 'Lusaka', 'Blantyre',
                    'Nairobi', 'CapeTown', 'Lahore', 'Delhi', 'Hyderabad', 'Mumbai', 'Karachi', 'Dhaka', 'MetroManila',
                    'Jakarta', 'Surabaya', 'SaoPaulo', 'PortoAlegre', 'Port-au-Prince', 'Caracas', 'Rio_de_Janeiro',
                    'Alexandria', 'Casablanca', 'Cairo']        # 37
}

facility = 'Health' # School
input_folder = rf"C:\Users\k\Desktop\slum\paper\data\Accessibility\Health\Distance\distance_excel_with_whole"
output_folder = rf"C:\Users\k\Desktop\slum\paper\data\Accessibility\Health\Distance\excel_in_region2"


f_slum = None
f_non_slum = None
f_city = None
for region, selected_name in continent_cities_dict.items():
    merged_file = f"{region}_Model.csv"

    os.makedirs(output_folder, exist_ok=True)
    city_in_total = 0
    csv_files = [f for f in os.listdir(input_folder) if f.endswith('.csv')]

    col_slum = None
    col_non_slum = None
    col_city = None
    total_len = 0

    for file in csv_files:

        file_path = os.path.join(input_folder, file)
        file_name = os.path.splitext(file)[0]

        if selected_name is not None and not file_name in selected_name:
            continue

        city_in_total += 1
        df = pd.read_csv(file_path)

        col1 = df.iloc[:, 0].dropna()
        col2 = df.iloc[:, 1].dropna()
        col3 = df.iloc[:, 2].dropna()

        assert len(col1) <= len(col2)  <= len(col3)

        if col_slum is not None:
            col_slum = pd.concat([col_slum, col1], ignore_index=True)      #
            col_non_slum = pd.concat([col_non_slum, col2], ignore_index=True)
            col_city = pd.concat([col_city, col3], ignore_index=True)
        else:
            col_slum = col1
            col_non_slum = col2
            col_city = col3
        # print(file, 'finished!')

    if f_slum is not None:
        f_slum = pd.concat([f_slum, col_slum], ignore_index=True)      #
        f_non_slum = pd.concat([f_non_slum, col_non_slum], ignore_index=True)
        f_city = pd.concat([f_city, col_city], ignore_index=True)
    else:
        f_slum = col_slum
        f_non_slum = col_non_slum
        f_city = col_city

    print(total_len - len(col_non_slum))
    processed_dfs = [col_slum, col_non_slum, col_city]
    merged_df = pd.concat(processed_dfs, axis=1)

    merged_df.to_csv(os.path.join(output_folder, merged_file), index=False)
    print(f" {city_in_total} files，save to {os.path.join(output_folder, merged_file)}")

    processed_df_all = [f_slum, f_non_slum, f_city]
    merged_df_all = pd.concat(processed_df_all, axis=1)
    merged_df_all.to_csv(os.path.join(output_folder, 'Merged_Model.csv'), index=False)
