import pandas as pd

file = "C:\\Users\\ishan\\OneDrive\\Desktop\\UWash\\ML\\Data_visualization\\Data_viz_project\\SI_XLS\\SI_XLS\\Input data.xlsx"

t1 = pd.read_excel(file, sheet_name="Table 1", skiprows=3)
t1.columns = ["pca_name", "internal_mwh", "colocation_mwh",
              "hyperscale_mwh", "total_mwh"]


t2 = pd.read_excel(file, sheet_name="Table 2", skiprows=3)
t2.columns = [
    "plant_state", "plant_name", "plant_id", "balancing_authority",
    "balancing_code", "pca_generation_mwh", "lat", "lon",
    "primary_fuel", "fuel_code", "net_gen_mwh", "co2_tons",
    "water_intensity_m3_per_mwh", "carbon_intensity_tons_per_mwh",
    "generation_ratio", "water_consumption_m3",
    "subbasin", "huc8", "huc8_id"
]


t4 = pd.read_excel(file, sheet_name="Table 4", skiprows=3)
t4.columns = ["subbasin", "huc8", "area_m2", "huc8_id", "pca_name"]


t5 = pd.read_excel(file, sheet_name="Table 5", skiprows=3)
t5.columns = ["huc8_id", "subbasin_name", "scaled_mwh", "scarcity_factor"]


t6 = pd.read_excel(file, sheet_name="Table 6", skiprows=3)
t6.columns = ["state", "water_intensity", "emission_intensity", "state_scaled_mwh"]


t1["pca_name"] = t1["pca_name"].str.strip()
t4["pca_name"] = t4["pca_name"].str.strip()


t4["huc8_id"] = t4["huc8_id"].astype(str)
t5["huc8_id"] = t5["huc8_id"].astype(str)
t2["huc8_id"] = t2["huc8_id"].astype(str)


merged = t4.merge(t1, on="pca_name", how="left")


merged = merged.merge(t5[["huc8_id", "scarcity_factor"]],
                      on="huc8_id", how="left")


merged = merged.merge(
    t2[[
        "huc8_id", "plant_state", "lat", "lon",
        "fuel_code", "co2_tons",
        "water_intensity_m3_per_mwh", "carbon_intensity_tons_per_mwh"
    ]],
    on="huc8_id",
    how="left"
)


merged["water_footprint"] = merged["total_mwh"] * merged["scarcity_factor"]
merged["carbon_footprint"] = merged["total_mwh"] * merged["carbon_intensity_tons_per_mwh"]



merged.to_csv("final_footprint_dataset.csv", index=False)

print("SUCCESS: final_footprint_dataset.csv has been created!")
print("Rows:", len(merged))
print("Columns:", len(merged.columns))
