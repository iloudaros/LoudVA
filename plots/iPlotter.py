import matplotlib.pyplot as plt
import seaborn as sns
import csv
import os
import re
from adjustText import adjust_text
import pandas as pd

def human_readable_frequency(frequency):
    """Convert frequency to a human-readable format."""
    if frequency >= 1e9:
        return f"{frequency / 1e9:.2f} GHz"
    elif frequency >= 1e6:
        return f"{frequency / 1e6:.2f} MHz"
    elif frequency >= 1e3:
        return f"{frequency / 1e3:.2f} kHz"
    else:
        return f"{frequency:.2f} Hz"

def is_pareto_efficient(costs, maximize_x=False, maximize_y=False, maximize_z=False):
    """Determine if a point is on the Pareto frontier."""
    is_efficient = [True] * len(costs)
    for i, cost in enumerate(costs):
        for j, comp in enumerate(costs):
            if i != j:
                dominates_x = comp[0] > cost[0] if maximize_x else comp[0] < cost[0]
                dominates_y = comp[1] > cost[1] if maximize_y else comp[1] < cost[1]
                if len(cost) == 3:
                    dominates_z = comp[2] > cost[2] if maximize_z else comp[2] < cost[2]
                    if dominates_x and dominates_y and dominates_z:
                        is_efficient[i] = False
                        break
                else:
                    if dominates_x and dominates_y:
                        is_efficient[i] = False
                        break
    return is_efficient

def extract_frequency_from_filename(filename):
    """Extract frequency from filename."""
    match = re.search(r'(\d+)(?=.\w+$)', filename)
    return int(match.group(1)) if match else None

def parse_distrust_file(distrust_file_path):
    """Parse a distrust file and convert distrust levels into a dictionary."""
    distrust_data = {}
    with open(distrust_file_path, 'r') as file:
        for line in file:
            parts = line.strip().split()
            freq_conc = eval(parts[0] + parts[1])  # Convert string to tuple.
            distrust_level = len(parts[3]) if len(parts) == 4 else 0
            distrust_data[freq_conc] = distrust_level
    return distrust_data

