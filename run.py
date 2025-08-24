#!/usr/bin/env python3
"""
ClotSync - Blood Donation & Hospital Inventory Management System
Run script for the Flask application
"""

import os
import sys
from app import app

if __name__ == '__main__':
    # Set default configuration
    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
    
    # Run the application
    print("🚀 Starting ClotSync Blood Donation System...")
    print("📍 Application will be available at: http://localhost:5000")
    print("🩸 Connecting lives through blood donation")
    print("-" * 50)
    
    try:
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=True
        )
    except KeyboardInterrupt:
        print("\n👋 ClotSync stopped. Thank you for using our system!")
    except Exception as e:
        print(f"❌ Error starting ClotSync: {e}")
        sys.exit(1)


