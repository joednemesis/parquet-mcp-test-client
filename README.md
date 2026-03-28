# **Parqet Connect MCP \- Python Test Client**

This repository contains a lightweight Python-based test client for the **Parqet Connect MCP API**. It demonstrates how to implement a secure **OAuth2 flow with PKCE (S256)** and interact with the Parqet MCP JSON-RPC endpoint.

## 📸 Screenshots
*(Note: These screenshots were generated using the provided mockup tool to protect private financial data.)*

| Start Page | Portfolio Selection |
| :--- | :--- |
| ![Startseite](screenshots/startpage.png) | ![Portfolio Auswahl](screenshots/PortfolioSelection.png) |

| Portfolio Details | Activities | Performance |
| :--- | :--- | :--- |
| ![Details](screenshots/Result_parqet_get_portfolio.png) | ![Aktivitäten](screenshots/Result_parqet_get_activities.png) | ![Performance](screenshots/Result_parqet_get_performance.png) |

## **🚀 Key Features**

* **Secure Authentication**: Full implementation of OAuth2 with PKCE (Proof Key for Code Exchange).  
* **JSON-RPC Integration**: Direct communication with the /mcp endpoint using JSON-RPC 2.0.  
* **Portfolio Discovery**: Automatically lists all available portfolios after a successful login.  
* **Analysis Tools**:  
  * **Portfolio Details**: Basic information and currency settings.  
  * **Performance Data**: Fetches KPIs like XIRR, TTWROR, and absolute gain.  
  * **Activities**: Displays recent transactions (Buy, Sell, Dividends, etc.).  
* **Privacy First**: Includes a dedicated app\_mockup.py for demonstration purposes and safe screenshot generation.

## **🛠 Project Structure**

* app.py: The main application template (Insert your Client ID here).  
* app\_mockup.py: A standalone version with fake data for safe presentations and screenshots.  
* requirements.txt: Required dependencies (Flask & Requests).  
* .gitignore: Configured to keep local credentials, the PKCE verifier, and private testing scripts out of the repository.

## **📦 Installation & Setup**

1. **Prerequisites**: Python 3.x installed.  
2. **Clone & Install**:  
   pip install \-r requirements.txt

3. **Configuration**:  
   * Register your integration at the Parqet Console.  
   * Set the Redirect URI to http://localhost:3000/callback.  
   * Add your CLIENT\_ID to app.py.

## **🚦 Usage**

### **Run the Client**

python app.py

### **Run the Mockup (Safe for Demo)**

To see the UI and explore the features without connecting to a real account:  
python app\_mockup.py

## **🔒 Security Notes**

* The **PKCE Verifier** is generated and stored locally in verifier.txt during the login process.  
* This file is strictly excluded via .gitignore to prevent session data or security tokens from being uploaded to GitHub.  
* For production use, ensure your Client ID and secrets are handled securely (e.g., via environment variables).

## **📖 Background & API Reference**

This project is based on the official Parqet documentation. To use the API, follow these steps in the [Parqet Developer Portal](https://developer.parqet.com):

1. **Organization & Integration**: Create an organization and an integration in the Parqet Console.  
2. **Client ID**: Copy your unique Client ID and paste it into the app.py file.  
3. **Redirect URI**: Ensure http://localhost:3000/callback is added as an authorized redirect URL in your integration settings.  
4. **Specifications & Documentation**:  
   * [OpenAPI Specification (JSON)](https://developer.parqet.com/api-spec/current.json)  
   * [Developer Hub Overview (llms.txt)](https://developer.parqet.com/llms.txt)  
   * [Available Tools & Schema](https://developer.parqet.com/docs/give-ai-portfolio-context-with-the-parqet-mcp#available-tools)

*Disclaimer: This is an independent open-source project and not an official product of Parqet GmbH.*
