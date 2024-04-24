import matplotlib.pyplot as plt
import csv
import os

def plot(folder_path, row_number, row_name, title):
  # Get filenames sorted by the highest integer in their names (descending order)
  filenames = sorted(os.listdir(folder_path), reverse=True)

  colors = plt.colormaps['tab20c']
  plt.figure(figsize=(13, 8))  # Adjust width and height as needed

  for i, filename in enumerate(filenames):
    filepath = os.path.join(folder_path, filename)
    inferences_per_second = []
    concurrency = []

    with open(filepath, 'r') as csvfile:
      reader = csv.reader(csvfile, delimiter=',')
      if not next(reader, None):  # Check if next row exists, return None if not
        continue  # Skip to the next file if the file is empty

      # Read data and sort it by the first column
      data = sorted(reader, key=lambda row: float(row[0]))
      for row in data:
        concurrency.append(float(row[0]))
        inferences_per_second.append(float(row[row_number]))

    plt.plot(concurrency, inferences_per_second, label=filename.split("_")[-1].split(".")[0], marker='o', linestyle='-', color=colors(i))

  plt.xlabel("Concurrency")
  plt.ylabel(row_name)
  plt.title(title)
  plt.legend()
  plt.grid(True)
  plt.show()