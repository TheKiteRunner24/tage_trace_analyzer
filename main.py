#!/usr/bin/env python3
import argparse
import os
import sys
import socket
import numpy as np

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 直接导入各个模块文件
try:
    # 导入 analyzer.py 中的函数
    from analyzer import analyze_mispredictions, print_results, export_to_csv
    # 导入 visualizer.py 中的函数
    from visualizer import create_static_chart, create_export_chart
    # 导入 web_app.py 中的类
    from web_app import MispredictionWebApp
except ImportError as e:
    print(f"Import error: {e}")
    print("\n请确保以下文件存在于当前目录:")
    print("  ✓ analyzer.py - 数据分析核心逻辑")
    print("  ✓ visualizer.py - 图表生成逻辑")
    print("  ✓ web_app.py - Web界面逻辑")
    sys.exit(1)

def parse_tick_range(tick_range_str: str):
    """Parse tick range string like 'start:end'"""
    if not tick_range_str:
        return None
    try:
        start, end = map(int, tick_range_str.split(':'))
        return (start, end)
    except ValueError:
        raise ValueError("tick-range format should be start:end")

def find_available_port(start_port=5000, max_attempts=100):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        try:
            # Try to bind to the port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('127.0.0.1', port))
            sock.close()
            return port
        except OSError:
            continue
    raise RuntimeError(f"No available port found in range {start_port}-{start_port+max_attempts-1}")

def main():
    parser = argparse.ArgumentParser(
        description='Analyze PC misprediction statistics from CondTrace tables',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s --db trace.db --web
  %(prog)s --db trace.db --top 50 --plot
  %(prog)s --db trace.db --tick-range 1000:2000 --verbose

Note: PC addresses are displayed as full addresses (original PC << 1)
        '''
    )
    parser.add_argument('--db', required=True, help='SQLite database path')
    parser.add_argument('--top', type=int, default=20, help='Show top N PCs (default: 20)')
    parser.add_argument('--tick-range', help='Tick range, format: start:end')
    parser.add_argument('--plot', action='store_true', help='Generate static chart')
    parser.add_argument('--web', action='store_true', help='Start web interface')
    parser.add_argument('--host', default='127.0.0.1', help='Web server host (default: 127.0.0.1)')
    parser.add_argument('--output', default='mispred_analysis.png', help='Chart output filename')
    parser.add_argument('--csv', help='Export to CSV file')
    parser.add_argument('--min-branches', type=int, default=10, 
                       help='Minimum number of branches to consider (default: 10)')
    parser.add_argument('--verbose', action='store_true', help='Show verbose output')
    
    args = parser.parse_args()
    
    # Check if database exists
    if not os.path.exists(args.db):
        print(f"Error: Database file not found: {args.db}")
        return
    
    # Parse tick range
    tick_range = parse_tick_range(args.tick_range)
    if tick_range:
        print(f"Tick range limited to: {tick_range[0]} - {tick_range[1]}")
    
    # Web interface mode
    if args.web:
        try:
            from flask import Flask
        except ImportError:
            print("\nFlask is required for web interface.")
            print("Install with: pip install flask")
            print("\nFor command-line usage:")
            print(f"  python {sys.argv[0]} --db trace.db --top 20 --plot")
            return
        
        app = MispredictionWebApp(args.db)
        app.run(host=args.host, port=find_available_port())
        return
    
    # Command line mode
    print(f"Analyzing database: {args.db}")
    print("-" * 80)
    
    results = analyze_mispredictions(args.db, args.top, tick_range, args.min_branches)
    
    if not results:
        print("\nNo data found with current filters.")
        print("Try reducing --min-branches value.")
        return
    
    # Print results
    print_results(results)
    
    # Generate static plots
    if args.plot:
        print(f"\nGenerating chart: {args.output}")
        create_static_chart(results, args.output)
    
    # Export to CSV
    if args.csv:
        export_to_csv(results, args.csv)
    
    # Verbose statistics
    if args.verbose:
        print("\nDetailed Statistics:")
        print("-" * 50)
        
        mispred_counts = [r[3] for r in results]
        mispred_rates = [r[4] * 100 for r in results]
        total_branches = [r[2] for r in results]
        
        print(f"Number of PCs analyzed: {len(results)}")
        print(f"Total branches: {sum(total_branches):,}")
        print(f"Total mispredictions: {sum(mispred_counts):,}")
        if sum(total_branches) > 0:
            print(f"Overall misprediction rate: {sum(mispred_counts)/sum(total_branches)*100:.2f}%")
        print(f"Average misprediction rate: {np.mean(mispred_rates):.2f}%")
        print(f"Median misprediction rate: {np.median(mispred_rates):.2f}%")

if __name__ == "__main__":
    main()