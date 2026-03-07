import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import ttest_ind

# 1. Load your data (replace 'data.csv' with your actual filename)
df = pd.read_csv(r"D:\Chrome\ratios.csv")

# 2. Identify the 6 ratio columns (assuming they start from the 3rd column)
value_cols = df.columns[2:8]

# 3. Define the 4 pairs of groups based on Tissue and Day
base_groups = ['Gut_D10', 'Gut_D40', 'Ovary_D10', 'Ovary_D40']

# Helper function to convert p-values to significance asterisks
def get_asterisks(p):
    if p < 0.001: return '***'
    elif p < 0.01:  return '**'
    elif p < 0.05:  return '*'
    else:           return 'ns'

# 4. Loop through each base group to create 4 separate figures
for base in base_groups:
    group_rapa = f'{base}_Rapa'
    group_ctrl = f'{base}_Ctrl'
    
    # Filter the dataframe for the current pair
    df_pair = df[df['group'].isin([group_ctrl, group_rapa])]
    
    # Create a figure with a 2x3 grid of subplots
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    fig.suptitle(f'Comparison: {group_ctrl} vs {group_rapa}', fontsize=16, fontweight='bold')
    
    # Flatten the 2x3 axes array to a 1D array for easy iteration
    axes = axes.flatten()
    
    # Loop through each of the 6 variables and plot
    for i, col in enumerate(value_cols):
        ax = axes[i]
        
        # Plot the bars with Standard Deviation error bars
        sns.barplot(
            data=df_pair, 
            x='group', 
            y=col, 
            ax=ax, 
            capsize=0.1, 
            errorbar='sd', 
            order=[group_ctrl, group_rapa], 
            palette=['#A0C4FF', '#FFADAD'],
            alpha=0.7  # Make bars slightly transparent
        )
        
        # Overlay the individual data points
        sns.stripplot(
            data=df_pair, 
            x='group', 
            y=col, 
            ax=ax, 
            order=[group_ctrl, group_rapa], 
            color='black',    # Color of the data points
            alpha=0.8,        # Transparency of the points
            jitter=True,      # Spread points out slightly so they don't overlap entirely
            size=6            # Size of the points
        )
        
        # Extract data for the t-test
        data_ctrl = df_pair[df_pair['group'] == group_ctrl][col].dropna()
        data_rapa = df_pair[df_pair['group'] == group_rapa][col].dropna()
        
        # Perform Independent t-test
        if len(data_ctrl) > 0 and len(data_rapa) > 0:
            stat, p = ttest_ind(data_ctrl, data_rapa)
            sig_label = get_asterisks(p)
            
            # Calculate positions for the significance line and text
            y_max = df_pair[col].max()
            y_min = df_pair[col].min()
            y_range = y_max - y_min if (y_max - y_min) > 0 else y_max * 0.1
            
            line_y = y_max + (y_range * 0.15)
            text_y = line_y + (y_range * 0.02)
            
            # Draw the line and text
            ax.plot([0, 1], [line_y, line_y], color='black', lw=1.2)
            ax.text(0.5, text_y, sig_label, ha='center', va='bottom', fontsize=14, fontweight='bold')
            
            # Extend y-axis limit slightly so the text doesn't get cut off
            ax.set_ylim(bottom=min(0, y_min - y_range*0.1), top=text_y + y_range*0.2)

        # Formatting the subplot
        ax.set_title(col, fontsize=12)
        ax.set_xlabel('')
        ax.set_ylabel('Ratio' if i % 3 == 0 else '') # Show y-label only on the left-most plots
        
    plt.tight_layout()
    # plt.savefig(f'{base}_comparison.png', dpi=300) # Uncomment to save
    plt.show()