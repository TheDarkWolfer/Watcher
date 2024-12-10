import json
from collections import defaultdict, Counter
import matplotlib.pyplot as plt

# Load JSON data from file
with open("ips.json", "r") as f:
    data = json.load(f)  # Assuming it's a list of IPs in the file

# Count occurrences by country
country_counts = Counter(entry.get("country", "Unknown") for entry in data)

# Sort by number of occurrences
sorted_country_counts = sorted(country_counts.items(), key=lambda x: x[1], reverse=True)

# Print sorted results
for country, count in sorted_country_counts:
    print(f"{country}: {count} IPs")

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