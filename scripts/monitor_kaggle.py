import os
import re
import sys
import time

os.environ['KAGGLE_CONFIG_DIR'] = os.path.expanduser('~/.kaggle')
import kaggle

kaggle.api.authenticate()
kernel_ref = 'meetpeeyushsharma/notebookd440319320'

url_pattern = re.compile(r'https://[a-z0-9-]+\.(?:ngrok-free\.dev|ngrok-free\.app|trycloudflare\.com)')
seen_lines = set()
public_url = None

print(f"Monitoring Kaggle kernel execution for {kernel_ref}...", flush=True)

for retry in range(40):
    try:
        stream = kaggle.api.kernels_logs_stream(kernel_ref)
        for chunk in stream:
            data = chunk.get('data', '')
            t = chunk.get('time', 0)
            if data.strip():
                line = f"[{t:.1f}s] {data.strip()}"
                if line not in seen_lines:
                    seen_lines.add(line)
                    print(line, flush=True)
                match = url_pattern.search(data)
                if match:
                    public_url = match.group(0)
                    print(f"\n🎯 FOUND LIVE GPU ENDPOINT: {public_url}", flush=True)
                    if "verified" in data.lower() or "serving" in data.lower():
                        sys.exit(0)
    except Exception as e:
        time.sleep(3)

print("Monitoring loop finished.", flush=True)
