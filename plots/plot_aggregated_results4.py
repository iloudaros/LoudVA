import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
import os

def plot_results(overall_df):
    """
    Generates and saves four separate publication-quality plot files using seaborn styling:
    Energy Efficiency, Mean Percentage Excess Latency, Request Compliance, 
    and Mean Excess Latency in Seconds.
    """
    
    # ============ SEABORN CONFIGURATION ============
    # Set seaborn style optimized for publication (matching first function)
    sns.set_theme(style="ticks", context="paper")
    sns.set_context("paper", font_scale=1.5, rc={"lines.linewidth": 2.0})
    
    # Use seaborn color palette for consistency
    colors = sns.color_palette("tab10")
    color_prof = colors[0]  # Blue
    color_pred = colors[1]  # Orange

    # --- Data Preparation ---
    overall_df['throughput_level'] = overall_df['aggregation_group'].str.extract(r'\(T-(\d+)\)').astype(int)
    
    df_prof = overall_df[overall_df['aggregation_group'].str.contains('loud_prof')].sort_values('throughput_level')
    df_pred = overall_df[overall_df['aggregation_group'].str.contains('loud_pred')].sort_values('throughput_level')

    if df_prof.empty or df_pred.empty:
        print("Error: Could not find data for both 'loud_prof' and 'loud_pred' in the aggregated file.")
        return

    throughput_levels = sorted(df_prof['throughput_level'].unique())
    output_dir = os.path.dirname(overall_df.attrs['source_path'])

    # ============ PLOT 1: Energy Efficiency (Frames per Joule) ============
    fig1, ax1 = plt.subplots(figsize=(10, 10), dpi=300)
    
    ax1.plot(throughput_levels, df_prof['frames_per_joule'], 
             marker='o', linestyle='-', 
             label='Loud Prof (Profiling)', 
             color=color_prof,
             linewidth=2.0, markersize=7,
             markeredgewidth=1.0, markeredgecolor='white',
             alpha=0.85, zorder=3)
    
    ax1.plot(throughput_levels, df_pred['frames_per_joule'], 
             marker='s', linestyle='-', 
             label='Loud Pred (Prediction)', 
             color=color_pred,
             linewidth=2.0, markersize=7,
             markeredgewidth=1.0, markeredgecolor='white',
             alpha=0.85, zorder=3)
    
    # Enhanced axis labels
    ax1.set_xlabel('Max Throughput Level (frames/s)', fontsize=14, fontweight='bold', labelpad=8)
    ax1.set_ylabel('Mean Frames per Joule', fontsize=14, fontweight='bold', labelpad=8)
    ax1.set_ylim(0, 1)
    
    # Professional legend styling
    legend = ax1.legend(fontsize=10, 
                       frameon=True, 
                       shadow=False,
                       fancybox=False,
                       edgecolor='black',
                       framealpha=0.95,
                       loc='best')
    legend.get_frame().set_linewidth(0.8)
    
    # Subtle grid
    ax1.grid(True, alpha=0.25, linestyle='--', linewidth=0.6, zorder=0)
    
    # Professional tick styling
    ax1.tick_params(axis='both', which='major', labelsize=11,
                   direction='out', length=4, width=0.8)
    
    # Clean up spines
    sns.despine(ax=ax1, top=True, right=True, trim=True)
    ax1.spines['left'].set_linewidth(0.8)
    ax1.spines['bottom'].set_linewidth(0.8)
    
    plt.tight_layout()
    efficiency_output_path = os.path.join(output_dir, 'experiment4_efficiency_plot.png')
    plt.savefig(efficiency_output_path, dpi=300, bbox_inches='tight')
    print(f"Energy Efficiency (Frames per Joule) plot saved to: {efficiency_output_path}")
    plt.close(fig1)

    # ============ PLOT 2: Mean Percentage Excess Latency (Broken Axis) ============
    fig2, (ax_top, ax_bottom) = plt.subplots(2, 1, sharex=True, figsize=(10, 10), 
                                              dpi=300, gridspec_kw={'height_ratios': [1, 1]})
    fig2.subplots_adjust(hspace=0.1)

    max_y_value = max(df_prof['mean_percent_excess'].max(), df_pred['mean_percent_excess'].max())
    ax_bottom.set_ylim(-5, 40)
    ax_top.set_ylim(80, max_y_value + 20)

    # Plot on both axes with consistent styling
    for ax in [ax_top, ax_bottom]:
        ax.plot(throughput_levels, df_prof['mean_percent_excess'], 
                marker='o', linestyle='-', 
                color=color_prof,
                linewidth=2.0, markersize=7,
                markeredgewidth=1.0, markeredgecolor='white',
                alpha=0.85, zorder=3,
                label='Loud Prof (Profiling)' if ax == ax_top else '')
        
        ax.plot(throughput_levels, df_pred['mean_percent_excess'], 
                marker='s', linestyle='-', 
                color=color_pred,
                linewidth=2.0, markersize=7,
                markeredgewidth=1.0, markeredgecolor='white',
                alpha=0.85, zorder=3,
                label='Loud Pred (Prediction)' if ax == ax_top else '')
    
    # Add value labels for extreme points
    for ax in [ax_top, ax_bottom]:
        for line in ax.lines:
            for x, y in zip(line.get_xdata(), line.get_ydata()):
                if y >= 80 or y <= 40:
                    ax.text(x, y + 2, f'{y:.1f}%', 
                           ha='center', va='bottom', 
                           fontsize=9, fontweight='bold',
                           bbox=dict(boxstyle='round,pad=0.3',
                                   facecolor='white',
                                   edgecolor='lightgray',
                                   alpha=0.8,
                                   linewidth=0.5))

    # Break indicators
    ax_top.spines['bottom'].set_visible(False)
    ax_bottom.spines['top'].set_visible(False)
    ax_top.xaxis.tick_top()
    ax_top.tick_params(labeltop=False, axis='x', length=0)
    ax_bottom.xaxis.tick_bottom()

    d = 0.015
    kwargs = dict(transform=ax_top.transAxes, color='k', clip_on=False, linewidth=0.8)
    ax_top.plot((-d, +d), (-d, +d), **kwargs)
    ax_top.plot((1 - d, 1 + d), (-d, +d), **kwargs)
    kwargs.update(transform=ax_bottom.transAxes)
    ax_bottom.plot((-d, +d), (1 - d, 1 + d), **kwargs)
    ax_bottom.plot((1 - d, 1 + d), (1 - d, 1 + d), **kwargs)
    
    # Enhanced labels
    ax_bottom.set_xlabel('Max Throughput Level (frames/s)', fontsize=14, fontweight='bold', labelpad=8)
    fig2.text(0.04, 0.5, 'Mean Excess Latency (%)', 
             va='center', rotation='vertical', 
             fontsize=14, fontweight='bold')
    
    # Reference line
    ax_bottom.axhline(0, color='red', linestyle=':', linewidth=1.5, 
                     label='Deadline Met', alpha=0.7, zorder=2)
    
    # Professional legend
    legend = ax_top.legend(fontsize=10, 
                          frameon=True,
                          shadow=False,
                          fancybox=False,
                          edgecolor='black',
                          framealpha=0.95,
                          loc='upper left')
    legend.get_frame().set_linewidth(0.8)
    
    # Grid and ticks
    for ax in [ax_top, ax_bottom]:
        ax.grid(True, alpha=0.25, linestyle='--', linewidth=0.6, zorder=0)
        ax.tick_params(axis='both', which='major', labelsize=11,
                      direction='out', length=4, width=0.8)
        # Only despine right side for broken axis plot
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_linewidth(0.8)
    ax_bottom.spines['bottom'].set_linewidth(0.8)
    
    plt.tight_layout()
    latency_output_path = os.path.join(output_dir, 'experiment4_latency_percent_plot.png')
    plt.savefig(latency_output_path, dpi=300, bbox_inches='tight')
    print(f"Mean Percentage Excess Latency plot saved to: {latency_output_path}")
    plt.close(fig2)

    # ============ PLOT 3: Request Compliance ============
    fig3, ax3 = plt.subplots(figsize=(10, 10), dpi=300)
    
    ax3.plot(throughput_levels, df_prof['percent_requests_within_constraint'], 
             marker='o', linestyle='-', 
             label='Loud Prof (Profiling)', 
             color=color_prof,
             linewidth=2.0, markersize=7,
             markeredgewidth=1.0, markeredgecolor='white',
             alpha=0.85, zorder=3)
    
    ax3.plot(throughput_levels, df_pred['percent_requests_within_constraint'], 
             marker='s', linestyle='-', 
             label='Loud Pred (Prediction)', 
             color=color_pred,
             linewidth=2.0, markersize=7,
             markeredgewidth=1.0, markeredgecolor='white',
             alpha=0.85, zorder=3)
    
    # Reference line
    ax3.axhline(100, color='green', linestyle=':', linewidth=1.5, 
               label='100% Compliant', alpha=0.7, zorder=2)
    
    # Enhanced axis labels
    ax3.set_xlabel('Max Throughput Level (frames/s)', fontsize=14, fontweight='bold', labelpad=8)
    ax3.set_ylabel('Requests Within Constraint (%)', fontsize=14, fontweight='bold', labelpad=8)
    ax3.set_ylim(50, 105)
    
    # Professional legend
    legend = ax3.legend(fontsize=10, 
                       frameon=True,
                       shadow=False,
                       fancybox=False,
                       edgecolor='black',
                       framealpha=0.95,
                       loc='best')
    legend.get_frame().set_linewidth(0.8)
    
    # Grid and styling
    ax3.grid(True, alpha=0.25, linestyle='--', linewidth=0.6, zorder=0)
    ax3.tick_params(axis='both', which='major', labelsize=11,
                   direction='out', length=4, width=0.8)
    
    sns.despine(ax=ax3, top=True, right=True, trim=True)
    ax3.spines['left'].set_linewidth(0.8)
    ax3.spines['bottom'].set_linewidth(0.8)
    
    plt.tight_layout()
    compliance_output_path = os.path.join(output_dir, 'experiment4_compliance_plot.png')
    plt.savefig(compliance_output_path, dpi=300, bbox_inches='tight')
    print(f"Request Compliance plot saved to: {compliance_output_path}")
    plt.close(fig3)

    # ============ PLOT 4: Mean Excess Latency in Seconds ============
    fig4, ax4 = plt.subplots(figsize=(10, 10), dpi=300)
    
    ax4.plot(throughput_levels, df_prof['mean_excess_latency_s'], 
             marker='o', linestyle='-', 
             label='Loud Prof (Profiling)', 
             color=color_prof,
             linewidth=2.0, markersize=7,
             markeredgewidth=1.0, markeredgecolor='white',
             alpha=0.85, zorder=3)
    
    ax4.plot(throughput_levels, df_pred['mean_excess_latency_s'], 
             marker='s', linestyle='-', 
             label='Loud Pred (Prediction)', 
             color=color_pred,
             linewidth=2.0, markersize=7,
             markeredgewidth=1.0, markeredgecolor='white',
             alpha=0.85, zorder=3)
    
    # Reference line
    ax4.axhline(0, color='red', linestyle=':', linewidth=1.5, 
               label='Deadline Met', alpha=0.7, zorder=2)
    
    # Enhanced axis labels
    ax4.set_xlabel('Max Throughput Level (frames/s)', fontsize=14, fontweight='bold', labelpad=8)
    ax4.set_ylabel('Mean Excess Latency (s)', fontsize=14, fontweight='bold', labelpad=8)
    
    # Professional legend
    legend = ax4.legend(fontsize=10, 
                       frameon=True,
                       shadow=False,
                       fancybox=False,
                       edgecolor='black',
                       framealpha=0.95,
                       loc='best')
    legend.get_frame().set_linewidth(0.8)
    
    # Grid and styling
    ax4.grid(True, alpha=0.25, linestyle='--', linewidth=0.6, zorder=0)
    ax4.tick_params(axis='both', which='major', labelsize=11,
                   direction='out', length=4, width=0.8)
    
    sns.despine(ax=ax4, top=True, right=True, trim=True)
    ax4.spines['left'].set_linewidth(0.8)
    ax4.spines['bottom'].set_linewidth(0.8)
    
    plt.tight_layout()
    latency_seconds_output_path = os.path.join(output_dir, 'experiment4_latency_seconds_plot.png')
    plt.savefig(latency_seconds_output_path, dpi=300, bbox_inches='tight')
    print(f"Absolute Excess Latency plot saved to: {latency_seconds_output_path}")
    plt.close(fig4)

def main():
    parser = argparse.ArgumentParser(description='Generate separate, publication-quality plots for Experiment 4.')
    parser.add_argument('aggregated_report_path', help='Path to the ..._aggregated_overall.csv file.')
    args = parser.parse_args()

    try:
        df = pd.read_csv(args.aggregated_report_path, sep=';', decimal=',')
        df.attrs['source_path'] = args.aggregated_report_path
    except FileNotFoundError:
        print(f"Error: Aggregated report file not found at {args.aggregated_report_path}")
        return
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return
        
    plot_results(df)

if __name__ == "__main__":
    main()
