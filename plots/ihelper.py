import matplotlib.pyplot as plt
import csv
import os
import re
from adjustText import adjust_text

# Converts frequency to a human-readable format.
def human_readable_frequency(frequency):
    if frequency >= 1e9:
        return f"{frequency / 1e9:.2f} GHz"
    elif frequency >= 1e6:
        return f"{frequency / 1e6:.2f} MHz"
    elif frequency >= 1e3:
        return f"{frequency / 1e3:.2f} kHz"
    else:
        return f"{frequency:.2f} Hz"

# Determines if a point is on the Pareto frontier.
def is_pareto_efficient(costs, maximize_x=False, maximize_y=False, maximize_z=False):
    is_efficient = [True] * len(costs)  # Initialize all points as efficient.
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

# Extracts frequency from filename.
def extract_frequency_from_filename(filename):
    match = re.search(r'(\d+)(?=.\w+$)', filename)
    if match:
        return int(match.group(1))
    else:
        return None

# Parses a distrust file and converts distrust levels into a dictionary.
def parse_distrust_file(distrust_file_path):
    distrust_data = {}
    with open(distrust_file_path, 'r') as file:
        for line in file:
            parts = line.strip().split()
            freq_conc = parts[0]+parts[1]
            count = int(parts[2])
            distrust_level = len(parts[3]) if len(parts) == 4 else 0
            freq_conc = eval(freq_conc)  # Convert string to tuple.
            distrust_data[freq_conc] = distrust_level
    return distrust_data

# Main plotting function.
def plot(folder_paths, row_number_x, row_number_y, row_name_x, row_name_y, title, label_column=None, connect_points=True, label_points=False, offset=(0.01, 0.01), pareto_boundary=False, maximize_x=False, maximize_y=False, row_number_z=None, maximize_z=False, debug_mode=False, distrust_file_paths=None, distrust_threshold=None, export_file_path=None, directory_labels=None):
    # Convert single string path to a list containing that path.
    if isinstance(folder_paths, str):
        folder_paths = [folder_paths]
    
    # Default directory labels if not provided.
    if directory_labels is None:
        directory_labels = [str(i) for i in range(len(folder_paths))]

    # Check if the number of folder paths matches the number of directory labels.
    assert len(folder_paths) == len(directory_labels), "The number of folders must match the number of directory labels."

    if distrust_file_paths is not None and isinstance(distrust_file_paths, str):
        distrust_file_paths = [distrust_file_paths]

    all_filenames = []
    frequencies_by_folder = {}
    distrust_data_by_folder = {}
    single_directory = len(folder_paths) == 1

    # Process each folder and gather filenames.
    for folder_path, dirname in zip(folder_paths, directory_labels):
        filenames = os.listdir(folder_path)
        filenames = [f for f in filenames if extract_frequency_from_filename(f) is not None]
        filenames = sorted(filenames, key=lambda x: extract_frequency_from_filename(x), reverse=True)
        all_filenames.extend([(f, dirname) for f in filenames])
        frequencies_by_folder[dirname] = []

        # Parse distrust files if provided.
        distrust_data = {}
        if distrust_file_paths and folder_path in distrust_file_paths:
            distrust_file_path = distrust_file_paths[folder_paths.index(folder_path)]
            distrust_data = parse_distrust_file(distrust_file_path)

        distrust_data_by_folder[dirname] = distrust_data
        if debug_mode:
            print(f"Distrust data for {dirname}:")
            for key, value in distrust_data.items():
                print(f"{key}: {value}")

    colors = plt.get_cmap('tab20c')  # Use colormap.
    plt.figure(figsize=(16, 10))  # Set plot size.

    all_data = []

    # Process each file and gather data points.
    for filename, dirname in all_filenames:
        folder_path = folder_paths[directory_labels.index(dirname)]
        filepath = os.path.join(folder_path, filename)
        frequency = extract_frequency_from_filename(filename)
        if frequency is None:
            continue

        frequencies_by_folder[dirname].append(frequency)

        with open(filepath, 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            header = next(reader, None)
            if not header:
                continue

            # Sort data based on the first column.
            data = sorted(reader, key=lambda row: float(row[0]))
            for row in data:
                x_val = float(row[row_number_x])
                y_val = float(row[row_number_y])
                label = row[label_column].replace('\n', ' ') if label_column is not None else None
                if row_number_z is not None:
                    z_val = float(row[row_number_z])
                    point = (x_val, y_val, z_val, label, frequency, dirname)
                else:
                    point = (x_val, y_val, label, frequency, dirname)

                freq_conc = (frequency, int(float(row[0])))  # Assuming concurrency is in the 0th column.
                distrust_level = distrust_data_by_folder[dirname].get(freq_conc, 0)
                if distrust_threshold is None or distrust_level <= distrust_threshold:
                    all_data.append(point)
    
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
    num_files_processed = 0
    for directory_label in directory_labels:
        for frequency in sorted(frequencies_by_folder[directory_label], reverse=True):
            # Filter points based on frequency and directory label.
            points = [point for point in all_data if point[-2] == frequency and point[-1] == directory_label]
            if not points:
                continue

            x = [point[0] for point in points]
            y = [point[1] for point in points]
            if row_number_z is not None:
                labels = [f"{directory_label} | {point[3]}" if not single_directory else point[3] for point in points]
            else:
                labels = [f"{directory_label} | {point[2]}" if not single_directory else point[2] for point in points]

            linestyle = '-' if connect_points else ''
            readable_frequency = human_readable_frequency(frequency)
            legend_label = f"{readable_frequency} ({directory_label})" if not single_directory else readable_frequency
            plt.plot(x, y, label=legend_label, marker='o', linestyle=linestyle, color=colors(num_files_processed % 20))
            num_files_processed += 1

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

    # Plot labels and other plot settings.
    plt.xlabel(row_name_x)
    plt.ylabel(row_name_y)
    plt.title(title)
    plt.legend()
    plt.grid(True)

    # Adjust text labels to avoid overlap.
    if texts:
        if debug_mode:
            print("Texts to adjust:")
            for text in texts:
                print(text)
        adjust_text(texts, arrowprops=dict(arrowstyle='->', color='purple'))

    plt.show()

    # Export the data points if export file path is provided.
    if export_file_path:
        with open(export_file_path, 'w', newline='') as export_file:
            writer = csv.writer(export_file)
            if row_number_z is not None:
                if single_directory:
                    writer.writerow([row_name_x, row_name_y, 'Z', 'Label', 'Frequency'])
                    writer.writerows([(point[0], point[1], point[2], point[3], point[4]) for point in all_data])
                else:
                    writer.writerow([row_name_x, row_name_y, 'Z', 'Label', 'Frequency', 'Directory'])
                    writer.writerows([(point[0], point[1], point[2], point[3], point[4], point[5]) for point in all_data])
            else:
                if single_directory:
                    writer.writerow([row_name_x, row_name_y, 'Label', 'Frequency'])
                    writer.writerows([(point[0], point[1], point[2], point[3]) for point in all_data])
                else:
                    writer.writerow([row_name_x, row_name_y, 'Label', 'Frequency', 'Directory'])
                    writer.writerows([(point[0], point[1], point[2], point[3], point[4]) for point in all_data])
