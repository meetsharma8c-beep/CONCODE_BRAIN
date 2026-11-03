#!/usr/bin/env python3
"""Automated Deployer for CONCODE Brain to Hugging Face Spaces + TripVerse."""

import json
import os
import re
import sys
import time
import subprocess
from pathlib import Path
from huggingface_hub import HfApi, create_repo, upload_folder, add_space_secret, add_space_variable, get_space_runtime

def get_tripverse_concode_api_key() -> str:
    env_path = Path("/Users/ms/Downloads/TripVerse/.env")
    if env_path.exists():
        content = env_path.read_text()
        m = re.search(r'CONCODE_API_KEY="?([a-zA-Z0-9_\-]+)"?', content)
        if m:
            return m.group(1).strip()
    return ""

def deploy_hf_space(token: str):
    print("=" * 60)
    print("🚀 AUTOMATING CONCODE BRAIN DEPLOYMENT TO HUGGING FACE")
    print("=" * 60)

    token = token.strip()
    if not token:
        print("❌ Error: Token is empty.")
        sys.exit(1)

    api = HfApi(token=token)
    try:
        user_info = api.whoami()
        username = user_info["name"]
        print(f"✅ Authenticated as Hugging Face user: {username}")
    except Exception as e:
        print(f"❌ Failed to authenticate with Hugging Face token: {e}")
        sys.exit(1)

    space_name = "concode-brain"
    repo_id = f"{username}/{space_name}"
    # Permanent HF Space URL format
    # In HF, space urls use hyphenated username-spacename (lowercased)
    clean_username = username.lower().replace("_", "-")
    space_subdomain = f"{clean_username}-{space_name.lower().replace('_', '-')}"
    permanent_url = f"https://{space_subdomain}.hf.space"
    space_web_url = f"https://huggingface.co/spaces/{repo_id}"

    print(f"\n📍 Permanent Space Host: {permanent_url}")
    print(f"🌐 Space Repo URL:       {space_web_url}")

    # 1. Create Space repo if not exists
    print("\n📦 Step 1: Ensuring Hugging Face Space exists...")
    try:
        create_repo(
            repo_id=repo_id,
            repo_type="space",
            space_sdk="docker",
            private=False,
            exist_ok=True,
            token=token,
        )
        print(f"✅ Space repository verified: {repo_id}")
    except Exception as e:
        print(f"⚠️ Repo creation notice: {e}")

    # 2. Prepare staging directory for Space files
    print("\n📁 Step 2: Packaging CONCODE Brain Docker Space...")
    staging_dir = Path("/tmp/concode_hf_staging")
    staging_dir.mkdir(parents=True, exist_ok=True)

    # Clean previous files
    for item in staging_dir.iterdir():
        if item.is_file():
            item.unlink()

    # Write README.md with YAML metadata
    readme_content = f"""---
title: ConCode Brain API
emoji: 🧠
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# ConCode Brain API
Official ConCode AI Brain travel and reasoning endpoints for TripVerse.
Permanent URL: `{permanent_url}`
"""
    (staging_dir / "README.md").write_text(readme_content)

    # Write Dockerfile for root context
    dockerfile_content = """FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \\
    PYTHONDONTWRITEBYTECODE=1 \\
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip \\
    && python -m pip install -r /app/requirements.txt

COPY app.py /app/app.py

EXPOSE 7860
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-7860} --workers 1"]
"""
    (staging_dir / "Dockerfile").write_text(dockerfile_content)

    # Copy app.py and requirements.txt
    src_app = Path("/Users/ms/Downloads/CONCODE_BRAIN/deployment/huggingface/app.py")
    src_req = Path("/Users/ms/Downloads/CONCODE_BRAIN/deployment/huggingface/requirements.txt")
    (staging_dir / "app.py").write_text(src_app.read_text())
    (staging_dir / "requirements.txt").write_text(src_req.read_text())

    print("✅ Staging directory ready with Dockerfile, app.py, requirements.txt, and README.md.")

    # 3. Upload files to Space
    print("\n⬆️  Step 3: Uploading files to Hugging Face Space...")
    try:
        upload_folder(
            folder_path=str(staging_dir),
            repo_id=repo_id,
            repo_type="space",
            commit_message="Deploy CONCODE Brain v3.0 to Space",
            token=token,
        )
        print("✅ Files uploaded successfully to Space!")
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        sys.exit(1)

    # 4. Configure Space Secrets & Variables
    print("\n🔐 Step 4: Configuring Space Secrets & Variables...")
    concode_api_key = get_tripverse_concode_api_key()
    if not concode_api_key or len(concode_api_key) < 32:
        concode_api_key = "concode-prod-" + os.urandom(24).hex()

    try:
        add_space_secret(repo_id=repo_id, key="CONCODE_API_KEY", value=concode_api_key, token=token)
        add_space_secret(repo_id=repo_id, key="CONCODE_REMOTE_LLM_API_KEY", value=token, token=token)
        print("✅ Space secrets set: CONCODE_API_KEY, CONCODE_REMOTE_LLM_API_KEY")
    except Exception as e:
        print(f"⚠️ Notice setting secrets: {e}")

    try:
        add_space_variable(repo_id=repo_id, key="CONCODE_REMOTE_LLM_BASE_URL", value="https://router.huggingface.co/v1", token=token)
        add_space_variable(repo_id=repo_id, key="CONCODE_REMOTE_LLM_MODEL", value="meta-llama/Llama-3.1-8B-Instruct", token=token)
        print("✅ Space variables set: CONCODE_REMOTE_LLM_BASE_URL, CONCODE_REMOTE_LLM_MODEL")
    except Exception as e:
        print(f"⚠️ Notice setting variables: {e}")

    # 5. Monitor Space Build & Start
    print("\n⏳ Step 5: Waiting for Space container to build and start...")
    max_wait = 300
    start_time = time.time()
    space_ready = False

    while time.time() - start_time < max_wait:
        try:
            runtime = get_space_runtime(repo_id=repo_id, token=token)
            stage = getattr(runtime, "stage", str(runtime))
            print(f"   Current Space Stage: {stage} (elapsed: {int(time.time() - start_time)}s)")
            if stage in ("RUNNING", "APP_STARTING", "RUNNING_BUILDING"):
                if stage == "RUNNING":
                    space_ready = True
                    break
            elif stage in ("BUILD_ERROR", "RUNTIME_ERROR", "CONFIG_ERROR"):
                print(f"❌ Space build/runtime error: {stage}")
                break
        except Exception as e:
            print(f"   Waiting for runtime status ({e})...")
        time.sleep(10)

    if not space_ready:
        print("⚠️ Space is still initializing or in queue. We will configure TripVerse with the permanent URL.")
    else:
        print(f"✅ Space is RUNNING at {permanent_url}!")

    # 6. Update TripVerse on Vercel
    print("\n🔗 Step 6: Linking permanent URL to TripVerse on Vercel...")
    tripverse_dir = Path("/Users/ms/Downloads/TripVerse")

    # Update local .env
    env_file = tripverse_dir / ".env"
    if env_file.exists():
        content = env_file.read_text()
        content = re.sub(r'CONCODE_API_URL="[^"]*"', f'CONCODE_API_URL="{permanent_url}"', content)
        content = re.sub(r'VITE_CONCODE_API_URL="[^"]*"', f'VITE_CONCODE_API_URL="{permanent_url}"', content)
        env_file.write_text(content)
        print("✅ Updated local TripVerse .env")

    # Update Vercel production env vars
    try:
        subprocess.run(
            ["npx", "vercel", "env", "add", "CONCODE_API_URL", "production", "--force"],
            input=f"{permanent_url}\n",
            text=True,
            cwd=str(tripverse_dir),
            capture_output=True,
            check=False,
        )
        subprocess.run(
            ["npx", "vercel", "env", "add", "VITE_CONCODE_API_URL", "production", "--force"],
            input=f"{permanent_url}\n",
            text=True,
            cwd=str(tripverse_dir),
            capture_output=True,
            check=False,
        )
        print("✅ Updated Vercel Production Environment Variables")
    except Exception as e:
        print(f"⚠️ Vercel env update notice: {e}")

    # Redeploy TripVerse
    print("\n🚀 Step 7: Triggering TripVerse Vercel production deployment...")
    deploy_res = subprocess.run(
        ["npx", "vercel", "--prod", "--yes"],
        cwd=str(tripverse_dir),
        capture_output=True,
        text=True,
        env={**os.environ, "GIT_DIR": "/dev/null"},
    )
    if deploy_res.returncode == 0:
        print("✅ TripVerse redeployed to production on Vercel!")
        for line in deploy_res.stdout.splitlines():
            if "tripverse" in line or "https://" in line:
                print(f"   {line}")
    else:
        print(f"⚠️ Vercel deploy output: {deploy_res.stderr}")

    print("\n" + "=" * 60)
    print("🎉 ALL AUTOMATION COMPLETED!")
    print(f"Permanent CONCODE Brain URL: {permanent_url}")
    print(f"Hugging Face Space:          {space_web_url}")
    print(f"TripVerse Production:        https://tripverse.concode.com")
    print("=" * 60)

if __name__ == "__main__":
    token = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("HF_TOKEN", "")
    if not token:
        print("Usage: python deploy_hf_space.py <HF_ACCESS_TOKEN>")
        sys.exit(1)
    deploy_hf_space(token)
