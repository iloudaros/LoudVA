import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import argparse

def create_plots(aggregated_csv_path):
    """
    Generates plots from aggregated experiment results.
    Automatically adapts plots based on whether the input CSV is an
    overall or a per-device aggregation.
    """
    # Set up plotting style
    sns.set_theme(style="whitegrid", context="paper", font_scale=1.2)
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['DejaVu Sans', 'Arial'],
        'figure.dpi': 300,
        'axes.titlesize': 12,
        'axes.labelsize': 11,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'legend.fontsize': 9,
        'axes.linewidth': 0.8,
        'grid.linewidth': 0.5
    })

    # Load data, assuming the separator and decimal from previous scripts
    try:
        df = pd.read_csv(aggregated_csv_path, sep=';', decimal=',')
    except Exception as e:
        print(f"Could not read with ';' separator, trying with ','. Error: {e}")
        df = pd.read_csv(aggregated_csv_path)

    # --- Determine Plotting Mode (Overall vs. Per-Device) ---
    is_per_device = 'device' in df.columns
    plot_mode = 'per_device' if is_per_device else 'overall'
    print(f"Detected '{plot_mode}' mode. Generating plots...")
    
    # --- Custom Sorting ---
    def scheduler_sort_key(x):
        if 'No Scheduler' in x:
            return (0, x)
        elif 'Fixed Batch' in x:
            try: return (1, float(x.split('(')[1].strip(')')))
            except: return (1, 99)
        elif 'Interval' in x:
            try: return (2, float(x.split('(')[1].strip(')')))
            except: return (2, 99)
        elif 'Our Scheduler' in x:
            mode_order = {'pred': 0, 'prof': 1}
            try: mode = x.split('(')[1].strip(')')
            except: return (3, 99)
            return (3, mode_order.get(mode, 2))
        return (4, x)
    
    df['sort_key'] = df['scheduler'].apply(scheduler_sort_key)
    sort_columns = ['sort_key', 'device'] if is_per_device else ['sort_key']
    df = df.sort_values(by=sort_columns).drop(columns='sort_key')
    
    # --- Setup Output & Plotting Parameters ---
    output_dir = os.path.join(os.path.dirname(aggregated_csv_path), "plots", plot_mode)
    os.makedirs(output_dir, exist_ok=True)
    hue_col = 'device' if is_per_device else 'scheduler'
    show_legend = is_per_device

    # --- Generic Bar Plot Function ---
    def generate_barplot(y_col, title, ylabel, filename, palette, ylim=None):
        if y_col not in df.columns or df[y_col].isnull().all():
            print(f"Skipping plot '{title}': Column '{y_col}' not found or is all empty.")
            return
        plt.figure(figsize=(10, 6) if is_per_device else (7, 5))
        ax = sns.barplot(x='scheduler', y=y_col, hue=hue_col, data=df, palette=palette, legend=show_legend)
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.set_xlabel("")
        if ylim:
            ax.set_ylim(ylim)
        plt.xticks(rotation=45, ha='right')
        if show_legend:
            plt.legend(title='Device', frameon=True, bbox_to_anchor=(1.02, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, filename))
        plt.close()

    # --- Generate All Plots ---
    generate_barplot('mean_excess_latency_s', "Mean Excess Latency", "Latency (s)", "latency.png", "viridis")
    generate_barplot('mean_excess_latency_adj_s', "Adjusted Mean Excess Latency", "Latency (s)", "latency_adjusted.png", "viridis")
    generate_barplot('mean_percent_excess', "Mean Percentage Excess Latency", "Excess Latency (%)", "percent_latency.png", "Purples")
    generate_barplot('total_energy_j', "Total Energy Consumption", "Energy (J)", "energy.png", "rocket")
    generate_barplot('requests_per_joule', "Throughput Efficiency", "Requests / Joule", "requests_per_joule.png", "Blues")
    generate_barplot('frames_per_joule', "Processing Efficiency", "Frames / Joule", "frames_per_joule.png", "Greens")
    generate_barplot('percent_time_out', "Request Timeouts", "Timeouts (%)", "timeouts.png", "mako", ylim=(0, 100))

    # --- Constraint Plots ---
    constraint_metrics = [
        ('percent_requests_within_constraint', 'Requests within Latency Constraint'),
        ('percent_completed_frames_within_constraint', 'Completed Frames within Latency Constraint'),
        ('percent_requests_within_adj', 'Requests within Adjusted Constraint'),
        ('percent_completed_frames_within_adj', 'Completed Frames within Adjusted Constraint')
    ]
    for metric, title in constraint_metrics:
        generate_barplot(metric, title, "Percentage (%)", f"{metric}.png", "coolwarm", ylim=(0, 100))

    # --- Special Plots (Temperature & GPU) ---
    if is_per_device:
        # For per-device, plot mean temperature as a grouped bar chart
        generate_barplot('mean_temperature_c', 'Mean Temperature by Scheduler', 'Temperature (°C)', 'temperature_mean.png', 'autumn')
    else:
        # For overall, create a multi-metric plot showing the temperature range
        plt.figure(figsize=(8, 5))
        df_melt = df.melt(id_vars=['scheduler'], 
                         value_vars=['max_temperature_c', 'mean_temperature_c', 'min_temperature_c'],
                         var_name='metric', value_name='temperature')
        ax = sns.barplot(x='scheduler', y='temperature', hue='metric', data=df_melt,
                        palette={"max_temperature_c": "#d62728", "mean_temperature_c": "#2ca02c", "min_temperature_c": "#1f77b4"})
        ax.set_title("Temperature Metrics by Scheduler")
        ax.set_ylabel("Temperature (°C)")
        ax.set_xlabel("")
        plt.xticks(rotation=45, ha='right')
        plt.legend(title='Metric', frameon=True)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "temperature_range.png"))
        plt.close()

    # GPU Frequencies Plot
    plt.figure(figsize=(12, 7) if is_per_device else (8, 5))
    if is_per_device:
        sns.lineplot(data=df, x='scheduler', y='avg_gpu_freq_mhz', hue='device', style='device', markers=True, dashes=False, palette='coolwarm')
        plt.title("Mean GPU Frequency by Scheduler and Device")
    else:
        plt.plot(df['scheduler'], df['max_gpu_freq_mhz'], 'o-', label='Max')
        plt.plot(df['scheduler'], df['avg_gpu_freq_mhz'], 's-', label='Mean')
        plt.plot(df['scheduler'], df['min_gpu_freq_mhz'], '^-', label='Min')
        plt.legend(frameon=True)
        plt.title("GPU Frequency Ranges by Scheduler")
    plt.ylabel("Frequency (MHz)")
    plt.xlabel("")
    plt.xticks(rotation=45, ha='right')
    plt.grid(alpha=0.4)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "gpu_frequencies.png"))
    plt.close()
    
    print(f"All plots saved in: {output_dir}")

def main():
    parser = argparse.ArgumentParser(description='Generate plots from aggregated results CSV.')
    parser.add_argument('aggregated_csv_path', help='Path to an aggregated CSV file (e.g., ..._overall.csv or ..._per_device.csv)')
    args = parser.parse_args()
    
    if not os.path.exists(args.aggregated_csv_path):
        print(f"Error: Input file not found at {args.aggregated_csv_path}")
        return
        
    create_plots(args.aggregated_csv_path)

if __name__ == "__main__":
    main()
