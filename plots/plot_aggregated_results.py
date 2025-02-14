import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import argparse

def create_individual_plots(aggregated_csv_path):
    # Set up plotting style
    sns.set_theme(style="whitegrid", context="paper", font_scale=1.2)
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['DejaVu Sans', 'Arial'],
        'figure.dpi': 300,
        'axes.titlesize': 11,
        'axes.labelsize': 10,
        'xtick.labelsize': 9,
        'ytick.labelsize': 9,
        'legend.fontsize': 9,
        'axes.linewidth': 0.8,
        'grid.linewidth': 0.4
    })

    # Load data
    df = pd.read_csv(aggregated_csv_path)

    # Custom sorting function
    def scheduler_sort_key(x):
        if 'No Scheduler' in x:
            return (0, x)
        elif 'Fixed Batch' in x:
            return (1, float(x.split('(')[1].strip(')')))
        elif 'Interval' in x:
            return (2, float(x.split('(')[1].strip(')')))
        elif 'Our Scheduler' in x:
            mode_order = {'pred': 0, 'prof': 1}
            mode = x.split('(')[1].strip(')')
            return (3, mode_order.get(mode, 2))
        return (4, x)
    
    # Apply custom sorting
    df['sort_key'] = df['scheduler'].apply(scheduler_sort_key)
    df = df.sort_values('sort_key').drop(columns='sort_key')
    
    # Create output directory
    output_dir = os.path.join(os.path.dirname(aggregated_csv_path), "plots")
    os.makedirs(output_dir, exist_ok=True)

    # Plot 1: Latency
    plt.figure(figsize=(6, 4))
    ax = sns.barplot(x='scheduler', y='mean_excess_latency_s', data=df, 
                     hue='scheduler', palette="viridis", legend=False)
    ax.set_title("Mean Excess Latency by Scheduler")
    ax.set_ylabel("Latency (s)")
    ax.set_xlabel("")
    plt.xticks(rotation=45, ha='right')
    plt.ylim(0, 20)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "latency.png"))
    plt.close()

    # Plot 1a: Adjusted Latency
    plt.figure(figsize=(6, 4))
    ax = sns.barplot(x='scheduler', y='mean_excess_latency_adj_s', data=df, 
                     hue='scheduler', palette="viridis", legend=False)
    ax.set_title("Adjusted Mean Excess Latency by Scheduler")
    ax.set_ylabel("Latency (s)")
    ax.set_xlabel("")
    plt.xticks(rotation=45, ha='right')
    plt.ylim(0, 20)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "latency_adjusted.png"))
    plt.close()

    # Plot 2: Energy Consumption
    plt.figure(figsize=(6, 4))
    ax = sns.barplot(x='scheduler', y='total_energy_j', data=df, 
                     hue='scheduler', palette="rocket", legend=False)
    ax.set_title("Total Energy Consumption by Scheduler")
    ax.set_ylabel("Energy (J)")
    ax.set_xlabel("")
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "energy.png"))
    plt.close()

    # Plot 3: Requests per Joule
    plt.figure(figsize=(6, 4))
    ax = sns.barplot(x='scheduler', y='requests_per_joule', data=df,
                    hue='scheduler', palette="Blues", legend=False)
    ax.set_title("Throughput Efficiency - Requests per Joule")
    ax.set_ylabel("Requests/Joule")
    ax.set_xlabel("")
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "requests_per_joule.png"))
    plt.close()

    # Plot 4: Frames per Joule
    plt.figure(figsize=(6, 4))
    ax = sns.barplot(x='scheduler', y='frames_per_joule', data=df,
                    hue='scheduler', palette="Greens", legend=False)
    ax.set_title("Processing Efficiency - Frames per Joule")
    ax.set_ylabel("Frames/Joule")
    ax.set_xlabel("")
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "frames_per_joule.png"))
    plt.close()

    # Plot 5: Temperature Ranges
    plt.figure(figsize=(8, 5))
    df_melt = df.melt(id_vars=['scheduler'], 
                     value_vars=['max_temperature_c', 'mean_temperature_c', 'min_temperature_c'],
                     var_name='metric', value_name='temperature')
    ax = sns.barplot(x='scheduler', y='temperature', hue='metric', data=df_melt,
                    palette=["#d62728", "#2ca02c", "#1f77b4"])
    ax.set_title("Temperature Metrics by Scheduler")
    ax.set_ylabel("Temperature (°C)")
    ax.set_xlabel("")
    plt.xticks(rotation=45, ha='right')
    plt.legend(title='Metric', frameon=True)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "temperature.png"))
    plt.close()

    # Plot 6: GPU Frequencies
    plt.figure(figsize=(7, 4.5))
    plt.plot(df['scheduler'], df['max_gpu_freq_mhz'], 'o-', label='Max')
    plt.plot(df['scheduler'], df['avg_gpu_freq_mhz'], 's-', label='Mean')
    plt.plot(df['scheduler'], df['min_gpu_freq_mhz'], '^-', label='Min')
    plt.title("GPU Frequency Ranges by Scheduler")
    plt.ylabel("Frequency (MHz)")
    plt.xticks(rotation=45, ha='right')
    plt.legend(frameon=True)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "gpu_frequencies.png"))
    plt.close()

    # Plot 7: Timeouts
    plt.figure(figsize=(6, 4))
    ax = sns.barplot(x='scheduler', y='percent_time_out', data=df, 
                     hue='scheduler', palette="mako", legend=False)
    ax.set_title("Request Timeouts by Scheduler")
    ax.set_ylabel("Timeouts (%)")
    ax.set_xlabel("")
    plt.xticks(rotation=45, ha='right')
    plt.ylim(0, 100)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "timeouts.png"))
    plt.close()

    # Constraint Plots
    constraint_metrics = [
        ('percent_requests_within_constraint', 'Requests within Latency Constraint'),
        ('percent_frames_within_constraint', 'Frames within Latency Constraint'),
        ('percent_completed_frames_within_constraint', 'Completed Frames within Latency Constraint'),
        ('percent_requests_within_adj', 'Requests within Adjusted Constraint'),
        ('percent_frames_within_adj', 'Frames within Adjusted Constraint'),
        ('percent_completed_frames_within_adj', 'Completed Frames within Adjusted Constraint')
    ]

    for i, (metric, title) in enumerate(constraint_metrics, 8):
        plt.figure(figsize=(6, 4))
        ax = sns.barplot(x='scheduler', y=metric, data=df, 
                        hue='scheduler', palette="coolwarm", legend=False)
        ax.set_title(f"{title} by Scheduler")
        ax.set_ylabel("Percentage (%)")
        ax.set_xlabel("")
        plt.xticks(rotation=45, ha='right')
        plt.ylim(0, 100)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f"{metric}.png"))
        plt.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate individual plots from aggregated results')
    parser.add_argument('aggregated_csv_path', help='Path to aggregated CSV file')
    args = parser.parse_args()
    
    create_individual_plots(args.aggregated_csv_path)
    print(f"Plots saved in: {os.path.join(os.path.dirname(args.aggregated_csv_path), 'plots')}")
