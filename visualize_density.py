"""
Quick visualization of density results without GDAL
"""
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Load the density CSV
density_file = Path('data/samples/03_density/density_time_at_cells_1000_All.csv')
df = pd.read_csv(density_file)

# Remove duplicates (take max density per grid cell)
df_unique = df.groupby('gridID', as_index=False).agg({'density': 'max', 'lon_centroid': 'first', 'lat_centroid': 'first'})

print(f"Loaded {len(df_unique)} unique grid cells")
print(f"Density range: {df_unique['density'].min():.4f} to {df_unique['density'].max():.4f} hours")

# Create scatter plot
plt.figure(figsize=(12, 8))
scatter = plt.scatter(df_unique['lon_centroid'], 
                     df_unique['lat_centroid'], 
                     c=df_unique['density'], 
                     cmap='hot', 
                     s=10, 
                     alpha=0.7)
plt.colorbar(scatter, label='Time at cells (hours)')
plt.xlabel('Longitude (EPSG:3035)')
plt.ylabel('Latitude (EPSG:3035)')
plt.title('AIS Vessel Density - Time at Cells (1km grid)')
plt.tight_layout()
plt.savefig('data/samples/03_density/density_map.png', dpi=150)
print("Saved visualization to density_map.png")
plt.show()
