"""Wrapper file to start dash server in Azure/production, all setup is done in dashapp module"""
from dashapp.app import dash_app
app = dash_app.server

if __name__ == "__main__":

    dash_app.run_server() #turning debug on seems to break things