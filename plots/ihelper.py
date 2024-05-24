import matplotlib.pyplot as plt
import csv
import os

def plot(folder_path, row_number_x, row_number_y, row_name_x, row_name_y, title, connect_points=True):
  # Get filenames sorted by the highest integer in their names (descending order)
  filenames = os.listdir(folder_path)
  filenames = sorted(filenames, key=lambda x : int(x.split("_")[-1].split(".")[0]) if x.endswith('.csv') else 0, reverse=True)

  colors = plt.colormaps['tab20c']
  plt.figure(figsize=(13, 8))  # Adjust width and height as needed

  for i, filename in enumerate(filenames):
    filepath = os.path.join(folder_path, filename)
    y = []
    x = []

    with open(filepath, 'r') as csvfile:
      reader = csv.reader(csvfile, delimiter=',')
      if not next(reader, None):  # Check if next row exists, return None if not
        continue  # Skip to the next file if the file is empty

      # Read data and sort it by the first column
      data = sorted(reader, key=lambda row: float(row[0]))
      for row in data:
        x.append(float(row[row_number_x]))
        y.append(float(row[row_number_y]))


    linestyle = '-' if connect_points else ''
    plt.plot(x, y, label=filename.split("_")[-1].split(".")[0], marker='o', linestyle=linestyle, color=colors(i))

  plt.xlabel(row_name_x)
  plt.ylabel(row_name_y)
  plt.title(title)
  plt.legend()
  plt.grid(True)
  plt.show()