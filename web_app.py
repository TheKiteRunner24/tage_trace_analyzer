# web_app.py
from flask import Flask, request, jsonify, Response, send_file
import io
from typing import Optional, Tuple
import analyzer
import visualizer

class MispredictionWebApp:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.app = Flask(__name__)
        self.current_results = []
        self.current_stats = {}
        self.setup_routes()
    
    def setup_routes(self):
        """Setup all Flask routes"""
        @self.app.route('/')
        def index():
            return self.get_index_html()
        
        @self.app.route('/analyze', methods=['POST'])
        def analyze():
            return self.handle_analysis()
        
        @self.app.route('/export/csv')
        def export_csv():
            return self.handle_export_csv()
        
        @self.app.route('/export/chart')
        def export_chart():
            return self.handle_export_chart()
        
        @self.app.route('/health')
        def health():
            return jsonify({'status': 'ok'})
    
    def get_index_html(self):
        """Return the HTML interface"""
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>PC Misprediction Analyzer</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body { padding: 20px; background-color: #f8f9fa; }
                .container { max-width: 1600px; }
                .card { margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .chart-container { background: white; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
                .stat-card { text-align: center; padding: 15px; border-radius: 5px; margin-bottom: 10px; }
                .stat-value { font-size: 1.8rem; font-weight: bold; }
                .stat-label { color: #6c757d; font-size: 0.9rem; }
                #loading { display: none; text-align: center; padding: 20px; }
                .chart-img { max-width: 100%; height: auto; }
                table { font-size: 0.9rem; }
                .table-container { 
                    max-height: 500px; 
                    overflow-y: auto; 
                    position: relative;
                }
                .table-container table thead {
                    position: sticky;
                    top: 0;
                    z-index: 10;
                    background-color: #343a40 !important;
                }
                .pc-addr { font-family: monospace; }
                .pc-orig { color: #666; font-size: 0.8em; }
                .sticky-header th {
                    position: sticky;
                    top: 0;
                    background-color: #343a40;
                    color: white;
                    z-index: 100;
                }
                .table-container::-webkit-scrollbar {
                    width: 8px;
                }
                .table-container::-webkit-scrollbar-track {
                    background: #f1f1f1;
                    border-radius: 4px;
                }
                .table-container::-webkit-scrollbar-thumb {
                    background: #888;
                    border-radius: 4px;
                }
                .table-container::-webkit-scrollbar-thumb:hover {
                    background: #555;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="mb-4">TAGE Trace Analyzer</h1>
                
                <!-- Control Panel -->
                <div class="card">
                    <div class="card-header bg-primary text-white">
                        <h5 class="mb-0">Analysis Settings</h5>
                    </div>
                    <div class="card-body">
                        <form id="analysisForm" class="row g-3">
                            <div class="col-md-3">
                                <label for="topN" class="form-label">Top N PCs</label>
                                <input type="number" class="form-control" id="topN" value="20" min="1" max="100">
                            </div>
                            <div class="col-md-3">
                                <label for="minBranches" class="form-label">Minimum Branches</label>
                                <input type="number" class="form-control" id="minBranches" value="10" min="1">
                            </div>
                            <div class="col-md-3">
                                <label for="tickStart" class="form-label">Tick Start (Optional)</label>
                                <input type="number" class="form-control" id="tickStart" placeholder="Start tick">
                            </div>
                            <div class="col-md-3">
                                <label for="tickEnd" class="form-label">Tick End (Optional)</label>
                                <input type="number" class="form-control" id="tickEnd" placeholder="End tick">
                            </div>
                            <div class="col-12">
                                <button type="submit" class="btn btn-primary">Analyze</button>
                                <button type="button" id="exportCsv" class="btn btn-success">Export CSV</button>
                                <button type="button" id="exportChart" class="btn btn-info">Export PNG</button>
                                <div id="loading" class="mt-3">
                                    <div class="spinner-border text-primary" role="status">
                                        <span class="visually-hidden">Loading...</span>
                                    </div>
                                    <span class="ms-2">Analyzing data...</span>
                                </div>
                            </div>
                        </form>
                    </div>
                </div>
                
                <!-- Statistics -->
                <div class="row mt-4" id="statsRow" style="display: none;">
                    <div class="col-md-3">
                        <div class="stat-card bg-light">
                            <div class="stat-value text-primary" id="totalPCs">0</div>
                            <div class="stat-label">PCs Analyzed</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-card bg-light">
                            <div class="stat-value text-success" id="totalBranches">0</div>
                            <div class="stat-label">Total Branches</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-card bg-light">
                            <div class="stat-value text-danger" id="totalMispred">0</div>
                            <div class="stat-label">Mispredictions</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-card bg-light">
                            <div class="stat-value text-warning" id="avgRate">0%</div>
                            <div class="stat-label">Avg Mispred Rate</div>
                        </div>
                    </div>
                </div>
                
                <!-- Chart Container -->
                <div class="chart-container mt-4" id="chartContainer" style="display: none;">
                    <h5>Analysis Charts</h5>
                    <div id="charts">
                        <img id="chartImage" class="chart-img" src="" alt="Analysis Chart">
                    </div>
                </div>
                
                <!-- Results Table -->
                <div class="card mt-4" id="resultsTable" style="display: none;">
                    <div class="card-header bg-secondary text-white">
                        <h5 class="mb-0">Detailed Results</h5>
                    </div>
                    <div class="card-body p-0">
                        <div class="table-container">
                            <table class="table table-striped table-hover mb-0">
                                <thead class="table-dark sticky-header">
                                    <tr>
                                        <th style="position: sticky; top: 0; background-color: #343a40;">Rank</th>
                                        <th style="position: sticky; top: 0; background-color: #343a40;">PC</th>
                                        <th style="position: sticky; top: 0; background-color: #343a40;">Start PC</th>
                                        <th style="position: sticky; top: 0; background-color: #343a40;">Count</th>
                                        <th style="position: sticky; top: 0; background-color: #343a40;">Mispred Count</th>
                                        <th style="position: sticky; top: 0; background-color: #343a40;">Mispred Rate</th>
                                    </tr>
                                </thead>
                                <tbody id="resultsBody">
                                    <!-- Results will be inserted here -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
            
            <script>
                document.getElementById('analysisForm').addEventListener('submit', function(e) {
                    e.preventDefault();
                    analyze();
                });
                
                document.getElementById('exportCsv').addEventListener('click', function() {
                    exportCsv();
                });
                
                document.getElementById('exportChart').addEventListener('click', function() {
                    exportChart();
                });
                
                function showLoading(show) {
                    document.getElementById('loading').style.display = show ? 'block' : 'none';
                }
                
                function analyze() {
                    showLoading(true);
                    
                    const formData = {
                        top_n: document.getElementById('topN').value,
                        min_branches: document.getElementById('minBranches').value,
                        tick_start: document.getElementById('tickStart').value || null,
                        tick_end: document.getElementById('tickEnd').value || null
                    };
                    
                    fetch('/analyze', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(formData)
                    })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Network response was not ok');
                        }
                        return response.json();
                    })
                    .then(data => {
                        showLoading(false);
                        
                        if (data.error) {
                            alert('Error: ' + data.error);
                            return;
                        }
                        
                        // Update statistics
                        document.getElementById('statsRow').style.display = 'flex';
                        document.getElementById('totalPCs').textContent = data.stats.total_pcs;
                        document.getElementById('totalBranches').textContent = data.stats.total_count.toLocaleString();
                        document.getElementById('totalMispred').textContent = data.stats.total_mispred.toLocaleString();
                        document.getElementById('avgRate').textContent = data.stats.avg_rate.toFixed(2) + '%';
                        
                        // Show chart
                        document.getElementById('chartContainer').style.display = 'block';
                        if (data.chart_image) {
                            document.getElementById('chartImage').src = data.chart_image;
                            document.getElementById('chartImage').style.display = 'block';
                        } else {
                            document.getElementById('chartImage').style.display = 'none';
                        }
                        
                        // Show results table
                        document.getElementById('resultsTable').style.display = 'block';
                        const tbody = document.getElementById('resultsBody');
                        tbody.innerHTML = '';
                        
                        data.results.forEach((item, index) => {
                            const row = document.createElement('tr');
                            row.innerHTML = `
                                <td>${index + 1}</td>
                                <td><code class="pc">${item.pc}</code></td>
                                <td><code class="startPc">${item.startPc}</code></td>
                                <td>${item.total.toLocaleString()}</td>
                                <td>${item.mispred.toLocaleString()}</td>
                                <td>${item.rate.toFixed(2)}%</td>
                            `;
                            tbody.appendChild(row);
                        });
                    })
                    .catch(error => {
                        showLoading(false);
                        console.error('Error:', error);
                        alert('Analysis failed: ' + error.message);
                    });
                }
                
                function exportCsv() {
                    window.location.href = '/export/csv?' + new URLSearchParams({
                        top_n: document.getElementById('topN').value,
                        min_branches: document.getElementById('minBranches').value,
                        tick_start: document.getElementById('tickStart').value || '',
                        tick_end: document.getElementById('tickEnd').value || ''
                    });
                }
                
                function exportChart() {
                    window.location.href = '/export/chart?' + new URLSearchParams({
                        top_n: document.getElementById('topN').value,
                        min_branches: document.getElementById('minBranches').value,
                        tick_start: document.getElementById('tickStart').value || '',
                        tick_end: document.getElementById('tickEnd').value || ''
                    });
                }
                
                // Perform initial analysis on page load
                window.addEventListener('DOMContentLoaded', function() {
                    analyze();
                });
            </script>
        </body>
        </html>
        '''
    
    def handle_analysis(self):
        """Handle analysis request from web interface"""
        try:
            data = request.json
            print(f"Received analysis request: {data}")
            
            top_n = int(data.get('top_n', 20))
            min_branches = int(data.get('min_branches', 10))
            
            tick_range = None
            tick_start = data.get('tick_start')
            tick_end = data.get('tick_end')
            
            if tick_start and tick_end:
                try:
                    tick_range = (int(tick_start), int(tick_end))
                    print(f"Using tick range: {tick_range}")
                except ValueError:
                    print("Invalid tick range values")
            
            # Perform analysis
            print(f"Starting analysis with top_n={top_n}, min_branches={min_branches}")
            results = analyzer.analyze_mispredictions(
                self.db_path, top_n * 3, tick_range, min_branches
            )
            results = results[:top_n]  # Final limit
            
            if not results:
                return jsonify({
                    'error': 'No data found with current filters. Try reducing Minimum Branches.'
                })
            
            print(f"Analysis completed: found {len(results)} PCs")
            
            # Calculate statistics
            total_count = sum(r[2] for r in results)  # r[2] is total count
            total_mispred = sum(r[3] for r in results)   # r[3] is mispred count
            avg_rate = (total_mispred / total_count * 100) if total_count > 0 else 0
            
            # Store for export
            self.current_results = results
            self.current_stats = {
                'total_pcs': len(results),
                'total_count': total_count,
                'total_mispred': total_mispred,
                'avg_rate': round(avg_rate, 2)
            }
            
            # Format results for JSON
            formatted_results = []
            for i, (pc, startPc, total, mispred, rate) in enumerate(results):
                formatted_results.append({
                    'rank': i + 1,
                    'pc': hex(pc),
                    'startPc': hex(startPc),
                    'total': total,
                    'mispred': mispred,
                    'rate': round(rate * 100, 2)
                })
            
            # Create chart
            print("Generating chart...")
            chart_image = visualizer.create_static_chart(results)
            print("Chart generated successfully")
            
            return jsonify({
                'results': formatted_results,
                'stats': self.current_stats,
                'chart_image': chart_image
            })
            
        except Exception as e:
            print(f"Error during analysis: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)})
    
    def handle_export_csv(self):
        """Handle CSV export request"""
        try:
            # Get parameters from request
            top_n = int(request.args.get('top_n', 20))
            min_branches = int(request.args.get('min_branches', 10))
            
            tick_range = None
            tick_start = request.args.get('tick_start')
            tick_end = request.args.get('tick_end')
            
            if tick_start and tick_end:
                try:
                    tick_range = (int(tick_start), int(tick_end))
                except ValueError:
                    pass
            
            # Perform fresh analysis
            results = analyzer.analyze_mispredictions(
                self.db_path, top_n, tick_range, min_branches
            )
            
            # Create CSV
            output = io.StringIO()
            output.write('Rank,PC,Start PC,Count,Mispred Count,Mispred Rate (%)\n')
            
            for i, (pc, startPc, total, mispred, rate) in enumerate(results, 1):
                output.write(f'{i},{hex(pc)},{hex(startPc)},{total},{mispred},{rate*100:.2f}\n')
            
            output.seek(0)
            
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': 'attachment;filename=misprediction_analysis.csv'}
            )
        except Exception as e:
            return jsonify({'error': str(e)})
    
    def handle_export_chart(self):
        """Handle chart export request"""
        try:
            # Get parameters from request
            top_n = int(request.args.get('top_n', 20))
            min_branches = int(request.args.get('min_branches', 10))
            
            tick_range = None
            tick_start = request.args.get('tick_start')
            tick_end = request.args.get('tick_end')
            
            if tick_start and tick_end:
                try:
                    tick_range = (int(tick_start), int(tick_end))
                except ValueError:
                    pass
            
            # Perform fresh analysis
            results = analyzer.analyze_mispredictions(
                self.db_path, top_n, tick_range, min_branches
            )
            
            # Create chart
            chart_buf = visualizer.create_export_chart(results)
            
            if chart_buf:
                return send_file(
                    chart_buf,
                    mimetype='image/png',
                    as_attachment=True,
                    download_name='misprediction_chart.png'
                )
            else:
                return jsonify({'error': 'Failed to create chart'})
        except Exception as e:
            return jsonify({'error': str(e)})

    def run(self, host: str = '127.0.0.1', port: int = 5000):
        """Run the Flask web application"""
        print(f"\n{'='*60}")
        print("TAGE Trace Analyzer - Web Interface")
        print(f"{'='*60}")
        print(f"Server starting at: http://{host}:{port}")
        print(f"Database: {self.db_path}")
        print(f"\nInstructions:")
        print("1. Open your web browser and go to the URL above")
        print("2. Adjust parameters as needed")
        print("3. Click 'Analyze' to see results")
        print("4. Use 'Export CSV' or 'Export PNG' to save results")
        print(f"{'='*60}")
        
        try:
            self.app.run(host=host, port=port, debug=False)
        except Exception as e:
            print(f"Failed to start server: {e}")
            print(f"\nPossible issues:")
            print(f"1. Port {port} might be in use. Try a different port")
            print("2. Check if database file exists and is accessible")
            print("3. Make sure Flask is installed: pip install flask")