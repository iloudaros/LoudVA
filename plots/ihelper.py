import matplotlib.pyplot as plt
import csv
import os
import re
from adjustText import adjust_text

def human_readable_frequency(frequency):
    if frequency >= 1e9:
        return f"{frequency / 1e9:.2f} GHz"
    elif frequency >= 1e6:
        return f"{frequency / 1e6:.2f} MHz"
    elif frequency >= 1e3:
        return f"{frequency / 1e3:.2f} kHz"
    else:
        return f"{frequency:.2f} Hz"

def is_pareto_efficient(costs, maximize_x=False, maximize_y=False, maximize_z=False):
    is_efficient = [True] * len(costs)
    for i, cost in enumerate(costs):
        for j, comp in enumerate(costs):
            if i != j:
                if maximize_x:
                    dominates_x = comp[0] > cost[0]
                else:
                    dominates_x = comp[0] < cost[0]

                if maximize_y:
                    dominates_y = comp[1] > cost[1]
                else:
                    dominates_y = comp[1] < cost[1]

                # Handle the optional third dimension
                if len(cost) == 3:
                    if maximize_z:
                        dominates_z = comp[2] > cost[2]
                    else:
                        dominates_z = comp[2] < cost[2]

                    if dominates_x and dominates_y and dominates_z:
                        is_efficient[i] = False
                        break
                else:
                    if dominates_x and dominates_y:
                        is_efficient[i] = False
                        break
    return is_efficient

def extract_frequency_from_filename(filename):
    match = re.search(r'(\d+)(?=.\w+$)', filename)
    if match:
        return int(match.group(1))
    else:
        return None

def parse_distrust_file(distrust_file_path):
    distrust_data = {}
    with open(distrust_file_path, 'r') as file:
        for line in file:
            parts = line.strip().split()
            
            freq_conc = parts[0]+parts[1]
            count = int(parts[2])
            distrust_level = len(parts[3]) if len(parts) == 4 else 0
            freq_conc = eval(freq_conc)  # Convert string to tuple
            distrust_data[freq_conc] = distrust_level
    return distrust_data

def plot(folder_path, row_number_x, row_number_y, row_name_x, row_name_y, title, label_column=None, connect_points=True, label_points=False, offset=(0.01, 0.01), pareto_boundary=False, maximize_x=False, maximize_y=False, row_number_z=None, maximize_z=False, debug_mode=False, distrust_file_path=None, distrust_threshold=None, export_file_path=None):
    # Get filenames and filter only the ones containing a digit before the extension
    filenames = os.listdir(folder_path)
    filenames = [f for f in filenames if extract_frequency_from_filename(f) is not None]
    filenames = sorted(filenames, key=lambda x: extract_frequency_from_filename(x), reverse=True)

    colors = plt.get_cmap('tab20c')
    plt.figure(figsize=(13, 8))  # Adjust width and height as needed

    distrust_data = parse_distrust_file(distrust_file_path) if distrust_file_path else {}
    
    if debug_mode:
        print("Distrust data:")
        for key, value in distrust_data.items():
            print(f"{key}: {value}")
        print(f"Distrust threshold: {distrust_threshold}")

    all_data = []
    for filename in filenames:
        if filename.endswith(".distrust"):
            continue  # Skip distrust files

        filepath = os.path.join(folder_path, filename)
        frequency = extract_frequency_from_filename(filename)
        if frequency is None:
            continue

        with open(filepath, 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            header = next(reader, None)
            if not header:
                continue

            data = sorted(reader, key=lambda row: float(row[0]))
            for row in data:
                x_val = float(row[row_number_x])
                y_val = float(row[row_number_y])
                label = row[label_column] if label_column is not None else None
                if row_number_z is not None:
                    z_val = float(row[row_number_z])
                    point = (x_val, y_val, z_val, label, frequency)
                else:
                    point = (x_val, y_val, label, frequency)

                # Apply distrust filtering
                freq_conc = (frequency, int(float(row[0])))  # Assuming concurrency is in the 0th column
                distrust_level = distrust_data.get(freq_conc, 0)
                if distrust_threshold is None or distrust_level <= distrust_threshold:
                    all_data.append(point)
    
    # Apply Pareto boundary filtering if enabled
    if debug_mode:
        print("All data points:")
        for point in all_data:
            print(point)
        print(f"Number of data points: {len(all_data)}")

    if pareto_boundary:
        if row_number_z is not None:
            pareto_mask = is_pareto_efficient([(point[0], point[1], point[2]) for point in all_data], maximize_x=maximize_x, maximize_y=maximize_y, maximize_z=maximize_z)
        else:
            pareto_mask = is_pareto_efficient([(point[0], point[1]) for point in all_data], maximize_x=maximize_x, maximize_y=maximize_y)
        all_data = [all_data[j] for j in range(len(all_data)) if pareto_mask[j]]

        if debug_mode:
            print("Pareto-efficient data points:")
            for point in all_data:
                print(point)
            print(f"Number of Pareto-efficient data points: {len(all_data)}")

    # Plot the data
    texts = []
    for i, filename in enumerate(filenames):
        frequency = extract_frequency_from_filename(filename)
        points = [point for point in all_data if point[-1] == frequency]
        if not points:
            continue

        x = [point[0] for point in points]
        y = [point[1] for point in points]
        labels = [point[3] for point in points] if row_number_z is not None else [point[2] for point in points]

        linestyle = '-' if connect_points else ''
        readable_frequency = human_readable_frequency(frequency)
        plt.plot(x, y, label=readable_frequency, marker='o', linestyle=linestyle, color=colors(i))

        if label_points:
            for j, txt in enumerate(labels):
                texts.append(plt.text(
                    x[j] + offset[0],
                    y[j] + offset[1],
                    txt,
                    ha='center',
                    va='center',
                    fontsize=9,
                    color='black'
                ))

    plt.xlabel(row_name_x)
    plt.ylabel(row_name_y)
    plt.title(title)
    plt.legend()
    plt.grid(True)

    if texts:
        if debug_mode:
            print("Texts to adjust:")
            for text in texts:
                print(text)
        adjust_text(texts, arrowprops=dict(arrowstyle='->', color='purple'))

    plt.show()

    # Export data points if export_file_path is provided
    if export_file_path:
        with open(export_file_path, 'w', newline='') as export_file:
            writer = csv.writer(export_file)
            if row_number_z is not None:
                writer.writerow([row_name_x, row_name_y, 'Z', 'Label', 'Frequency'])
                writer.writerows([(point[0], point[1], point[2], point[3], point[4]) for point in all_data])
            else:
                writer.writerow([row_name_x, row_name_y, 'Label', 'Frequency'])
                writer.writerows([(point[0], point[1], point[2], point[3]) for point in all_data])
