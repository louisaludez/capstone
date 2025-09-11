#!/usr/bin/env python
"""
Install SARIMA dependencies for the hotel management system
Run this script to install required packages for time series forecasting
"""

import subprocess
import sys
import os

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✓ Successfully installed {package}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install {package}: {e}")
        return False

def main():
    print("Installing SARIMA dependencies for Hotel Management System...")
    print("=" * 60)
    
    packages = [
        "pandas==2.0.3",
        "numpy==1.24.3", 
        "statsmodels==0.14.0",
        "scikit-learn==1.3.0"
    ]
    
    success_count = 0
    total_packages = len(packages)
    
    for package in packages:
        print(f"Installing {package}...")
        if install_package(package):
            success_count += 1
    
    print("=" * 60)
    print(f"Installation complete: {success_count}/{total_packages} packages installed successfully")
    
    if success_count == total_packages:
        print("✓ All SARIMA dependencies are ready!")
        print("\nYou can now:")
        print("1. Run 'python manage.py test_sarima' to test the forecasting")
        print("2. Visit the admin dashboard to see the SARIMA chart")
    else:
        print("⚠ Some packages failed to install. Please check the errors above.")
        print("You may need to install them manually or check your Python environment.")

if __name__ == "__main__":
    main()
