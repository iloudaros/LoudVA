import matplotlib.pyplot as plt
import csv
import os
import re

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

def plot(folder_path, row_number_x, row_number_y, row_name_x, row_name_y, title, label_column=None, connect_points=True, label_points=False, offset=(0.1, -0.2), pareto_boundary=False, maximize_x=False, maximize_y=False, row_number_z=None, maximize_z=False, debug_mode=False):
    # Get filenames and filter only the ones containing a digit before the extension
    filenames = os.listdir(folder_path)
    filenames = [f for f in filenames if extract_frequency_from_filename(f) is not None]
    filenames = sorted(filenames, key=lambda x: extract_frequency_from_filename(x), reverse=True)

    colors = plt.get_cmap('tab20c')
    plt.figure(figsize=(13, 8))  # Adjust width and height as needed

    # Collect all data points first
    all_data = []
    for filename in filenames:
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
                    all_data.append((x_val, y_val, z_val, label, frequency))
                else:
                    all_data.append((x_val, y_val, label, frequency))

    # Apply Pareto boundary filtering if enabled
    if pareto_boundary:
        if row_number_z is not None:
            pareto_mask = is_pareto_efficient([(point[0], point[1], point[2]) for point in all_data], maximize_x=maximize_x, maximize_y=maximize_y, maximize_z=maximize_z)
        else:
            pareto_mask = is_pareto_efficient([(point[0], point[1]) for point in all_data], maximize_x=maximize_x, maximize_y=maximize_y)
        all_data = [all_data[j] for j in range(len(all_data)) if pareto_mask[j]]
        
		# Print the Pareto-efficient data points and the number of them
        if debug_mode:
            print("Pareto-efficient data points:")
            for point in all_data:
                print(point)
            print(f"Number of Pareto-efficient data points: {len(all_data)}")
        

    # Plot the data
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
            # Add the point labels with an offset
            for j, txt in enumerate(labels):
                plt.text(x[j] + offset[0], y[j] + offset[1], txt, ha='center', va='center', fontsize=9, color='black')

    plt.xlabel(row_name_x)
    plt.ylabel(row_name_y)
    plt.title(title)
    plt.legend()
    plt.grid(True)
    plt.show()
