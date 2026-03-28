import hashlib
import base64
import requests
import secrets
import json
import os
from flask import Flask, redirect, request, session as flask_session

# Flask App Initialization
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# --- Configuration ---
# --- Please provide your Client ID from the Parqet integration. ---
CLIENT_ID = "xxxxxxxxxxxxxxxxxxxxxxx"
REDIRECT_URI = "http://localhost:3000/callback"
AUTH_URL = "https://connect.parqet.com/oauth2/authorize"
TOKEN_URL = "https://connect.parqet.com/oauth2/token"
MCP_BASE_URL = "https://mcp.parqet.com"

# Temporary file for the PKCE Verifier
VERIFIER_FILE = "verifier.txt"

def get_base_style():
    """Defines the visual design for the analysis dashboard."""
    return """
    <style>
        body { font-family: 'Inter', -apple-system, sans-serif; background-color: #f1f5f9; color: #0f172a; margin: 0; line-height: 1.5; }
        .container { max-width: 1100px; margin: 40px auto; padding: 0 20px; }
        .card { background: white; border-radius: 16px; padding: 32px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1); border: 1px solid #e2e8f0; margin-bottom: 24px; }
        .header { background: #0f172a; color: white; padding: 20px; border-radius: 12px 12px 0 0; margin: -32px -32px 24px -32px; }
        .header h1 { margin: 0; font-size: 22px; }
        .log-entry { padding: 20px; border-radius: 10px; border-left: 5px solid #cbd5e1; background: #f8fafc; margin-bottom: 15px; }
        .log-entry.success { border-left-color: #10b981; background: #f0fdf4; }
        .log-entry.error { border-left-color: #ef4444; background: #fef2f2; }
        
        /* Improved JSON Design */
        .json-view { 
            background: #1e293b; 
            color: #e2e8f0; 
            padding: 16px; 
            border-radius: 8px; 
            overflow-x: auto; 
            font-family: 'Fira Code', 'Cascadia Code', monospace; 
            font-size: 13px; 
            margin-top: 10px; 
            line-height: 1.6; 
            border: 1px solid #334155;
            white-space: pre-wrap;
        }
        .json-key { color: #94a3b8; }
        .json-string { color: #38bdf8; }
        .json-number { color: #fbbf24; }
        .json-boolean { color: #f472b6; }
        
        .btn { display: inline-block; padding: 12px 28px; background: #2563eb; color: white; border-radius: 8px; text-decoration: none; font-weight: 600; border: none; cursor: pointer; margin-right: 8px; margin-bottom: 8px; }
        .btn:hover { background: #1d4ed8; }
        .btn-alt { background: #10b981; }
        .btn-alt:hover { background: #059669; }
        .btn-perf { background: #8b5cf6; }
        .btn-perf:hover { background: #7c3aed; }
        .label { font-weight: bold; font-size: 12px; color: #64748b; text-transform: uppercase; margin-top: 15px; display: block; }
        select { width: 100%; padding: 12px; border-radius: 8px; border: 1px solid #cbd5e1; background: white; font-size: 16px; margin-bottom: 20px; }
    </style>
    """

def format_json_html(data):
    """Formats JSON data for a prettier HTML output."""
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    # Simple highlighting via simulated regex replacement
    return f'<div class="json-view">{json_str}</div>'

@app.route('/')
def index():
    """Application landing page."""
    return f"""
    {get_base_style()}
    <div class="container">
        <div class="card">
            <div class="header"><h1>Parqet MCP RPC Client</h1></div>
            <p>Status: Ready to test the RPC endpoint <code>/mcp</code>.</p>
            <p>Action: Start authentication to load portfolios.</p>
            <br>
            <a href="/login" class="btn">Start Authentication</a>
        </div>
    </div>
    """

@app.route('/login')
def login():
    """Starts the OAuth2 process with PKCE."""
    verifier = secrets.token_urlsafe(32)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')
    with open(VERIFIER_FILE, "w") as f: f.write(verifier)
    
    params = {
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'scope': 'openid profile portfolio:read',
        'code_challenge': challenge,
        'code_challenge_method': 'S256',
        'response_type': 'code',
        'state': secrets.token_urlsafe(16),
        'audience': 'mcp.parqet.com'
    }
    auth_req = requests.Request('GET', AUTH_URL, params=params).prepare()
    return redirect(auth_req.url)

@app.route('/callback')
def callback():
    """Processes the redirect and exchanges the code for a token."""
    code = request.args.get('code')
    if not code:
        return redirect('/')
        
    if not os.path.exists(VERIFIER_FILE): 
        return "Error: PKCE Verifier file not found."
    
    with open(VERIFIER_FILE, "r") as f: 
        verifier = f.read().strip()
    
    token_response = requests.post(TOKEN_URL, data={
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'code_verifier': verifier
    }).json()

    token = token_response.get('access_token')
    if not token:
        return f"Error retrieving token: {json.dumps(token_response)}"

    flask_session['access_token'] = token
    return redirect('/selection')

