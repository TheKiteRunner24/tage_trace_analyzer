# analyzer.py
import sqlite3
from typing import List, Tuple, Dict, Optional

def shift_pc_left(pc: int) -> int:
    """Shift PC left by 1 bit (multiply by 2) to get full address"""
    return pc << 1

def analyze_mispredictions(db_path: str, top_n: int = 20, 
                          tick_range: Optional[Tuple[int, int]] = None, 
                          min_branches: int = 10) -> List[Tuple[int, int, int, int, float]]:
    """
    Analyze PCs with most mispredictions
    
    Args:
        db_path: Database path
        top_n: Show top N PCs
        tick_range: (start, end) tick range
        min_branches: Minimum branches to include
        
    Returns:
        List[(pc, startPc, total_count, mispred_count, rate), ...]
    """
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Statistics
    pc_stats: Dict[int, Dict[str, int]] = {}
    
    print("Starting analysis of tables...")
    
    # Process 8 CondTrace tables
    for table_id in range(8):
        table_name = f"CondTrace_{table_id}"
        
        # Check if table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cur.fetchone():
            print(f"Table {table_name} does not exist, skipping")
            continue
        
        print(f"Analyzing table {table_name}...")
        
        # Build query
        where_clauses = []
        params = []
        
        if tick_range:
            where_clauses.append("STAMP BETWEEN ? AND ?")
            params.extend(tick_range)
        
        where = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        # query
        sql = f"""
        SELECT 
            CFIPC as pc,
            STARTPC_ADDR as startPc,
            COUNT(*) as total,
            SUM(MISPREDICT) as mispred
        FROM {table_name}
        {where}
        GROUP BY CFIPC
        """
        
        cur.execute(sql, params)
        
        for pc, startPc, total, mispred in cur.fetchall():
            pc_int = int(pc)
            if pc_int not in pc_stats:
                pc_stats[pc_int] = {"startPc": 0, "total": 0, "mispred": 0}
            
            pc_stats[pc_int]['startPc'] = startPc
            pc_stats[pc_int]["total"] += total
            pc_stats[pc_int]["mispred"] += mispred
    
    conn.close()
    
    if not pc_stats:
        print("No data found!")
        return []
    
    # Calculate misprediction rate and sort
    results = []
    for pc, stats in pc_stats.items():
        startPc = stats["startPc"]
        total = stats["total"]
        if total < min_branches:
            continue
        mispred = stats["mispred"]
        rate = mispred / total if total > 0 else 0
        results.append((pc, startPc, total, mispred, rate))
    
    # Sort by misprediction count (descending)
    results.sort(key=lambda x: x[3], reverse=True)  # x[3] is mispred count
    
    print(f"\nAnalyzed {len(pc_stats)} distinct PCs")
    print(f"After filtering: {len(results)} PCs")
    if results:
        total_branches = sum(r[2] for r in results)  # r[2] is total count
        total_mispred = sum(r[3] for r in results)   # r[3] is mispred count
        print(f"Total branches in filtered results: {total_branches:,}")
        print(f"Total mispredictions: {total_mispred:,}")
        if total_branches > 0:
            print(f"Overall misprediction rate: {total_mispred/total_branches*100:.2f}%\n")
    
    return results[:top_n]

def print_results(results: List[Tuple[int, int, int, int, float]]):
    """Print analysis results in formatted table"""
    if not results:
        print("No data to display")
        return
    
    print("\n" + "=" * 120)
    print("PC Misprediction Statistics (Sorted by Misprediction Count)")
    print("=" * 120)
    print(f"{'Rank':<5} {'PC':<20} {'start PC':<18} {'Total Count':<15} {'Mispred Count':<15} {'Mispred Rate':<15}")
    print("-" * 120)
    
    for i, (pc, startPc, total, mispred, rate) in enumerate(results, 1):
        print(f"{i:<5} {hex(pc):<20} {hex(startPc):<18} {total:<15} {mispred:<15} {rate*100:<8.2f}%")
    
    print("=" * 120)
    
    # Summary
    total_branches = sum(r[2] for r in results)  # r[2] is total count
    total_mispred = sum(r[3] for r in results)   # r[3] is mispred count
    if total_branches > 0:
        print(f"\nSummary for top {len(results)} PCs:")
        print(f"  Total branches: {total_branches:,}")
        print(f"  Total mispredictions: {total_mispred:,}")
        print(f"  Overall misprediction rate: {total_mispred/total_branches*100:.2f}%")

def export_to_csv(results: List[Tuple[int, int, int, int, float]], output_file: str):
    """Export results to CSV file"""
    import csv
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Rank', 'PC', 'Start PC', 
                        'Total Branches', 'Mispred Count', 'Mispred Rate (%)'])
        
        for i, (pc, startPc, total, mispred, rate) in enumerate(results, 1):
            writer.writerow([i, hex(pc), hex(startPc), total, mispred, f"{rate*100:.2f}"])
    
    print(f"CSV saved to: {output_file}")