def plot(folder_paths, row_number_x, row_number_y, row_name_x, row_name_y, title,
         label_column=None, connect_points=True, label_points=False, offset=(0.01, 0.01),
         pareto_boundary=False, maximize_x=False, maximize_y=False, row_number_z=None,
         row_name_z='Z', maximize_z=False, debug_mode=False, distrust_file_paths=None,
         distrust_threshold=None, export_file_path=None, directory_labels=None, filter_only=False):
    """Main plotting function with seaborn styling for publication-quality figures."""
    
    folder_paths = [folder_paths] if isinstance(folder_paths, str) else folder_paths
    directory_labels = directory_labels or [str(i) for i in range(len(folder_paths))]

    assert len(folder_paths) == len(directory_labels), "The number of folders must match the number of directory labels."

    if distrust_file_paths and isinstance(distrust_file_paths, str):
        distrust_file_paths = [distrust_file_paths]

    all_filenames = []
    frequencies_by_folder = {}
    distrust_data_by_folder = {}
    single_directory = len(folder_paths) == 1

    for folder_path, dirname in zip(folder_paths, directory_labels):
        filenames = sorted([f for f in os.listdir(folder_path) if extract_frequency_from_filename(f) is not None],
                           key=lambda x: extract_frequency_from_filename(x), reverse=True)
        all_filenames.extend([(f, dirname) for f in filenames])
        frequencies_by_folder[dirname] = []

        distrust_data = {}
        if distrust_file_paths and folder_path in distrust_file_paths:
            distrust_file_path = distrust_file_paths[folder_paths.index(folder_path)]
            distrust_data = parse_distrust_file(distrust_file_path)

        distrust_data_by_folder[dirname] = distrust_data
        if debug_mode:
            print(f"Distrust data for {dirname}:")
            for key, value in distrust_data.items():
                print(f"{key}: {value}")

    all_data = []

    for filename, dirname in all_filenames:
        filepath = os.path.join(folder_paths[directory_labels.index(dirname)], filename)
        frequency = extract_frequency_from_filename(filename)
        if frequency is None:
            continue

        frequencies_by_folder[dirname].append(frequency)

        with open(filepath, 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            header = next(reader, None)
            if not header:
                continue

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

                freq_conc = (frequency, int(float(row[0])))
                distrust_level = distrust_data_by_folder[dirname].get(freq_conc, 0)
                if distrust_threshold is None or distrust_level <= distrust_threshold:
                    all_data.append(point)

    if debug_mode:
        print("All data points:")
        for point in all_data:
            print(point)
        print(f"Number of data points: {len(all_data)}")

    if pareto_boundary:
        pareto_mask = is_pareto_efficient(
            [(point[0], point[1], point[2]) for point in all_data] if row_number_z is not None else [(point[0], point[1]) for point in all_data],
            maximize_x=maximize_x, maximize_y=maximize_y, maximize_z=maximize_z
        )
        all_data = [all_data[j] for j in range(len(all_data)) if pareto_mask[j]]

        if debug_mode:
            print("Pareto-efficient data points:")
            for point in all_data:
                print(point)
            print(f"Number of Pareto-efficient data points: {len(all_data)}")

    # Export the data points if export file path is provided.
    if export_file_path:
        with open(export_file_path, 'w', newline='') as export_file:
            writer = csv.writer(export_file)
            if row_number_z is not None:
                if single_directory:
                    writer.writerow([row_name_x, row_name_y, row_name_z, 'Label', 'Frequency'])
                    writer.writerows([(point[0], point[1], point[2], point[3], point[4]) for point in all_data])
                else:
                    writer.writerow([row_name_x, row_name_y, row_name_z, 'Label', 'Frequency', 'Directory'])
                    writer.writerows([(point[0], point[1], point[2], point[3], point[4], point[5]) for point in all_data])
            else:
                if single_directory:
                    writer.writerow([row_name_x, row_name_y, 'Label', 'Frequency'])
                    writer.writerows([(point[0], point[1], point[2], point[3]) for point in all_data])
                else:
                    writer.writerow([row_name_x, row_name_y, 'Label', 'Frequency', 'Directory'])
                    writer.writerows([(point[0], point[1], point[2], point[3], point[4]) for point in all_data])

    # If filter_only is True, skip plotting and return the filtered data
    if filter_only:
        return all_data

    # ============ SEABORN PLOTTING SECTION ============
    
    # Set seaborn style optimized for publication
    sns.set_theme(style="ticks", context="paper")
    sns.set_context("paper", font_scale=7.5, rc={"lines.linewidth": 2.0})
    
    # Create figure with high DPI for publication quality
    fig, ax = plt.subplots(figsize=(10, 7), dpi=300)
    
    # Use tab20/tab20b/tab20c colormap similar to original
    # Combining tab20, tab20b, and tab20c for maximum color variety
    num_unique_combinations = sum(len(frequencies_by_folder[d]) for d in directory_labels)
    
    # Create extended color palette using tab20 variants (similar to original tab20c)
    if num_unique_combinations <= 20:
        colors = sns.color_palette("tab20", n_colors=20)
    else:
        # Combine multiple tab palettes for more colors
        colors = (sns.color_palette("tab20", n_colors=20) + 
                 sns.color_palette("tab20b", n_colors=20) + 
                 sns.color_palette("tab20c", n_colors=20))
    
    texts = []
    num_files_processed = 0
    
    for directory_label in directory_labels:
        for frequency in sorted(frequencies_by_folder[directory_label], reverse=True):
            points = [point for point in all_data if point[-2] == frequency and point[-1] == directory_label]
            if not points:
                continue

            x = [point[0] for point in points]
            y = [point[1] for point in points]
            labels = [f"{directory_label} | {point[3]}" if not single_directory else point[3] for point in points]

            readable_frequency = human_readable_frequency(frequency)
            legend_label = f"{readable_frequency} ({directory_label})" if not single_directory else readable_frequency
            
            current_color = colors[num_files_processed % len(colors)]
            
            # Plot with enhanced styling for publication
            if connect_points:
                ax.plot(x, y, label=legend_label, marker='o', linestyle='-', 
                       color=current_color,
                       linewidth=2.0, markersize=7, 
                       markeredgewidth=1.0, 
                       markeredgecolor='white', 
                       alpha=0.85,
                       zorder=3)
            else:
                ax.scatter(x, y, label=legend_label, 
                          color=current_color,
                          s=100, edgecolors='white', 
                          linewidth=1.0, alpha=0.85,
                          zorder=3)
            
            num_files_processed += 1

            if label_points:
                for j, txt in enumerate(labels):
                    texts.append(ax.text(x[j] + offset[0], y[j] + offset[1], txt, 
                                        ha='center', va='center', 
                                        fontsize=8, 
                                        color='black',
                                        bbox=dict(boxstyle='round,pad=0.4', 
                                                facecolor='white', 
                                                edgecolor='lightgray', 
                                                alpha=0.8,
                                                linewidth=0.5)))

    # Enhanced axis labels and formatting for publication
    ax.set_xlabel(row_name_x, fontsize=14, fontweight='bold', labelpad=8)
    ax.set_ylabel(row_name_y, fontsize=14, fontweight='bold', labelpad=8)
    
    # Title removed for publication
    
    # Professional legend styling
    legend = ax.legend(fontsize=10, 
                      frameon=True, 
                      shadow=False,
                      fancybox=False,
                      edgecolor='black',
                      framealpha=0.95,
                      loc='best', 
                      ncol=1 if num_files_processed <= 8 else 2)
    legend.get_frame().set_linewidth(0.8)
    
    # Subtle grid for easier reading
    ax.grid(True, alpha=0.25, linestyle='--', linewidth=0.6, zorder=0)
    
    # Professional tick styling
    ax.tick_params(axis='both', which='major', labelsize=11, 
                   direction='out', length=4, width=0.8)
    
    # Clean up spines for publication
    sns.despine(ax=ax, top=True, right=True, trim=True)
    ax.spines['left'].set_linewidth(0.8)
    ax.spines['bottom'].set_linewidth(0.8)
    
    # Tight layout to prevent label cutoff
    plt.tight_layout()

    if texts:
        if debug_mode:
            print("Texts to adjust:")
            for text in texts:
                print(text)
        adjust_text(texts, 
                  # arrowprops=dict(arrowstyle='->', color='gray', lw=1.0, alpha=0.7),
                   expand_points=(1.2, 1.2),
                   force_points=0.5)

    plt.show()
    
    return fig, ax  # Return figure and axis for further customization or saving