@app.route('/selection')
def selection():
    """Executes the discovery chain and displays portfolio selection."""
    token = flask_session.get('access_token')
    if not token:
        return redirect('/')

    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {token}", 
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    })
    
    target_url = f"{MCP_BASE_URL}/mcp"
    rpc_logs = []

    # 1. MCP Initialization
    init_res = session.post(target_url, json={
        "jsonrpc": "2.0", "id": "init-id", "method": "initialize",
        "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "Parqet-Client", "version": "1.0.0"}}
    })
    mcp_session_id = init_res.headers.get('mcp-session-id')
    flask_session['mcp_session_id'] = mcp_session_id
    session.headers.update({"mcp-session-id": mcp_session_id})
    session.post(target_url, json={"jsonrpc": "2.0", "method": "notifications/initialized"})
    
    rpc_logs.append({"title": "Initialization", "received": init_res.json()})

    # 2. parqet_get_user
    u_res = session.post(target_url, json={
        "jsonrpc": "2.0", "id": "user-id", "method": "tools/call", "params": {"name": "parqet_get_user", "arguments": {}}
    })
    rpc_logs.append({"title": "Step 1: parqet_get_user", "received": u_res.json()})

    # 3. parqet_list_portfolios
    lp_res = session.post(target_url, json={
        "jsonrpc": "2.0", "id": "list-portfolios-id", "method": "tools/call", "params": {"name": "parqet_list_portfolios", "arguments": {}}
    })
    lp_data = lp_res.json()
    rpc_logs.append({"title": "Step 2: parqet_list_portfolios", "received": lp_data})

    # Prepare portfolios for dropdown
    portfolios = []
    try:
        content_text = lp_data['result']['content'][0]['text']
        items = json.loads(content_text).get('items', [])
        for p in items:
            portfolios.append({"id": p['id'], "name": p['name']})
    except:
        pass

    portfolio_options = "".join([f'<option value="{p["id"]}">{p["name"]}</option>' for p in portfolios])
    
    # Log output with improved JSON formatting
    log_html = "".join([
        f'<div class="log-entry success"><strong>{l["title"]}</strong>{format_json_html(l["received"])}</div>' 
        for l in rpc_logs
    ])

    return f"""
    {get_base_style()}
    <div class="container">
        <div class="card">
            <div class="header"><h1>Portfolio Selection</h1></div>
            <div class="log-container">{log_html}</div>
            
            <form method="POST">
                <label class="label">Select a portfolio for analysis:</label>
                <select name="portfolio_id">
                    {portfolio_options}
                </select>
                <button type="submit" formaction="/analyze" class="btn">Get Portfolio Details</button>
                <button type="submit" formaction="/activities" class="btn btn-alt">Get Activities</button>
                <button type="submit" formaction="/performance" class="btn btn-perf">Get Performance</button>
            </form>
        </div>
    </div>
    """

@app.route('/analyze', methods=['POST'])
def analyze():
    """Executes parqet_get_portfolio."""
    portfolio_id = request.form.get('portfolio_id')
    return execute_rpc_call("parqet_get_portfolio", {"portfolioId": portfolio_id}, portfolio_id)

@app.route('/activities', methods=['POST'])
def activities():
    """Executes parqet_get_activities."""
    portfolio_id = request.form.get('portfolio_id')
    return execute_rpc_call("parqet_get_activities", {"portfolioId": portfolio_id}, portfolio_id)

@app.route('/performance', methods=['POST'])
def performance():
    """Executes parqet_get_performance."""
    portfolio_id = request.form.get('portfolio_id')
    # Optimized arguments based on official documentation
    args = {
        "portfolioIds": [portfolio_id],
        "intervalType": "relative",
        "intervalValue": "max"
    }
    return execute_rpc_call("parqet_get_performance", args, portfolio_id)

def execute_rpc_call(method_name, arguments, portfolio_id):
    """Generic function to execute RPC tools."""
    token = flask_session.get('access_token')
    mcp_sid = flask_session.get('mcp_session_id')
    
    if not portfolio_id or not token:
        return redirect('/')

    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {token}", 
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "mcp-session-id": mcp_sid
    })
    target_url = f"{MCP_BASE_URL}/mcp"

    payload = {
        "jsonrpc": "2.0",
        "id": f"{method_name}-id",
        "method": "tools/call",
        "params": {
            "name": method_name,
            "arguments": arguments
        }
    }
    res = session.post(target_url, json=payload, timeout=15)
    
    return render_result(method_name, payload, res.json(), portfolio_id)

def render_result(title, sent, received, p_id):
    """Helper function to render the result page."""
    return f"""
    {get_base_style()}
    <div class="container">
        <div class="card">
            <div class="header"><h1>Result: {title}</h1></div>
            <div class="log-entry success">
                <strong>Analysis for Portfolio: {p_id}</strong>
                <span class="label">Request:</span>
                {format_json_html(sent)}
                <span class="label">Response:</span>
                {format_json_html(received)}
            </div>
            <br>
            <a href="/selection" class="btn" style="background: #64748b;">Back to List</a>
        </div>
    </div>
    """

if __name__ == '__main__':
    app.run(port=3000, debug=True)