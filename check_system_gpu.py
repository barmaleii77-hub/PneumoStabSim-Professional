# -*- coding: utf-8 -*-
"""
Check system GPU and DirectX capabilities
"""
import sys
import subprocess

def check_gpu_info():
    """Check GPU using PowerShell"""
    print("\n" + "="*70)
    print("SYSTEM GPU CHECK")
    print("="*70 + "\n")
    
    try:
        # Get GPU info via PowerShell
        cmd = [
            'powershell', 
            '-Command',
            'Get-WmiObject Win32_VideoController | Select-Object Name, DriverVersion, Status | Format-List'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            output = result.stdout
            print("GPU Information:")
            print(output)
            
            # Check if it's software renderer
            if "Basic Render Driver" in output or "Microsoft Basic" in output:
                print("\n??  WARNING: Using SOFTWARE RENDERER (no GPU acceleration)")
                print("   Qt Quick 3D will NOT work properly")
                print("\n   Possible reasons:")
                print("   1. Remote Desktop (RDP) connection")
                print("   2. Virtual Machine without GPU passthrough")
                print("   3. GPU disabled or no drivers installed")
                print("\n   Solution:")
                print("   - Use local machine access (not RDP)")
                print("   - Enable GPU passthrough in VM")
                print("   - Install GPU drivers")
                print("   - OR: Use 2D Canvas instead of 3D")
            else:
                print("\n? Hardware GPU detected - 3D should work")
        else:
            print(f"ERROR: {result.stderr}")
    
    except Exception as e:
        print(f"ERROR checking GPU: {e}")
    
    print("\n" + "="*70 + "\n")


def check_rdp():
    """Check if running in Remote Desktop"""
    print("RDP CHECK:")
    print("-"*70)
    
    try:
        import os
        session = os.environ.get('SESSIONNAME', 'Unknown')
        print(f"Session Name: {session}")
        
        if 'RDP' in session.upper() or 'Console' not in session:
            print("\n??  WARNING: Running in Remote Desktop")
            print("   Remote Desktop forces software rendering")
            print("   Qt Quick 3D will NOT work")
            print("\n   Solution:")
            print("   - Access machine locally (not via RDP)")
            print("   - OR: Use 2D Canvas instead of 3D")
        else:
            print("\n? Running locally (not RDP)")
    
    except Exception as e:
        print(f"ERROR: {e}")
    
    print("\n" + "="*70 + "\n")


def check_directx():
    """Try to get DirectX info"""
    print("DIRECTX CHECK:")
    print("-"*70)
    
    try:
        # Run dxdiag and save to temp file
        import tempfile
        import time
        
        temp_file = tempfile.mktemp(suffix='.txt')
        
        print(f"Running dxdiag (this may take 10-15 seconds)...")
        cmd = ['dxdiag', '/t', temp_file]
        
        result = subprocess.run(cmd, timeout=30)
        
        # Wait for file to be written
        time.sleep(2)
        
        if result.returncode == 0:
            try:
                with open(temp_file, 'r', encoding='utf-16-le') as f:
                    content = f.read()
                
                # Look for key information
                if 'DirectX Version:' in content:
                    for line in content.split('\n'):
                        if 'DirectX Version:' in line:
                            print(f"  {line.strip()}")
                
                # Look for display adapter
                print("\nDisplay Adapters:")
                in_display = False
                for line in content.split('\n'):
                    if 'Display Devices' in line or 'Card name:' in line:
                        in_display = True
                    if in_display and ('Card name:' in line or 'Driver Version:' in line):
                        print(f"  {line.strip()}")
                    if in_display and '---' in line:
                        break
                
            except Exception as e:
                print(f"ERROR reading dxdiag output: {e}")
        
        # Cleanup
        try:
            import os
            os.remove(temp_file)
        except:
            pass
    
    except subprocess.TimeoutExpired:
        print("ERROR: dxdiag timed out")
    except Exception as e:
        print(f"ERROR: {e}")
    
    print("\n" + "="*70 + "\n")


def main():
    print("\n" + "="*70)
    print("Qt Quick 3D SYSTEM DIAGNOSTIC")
    print("="*70)
    print("\nThis will check why Qt Quick 3D might not be working")
    print("="*70)
    
    check_gpu_info()
    check_rdp()
    check_directx()
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print("\nIf you see 'Microsoft Basic Render Driver':")
    print("  ? Qt Quick 3D will NOT work")
    print("  ? Use 2D Canvas for pneumatic scheme")
    print("\nIf you see hardware GPU:")
    print("  ? Qt Quick 3D should work")
    print("  ? If still not working, check Qt Quick 3D installation")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
