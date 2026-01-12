# visualizer.py
import io
import base64
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple

def create_static_chart(results: List[Tuple[int, int, int, int, float]], 
                       output_file: str = None) -> str:
    """
    Create a static chart and return base64 encoded image or save to file
    
    Args:
        results: List of (orig_pc, full_pc, total, mispred, rate)
        output_file: If provided, save chart to file. Otherwise return base64 string.
    
    Returns:
        base64 encoded image string if output_file is None, otherwise None
    """
    if not results:
        return None
    
    plt.style.use('default')
    
    # Create a simpler single chart
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # Extract data - use full_pc for display
    pcs = [hex(r[1]) for r in results]  # r[1] is full_pc
    totals = [r[2] for r in results]    # r[2] is total count
    mispreds = [r[3] for r in results]  # r[3] is mispred count
    rates = [r[4] * 100 for r in results]  # r[4] is mispred_rate
    
    indices = np.arange(len(pcs))
    
    # Chart 1: Misprediction Count
    bars1 = ax1.bar(indices, mispreds, color='#ef4444', alpha=0.8)
    ax1.set_xlabel('PC Address (Full)')
    ax1.set_ylabel('Misprediction Count')
    ax1.set_title('Top PCs by Misprediction Count')
    ax1.set_xticks(indices)
    
    # Truncate PC display if too long
    if len(pcs) > 15:
        display_pcs = []
        for pc in pcs:
            if len(pc) > 10:
                display_pcs.append(f"{pc[:8]}...")
            else:
                display_pcs.append(pc)
    else:
        display_pcs = pcs
        
    ax1.set_xticklabels(display_pcs, rotation=45, ha='right', fontsize=8)
    ax1.grid(True, alpha=0.3)
    
    # Add values on top of bars
    for i, v in enumerate(mispreds):
        ax1.text(i, v + max(mispreds)*0.01, f'{v:,}', ha='center', va='bottom', fontsize=7)
    
    # Chart 2: Misprediction Rate
    bars2 = ax2.bar(indices, rates, color='#f59e0b', alpha=0.8)
    ax2.set_xlabel('PC Address (Full)')
    ax2.set_ylabel('Misprediction Rate (%)')
    ax2.set_title('Top PCs by Misprediction Rate')
    ax2.set_xticks(indices)
    ax2.set_xticklabels(display_pcs, rotation=45, ha='right', fontsize=8)
    ax2.grid(True, alpha=0.3)
    
    # Add values on top of bars
    for i, v in enumerate(rates):
        ax2.text(i, v + max(rates)*0.01, f'{v:.1f}%', ha='center', va='bottom', fontsize=7)
    
    # Chart 3: Total Branches
    bars3 = ax3.bar(indices, totals, color='#3b82f6', alpha=0.8)
    ax3.set_xlabel('PC Address (Full)')
    ax3.set_ylabel('Total Branch Count')
    ax3.set_title('Top PCs by Total Branches')
    ax3.set_xticks(indices)
    ax3.set_xticklabels(display_pcs, rotation=45, ha='right', fontsize=8)
    ax3.grid(True, alpha=0.3)
    
    # Add values on top of bars
    for i, v in enumerate(totals):
        ax3.text(i, v + max(totals)*0.01, f'{v:,}', ha='center', va='bottom', fontsize=7)
    
    # Chart 4: Scatter plot
    scatter = ax4.scatter(totals, mispreds, c=rates, s=50, cmap='RdYlGn_r', alpha=0.8)
    ax4.set_xlabel('Total Branches')
    ax4.set_ylabel('Misprediction Count')
    ax4.set_title('Mispredictions vs Total Branches')
    ax4.grid(True, alpha=0.3)
    
    # Add colorbar
    plt.colorbar(scatter, ax=ax4).set_label('Misprediction Rate (%)')
    
    # Add labels to some points
    for i, (pc, x, y) in enumerate(zip(display_pcs[:5], totals[:5], mispreds[:5])):
        ax4.annotate(pc, (x, y), xytext=(5, 5), textcoords='offset points', fontsize=7)
    
    plt.suptitle('PC Misprediction Analysis (PCs shown as full addresses)', 
                fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    if output_file:
        # Save to file
        plt.savefig(output_file, dpi=100, bbox_inches='tight')
        plt.close(fig)
        print(f"Chart saved to: {output_file}")
        return output_file
    else:
        # Convert to base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        return f"data:image/png;base64,{img_str}"

def create_export_chart(results: List[Tuple[int, int, int, int, float]]) -> io.BytesIO:
    """
    Create a chart specifically for export (returns BytesIO object)
    
    Args:
        results: List of (orig_pc, full_pc, total, mispred, rate)
    
    Returns:
        BytesIO object containing chart image
    """
    if not results:
        return None
    
    plt.style.use('default')
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Extract data
    pcs = [hex(r[1]) for r in results]  # r[1] is full_pc
    totals = [r[2] for r in results]    # r[2] is total count
    mispreds = [r[3] for r in results]  # r[3] is mispred count
    rates = [r[4] * 100 for r in results]  # r[4] is mispred_rate
    
    indices = np.arange(len(pcs))
    
    # Create charts
    axes[0, 0].bar(indices, mispreds, color='#ef4444')
    axes[0, 0].set_title('Misprediction Count')
    axes[0, 0].set_xlabel('PC Address (Full)')
    axes[0, 0].set_xticks(indices)
    
    # Truncate long PC addresses for display
    if len(pcs) > 15:
        display_pcs = []
        for pc in pcs:
            if len(pc) > 10:
                display_pcs.append(f"{pc[:8]}...")
            else:
                display_pcs.append(pc)
    else:
        display_pcs = pcs
        
    axes[0, 0].set_xticklabels(display_pcs, rotation=45, ha='right', fontsize=8)
    
    axes[0, 1].bar(indices, rates, color='#f59e0b')
    axes[0, 1].set_title('Misprediction Rate (%)')
    axes[0, 1].set_xlabel('PC Address (Full)')
    axes[0, 1].set_xticks(indices)
    axes[0, 1].set_xticklabels(display_pcs, rotation=45, ha='right', fontsize=8)
    
    axes[1, 0].bar(indices, totals, color='#3b82f6')
    axes[1, 0].set_title('Total Branches')
    axes[1, 0].set_xlabel('PC Address (Full)')
    axes[1, 0].set_xticks(indices)
    axes[1, 0].set_xticklabels(display_pcs, rotation=45, ha='right', fontsize=8)
    
    axes[1, 1].scatter(totals, mispreds, c=rates, cmap='RdYlGn_r')
    axes[1, 1].set_title('Mispredictions vs Total Branches')
    axes[1, 1].set_xlabel('Total Branches')
    axes[1, 1].set_ylabel('Misprediction Count')
    
    plt.suptitle('PC Misprediction Analysis (PCs shown as full addresses)', 
                fontsize=12, fontweight='bold')
    plt.tight_layout()
    
    # Save to buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    
    return buf