import sys
sys.path.insert(0, '.')
from admin_panel.app import create_app
from admin_panel.extensions import db
from setup_test_data import setup_test_data, cleanup_test_data
import os
import requests
import multiprocessing
import time

def run_app():
    # Use test-specific database URL to avoid conflicts with main application
    # This ensures tests don't interfere with the main database
    os.environ['DATABASE_URL'] = 'sqlite:///bot_test.db'
    app = create_app('development')
    app.run(host='127.0.0.1', port=5001, debug=False)

if __name__ == '__main__':
    try:
        # Setup data in the main process
        setup_test_data()
        
        # Run Flask app in a separate process
        server_process = multiprocessing.Process(target=run_app)
        server_process.start()
        time.sleep(3) # Give the server time to start

        # Test 1: Listar todos los fragmentos (sin filtros)
        print("--- Running Test 1: Listar todos los fragmentos (sin filtros) ---")
        response = requests.get('http://127.0.0.1:5001/api/v1/narrative/fragments')
        data = response.json()
        assert response.status_code == 200
        assert data['success'] == True
        assert len(data['data']) == 4
        assert data['pagination']['total'] == 4
        print("✓ Test 1 passed.")

        # Test 2: Paginación
        print("--- Running Test 2: Paginación ---")
        response = requests.get('http://127.0.0.1:5001/api/v1/narrative/fragments?page=1&per_page=2')
        data = response.json()
        assert data['pagination']['page'] == 1
        assert data['pagination']['total'] == 4
        assert len(data['data']) == 2
        response = requests.get('http://127.0.0.1:5001/api/v1/narrative/fragments?page=2&per_page=2')
        data = response.json()
        assert data['pagination']['page'] == 2
        assert len(data['data']) == 2
        print("✓ Test 2 passed.")

    finally:
        # Terminate the server process
        server_process.terminate()
        server_process.join()
        
        # Cleanup data in the main process
        cleanup_test_data()
