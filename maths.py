import json
import argparse
import datetime
import os
import magic

import matplotlib.pyplot as plt

from collections import Counter

#################################
#   ERROR CODES                 #
# 1 : No file provided          #
# 2 : Provided file isn't json  #
#################################

# Set up argument parser
parser = argparse.ArgumentParser(description="Analyze IP distribution by countries from a JSON file.")
parser.add_argument("file", type=str, help="Path to the JSON file containing IP data")
parser.add_argument(
    "--save", "-s", type=str, const=f"graph-{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.png", default=None, nargs="?",
    help="Path to save the graph (e.g., 'output.png'). If not specified, the graph will be saved under `YYYYMMDD-HH-MM-SS-graph.png` ."
)

args = parser.parse_args()

# Load JSON data from the provided file
if os.path.isfile(args.file):
    if (magic.from_file(args.file, mime=True) == "application/json"):
        with open(args.file, "r") as f:
            data = json.load(f)
    else:
        print(f"Error: File '{args.file}' is not a json file.")
        exit(2)
else :
    print(f"Error: File '{args.file}' does not exist.")
    exit(1)

# Count occurrences by country and sort by count
country_counts = Counter(entry.get("country", "Unknown") for entry in data)
sorted_data = sorted(country_counts.items(), key=lambda x: x[1], reverse=True)

# Extract sorted countries, counts, and percentages
total_connections = sum(country_counts.values())
countries, counts = zip(*sorted_data)
percentages = [count / total_connections * 100 for count in counts]

# Define colors (categorical colormap for distinct colors)
colors = plt.cm.tab20(range(len(countries)))

# Plot the pie chart
plt.figure(figsize=(8, 8))
patches, _, _ = plt.pie(
    counts,
    labels=None,  # Add a legend instead of labels on the chart
    colors=colors,
    autopct='',
    startangle=140,
    textprops={'fontsize': 10}
)

# Add a sorted legend with percentages and counts
legend_labels = [f"{country} - {count} ({percentage:.1f}%)" for country, count, percentage in zip(countries, counts, percentages)]
plt.legend(patches, legend_labels, loc="best", title="Connections by Country")

plt.title("IP Distribution by Country")

if args.save:
    plt.savefig(args.save, bbox_inches="tight")
    print(f"Graph saved to {args.save}")
else:
    plt.show()