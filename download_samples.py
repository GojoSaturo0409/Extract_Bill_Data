#!/usr/bin/env python3
"""
Automatic downloader for training samples
Usage: python3 download_samples.py
"""

import urllib.request
import zipfile
import os
import sys

def download_samples():
    """Download and extract training samples"""
    
    url = "https://hackrx.blob.core.windows.net/files/TRAINING_SAMPLES.zip"
    zip_file = "TRAINING_SAMPLES.zip"
    extract_dir = "TRAINING_SAMPLES"
    
    print("="*60)
    print("📥 Downloading Training Samples")
    print("="*60)
    
    # Check if already extracted
    if os.path.isdir(extract_dir):
        files = os.listdir(extract_dir)
        if files:
            print(f"\n✅ TRAINING_SAMPLES already exists with {len(files)} files")
            print(f"\nSamples found:")
            for f in sorted(files)[:5]:
                print(f"   • {f}")
            if len(files) > 5:
                print(f"   ... and {len(files)-5} more")
            print(f"\n✅ Ready to test! Run:")
            print(f"   python3 quick_test.py TRAINING_SAMPLES/sample_1.png")
            return True
    
    # Download
    try:
        print(f"\n📥 Downloading from:")
        print(f"   {url}")
        print(f"\nThis may take a minute...")
        
        urllib.request.urlretrieve(url, zip_file)
        
        print(f"✅ Downloaded: {zip_file}")
        
        # Extract
        print(f"\n📦 Extracting...")
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall()
        
        print(f"✅ Extracted to: {extract_dir}/")
        
        # List files
        files = os.listdir(extract_dir)
        print(f"\n📋 Found {len(files)} sample files:")
        for f in sorted(files):
            size = os.path.getsize(os.path.join(extract_dir, f)) / 1024
            print(f"   • {f} ({size:.1f} KB)")
        
        # Cleanup zip
        os.remove(zip_file)
        print(f"\n✅ Cleaned up: {zip_file}")
        
        print(f"\n{'='*60}")
        print(f"✅ READY TO TEST!")
        print(f"{'='*60}")
        print(f"\n1. Make sure API is running: python app.py")
        print(f"2. Test extraction:")
        print(f"   python3 quick_test.py TRAINING_SAMPLES/sample_1.png")
        print(f"\n" + "="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print(f"\nManual download:")
        print(f"1. Visit: {url}")
        print(f"2. Save the file")
        print(f"3. Extract it in your project folder")
        print(f"4. Run: python3 quick_test.py TRAINING_SAMPLES/sample_1.png")
        return False

if __name__ == '__main__':
    success = download_samples()
    sys.exit(0 if success else 1)
