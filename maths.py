import json
from collections import defaultdict
import matplotlib.pyplot as plt

# Load JSON data from file
with open("ips.json", "r") as f:
    data = json.load(f)  # Assuming it's a list of IPs in the file


# Create a dictionary to group IPs by country
country_groups = defaultdict(list)

# Populate the dictionary
for entry in data:
    country = entry.get("country", "Unknown")  # Default to "Unknown" if no country field
    country_groups[country].append(entry)

# Example output
for country, ips in country_groups.items():
    print(f"{country}: {len(ips)} IPs")

# Extract countries and counts
countries, counts = zip(*sorted_country_counts)

# Plot the bar chart
plt.figure(figsize=(10, 6))
plt.barh(countries, counts, alpha=0.8)
plt.xlabel("Number of IPs")
plt.ylabel("Country")
plt.title("IP Distribution by Country")
plt.gca().invert_yaxis()  # Invert Y-axis for better readability
plt.show()