"""
CONCODE Neural Brain — Training Data Generator

Generates 3 datasets locally on Mac (no paid APIs):
  1. intent_dataset.jsonl — 500+ examples per guild (13 guilds)
  2. repair_dataset.jsonl — 10,000 broken/fixed code pairs
  3. multi_guild_train.jsonl — 500+ instruction/output pairs per guild

Run: python -m src.generate_data
"""

import yaml
import random
import json
import os
import re
from pathlib import Path

random.seed(42)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
GUILDS_FILE = DATA_DIR / "guilds.yaml"


def load_guilds():
    with open(GUILDS_FILE) as f:
        guilds = yaml.safe_load(f)["guilds"]
    return {g["name"]: g for g in guilds}


# ================================================================
# 1. INTENT CLASSIFIER DATASET (500+ per guild)
# ================================================================

def generate_intent_dataset():
    print("=" * 60)
    print("Generating intent classification dataset...")
    guilds_dict = load_guilds()

    templates = {
        "debugger": [
            "Fix this error: {error}",
            "Why does {variable} crash?",
            "Debug {context} {error}",
            "Resolve {error} in {context}",
            "Help me debug this broken {context} code",
            "Uncaught {error} when calling {variable}",
            "My {context} throws {error} on line 42",
            "Getting {error} after deploying to production",
            "Stack trace shows {error} in {variable}",
            "How to fix {error} in my {context}?",
            "Null pointer exception in {variable}",
            "Cannot read property of {variable}",
            "My app crashes with {error}",
            "Debug why {variable} returns undefined",
            "Fix the broken {context} logic",
        ],
        "webgl": [
            "Create a 3D {object} in three.js",
            "Add a {shader} shader to my scene",
            "Render a dynamic {object} with custom lighting",
            "Optimize Three.js particle system for {object}",
            "Implement GLSL {shader} for 3D canvas",
            "Animate a 3D {object} using WebGL",
            "Build a {object} with PBR materials",
            "Create {shader} post-processing pipeline",
            "Render instanced {object} geometries",
            "Set up orbit camera controls for {object} scene",
            "Write a custom {shader} shader in GLSL",
            "Build interactive 3D {object} viewer",
            "Create WebGL ray marching {shader}",
            "Implement shadow mapping for {object} scene",
            "Generate procedural {object} mesh",
        ],
        "ai_ml": [
            "Build a PyTorch model for {task}",
            "Fine-tune LLM on custom dataset for {task}",
            "Implement sentence-transformers embedding search for {task}",
            "Create RAG pipeline for {task}",
            "Train intent classifier model for {task}",
            "Quantize model weights to GGUF format for {task}",
            "Build transformer architecture for {task}",
            "Implement attention mechanism for {task}",
            "Create training loop for {task} model",
            "Deploy ML model serving for {task}",
            "Implement LoRA fine-tuning for {task}",
            "Build vector database for {task}",
            "Create evaluation metrics for {task}",
            "Design neural network for {task}",
            "Implement data augmentation for {task}",
        ],
        "qa": [
            "Write unit tests for {component}",
            "Create integration test for {feature}",
            "Set up {framework} testing framework",
            "Add test coverage for {component}",
            "Write e2e tests for {feature} flow",
            "Mock {dependency} in unit tests",
            "Create snapshot tests for {component}",
            "Test edge cases for {feature}",
            "Set up CI test pipeline for {framework}",
            "Write BDD specs for {feature}",
            "Test error handling in {component}",
            "Create load testing script for {feature}",
            "Write property-based tests for {component}",
            "Add regression tests for {feature}",
            "Implement TDD for new {component}",
        ],
        "security": [
            "Add JWT to {endpoint}",
            "Secure the API against {vulnerability}",
            "Implement OAuth2 authentication for {endpoint}",
            "Sanitize user inputs to prevent {vulnerability}",
            "Configure CORS and CSP headers for {endpoint}",
            "Encrypt sensitive {data_type} using AES-256",
            "Set up rate limiting for {endpoint}",
            "Implement RBAC for {endpoint}",
            "Add CSRF protection to {endpoint}",
            "Hash {data_type} with bcrypt",
            "Create secure session management for {endpoint}",
            "Implement two-factor authentication for {endpoint}",
            "Audit {endpoint} for {vulnerability}",
            "Configure TLS certificates for {endpoint}",
            "Validate JWT tokens at {endpoint}",
        ],
        "performance": [
            "Optimize performance of {component}",
            "Reduce latency in {component} rendering",
            "Fix high memory usage caused by {cause}",
            "Speed up {component} by implementing {strategy}",
            "Benchmark and profile {component} under load",
            "Eliminate memory leak in {cause}",
            "Implement {strategy} for {component}",
            "Reduce bundle size of {component}",
            "Optimize database queries in {component}",
            "Add virtual scrolling to {component}",
            "Implement code splitting for {component}",
            "Profile {component} with Chrome DevTools",
            "Reduce re-renders in {component}",
            "Optimize images and assets in {component}",
            "Add CDN caching for {component}",
        ],
        "database": [
            "Design a database schema for {domain}",
            "Write an efficient SQL query to fetch {entity}",
            "Add indexes to improve performance of {table}",
            "Set up a migration script for {table}",
            "Configure PostgreSQL connection pool for {domain}",
            "Normalize tables for {domain} backend",
            "Create stored procedure for {entity}",
            "Design many-to-many relationship for {domain}",
            "Optimize slow query on {table}",
            "Set up database replication for {domain}",
            "Create aggregation pipeline for {entity}",
            "Implement database transactions for {domain}",
            "Design time-series schema for {domain}",
            "Add full-text search to {table}",
            "Create backup strategy for {domain} database",
        ],
        "ui_ux": [
            "Create a responsive {ui_element} component",
            "Design a dark mode theme with glassmorphism for {ui_element}",
            "Improve accessible keyboard navigation for {ui_element}",
            "Add smooth CSS animations to {ui_element}",
            "Build a modern dashboard layout with a floating {ui_element}",
            "Style an interactive {ui_element} using CSS",
            "Create mobile-first {ui_element} layout",
            "Implement skeleton loading for {ui_element}",
            "Design micro-interactions for {ui_element}",
            "Build drag-and-drop interface for {ui_element}",
            "Create animated page transitions for {ui_element}",
            "Implement infinite scroll for {ui_element}",
            "Design color palette and typography for {ui_element}",
            "Build accordion/collapsible {ui_element}",
            "Create custom scrollbar for {ui_element}",
        ],
        "devops": [
            "Write a Dockerfile for a {tech_stack} application",
            "Configure GitHub Actions pipeline for {deploy_target}",
            "Set up Kubernetes deployment manifests for {deploy_target}",
            "Automate CI/CD testing and build steps for {tech_stack}",
            "Create NGINX reverse proxy config for {deploy_target}",
            "Set up Terraform infrastructure for {deploy_target}",
            "Configure Docker Compose for {tech_stack} stack",
            "Create Helm chart for {deploy_target}",
            "Set up monitoring with Prometheus for {deploy_target}",
            "Configure auto-scaling for {deploy_target}",
            "Create rolling deployment strategy for {tech_stack}",
            "Set up log aggregation for {deploy_target}",
            "Configure SSL/TLS certificates for {deploy_target}",
            "Create disaster recovery plan for {deploy_target}",
            "Set up blue-green deployment for {tech_stack}",
        ],
        "api": [
            "Design RESTful API routes for {feature}",
            "Create a GraphQL schema for {feature}",
            "Implement OpenAPI / Swagger documentation for {feature}",
            "Build a webhooks handler for {feature}",
            "Write FastAPI endpoints to process {feature}",
            "Add rate limiting and pagination to {feature} routes",
            "Create middleware for {feature} API",
            "Implement API versioning for {feature}",
            "Build WebSocket endpoint for {feature}",
            "Design error handling for {feature} API",
            "Create API gateway for {feature}",
            "Implement HATEOAS for {feature} resources",
            "Build batch processing endpoint for {feature}",
            "Create API health check for {feature}",
            "Design idempotent endpoints for {feature}",
        ],
        "fullstack": [
            "Design a full-stack system architecture for {app_type}",
            "Integrate frontend {frontend_tech} with backend {backend_tech}",
            "Build complete end-to-end authentication flow for {app_type}",
            "Architect real-time WebSockets synchronization for {app_type}",
            "Structure multi-tenant cloud architecture for {app_type}",
            "Setup full-stack monorepo for {app_type}",
            "Create project scaffold for {app_type}",
            "Design microservices for {app_type}",
            "Build SSR application with {frontend_tech} and {backend_tech}",
            "Create full-stack CRUD for {app_type}",
            "Design event-driven architecture for {app_type}",
            "Build real-time dashboard for {app_type}",
            "Create notification system for {app_type}",
            "Design file upload pipeline for {app_type}",
            "Build search functionality for {app_type}",
        ],
    }

    fillers = {
        "debugger": {
            "error": ["TypeError", "ReferenceError", "NullPointerException",
                      "cannot read property 'undefined'", "IndexError",
                      "SyntaxError", "UnhandledPromiseRejection", "RangeError",
                      "NetworkError", "TimeoutError"],
            "variable": ["user", "data", "config", "token", "response",
                         "state", "payload", "session", "context", "handler"],
            "context": ["loop", "API call", "event listener", "async function",
                        "database connection", "React component", "middleware",
                        "WebSocket handler", "form validation"],
        },
        "webgl": {
            "object": ["cube", "sphere", "terrain", "character model", "galaxy",
                       "mesh", "camera view", "particle system", "skybox",
                       "planet", "voxel world"],
            "shader": ["fragment", "vertex", "post-processing", "bloom",
                       "water ripple", "toon outline", "pbr", "displacement",
                       "cel shading", "volumetric fog"],
        },
        "ai_ml": {
            "task": ["text classification", "code generation", "semantic search",
                     "sentiment analysis", "named entity recognition",
                     "image captioning", "question answering", "summarization",
                     "translation", "anomaly detection"],
        },
        "qa": {
            "component": ["user registration", "payment processor", "auth module",
                          "search engine", "notification service", "file uploader",
                          "data pipeline", "API gateway", "cache layer"],
            "feature": ["login flow", "checkout process", "user profile",
                        "dashboard", "settings page", "file upload",
                        "search results", "notifications", "data export"],
            "framework": ["Jest", "Mocha", "Cypress", "Playwright", "pytest",
                          "Vitest", "Testing Library"],
            "dependency": ["database", "API client", "auth service",
                           "file system", "email sender", "cache"],
        },
        "security": {
            "endpoint": ["/api/login", "/user/profile", "/checkout",
                         "/auth/callback", "admin panel", "/api/users",
                         "/webhook", "/upload", "/settings"],
            "vulnerability": ["XSS attacks", "SQL injection", "CSRF exploits",
                              "rate limiting bypass", "session hijacking",
                              "path traversal", "SSRF", "broken auth"],
            "data_type": ["passwords", "credit cards", "API keys",
                          "session tokens", "personal info", "medical records",
                          "financial data"],
        },
        "performance": {
            "component": ["search algorithm", "React re-render", "SQL query",
                          "large list view", "image processing pipeline",
                          "WebSocket handler", "file parser", "API response"],
            "cause": ["unbounded event listeners", "unindexed queries",
                      "heavy DOM manipulation", "large array mappings",
                      "synchronous I/O", "memory allocation", "N+1 queries"],
            "strategy": ["memoization", "debouncing", "caching", "lazy loading",
                         "web workers", "virtual scrolling", "code splitting",
                         "connection pooling"],
        },
        "database": {
            "domain": ["e-commerce app", "social network", "analytics platform",
                       "SaaS subscription", "inventory manager", "healthcare system",
                       "content management", "logistics tracker"],
            "entity": ["active users", "monthly revenue", "nested comments",
                       "audit logs", "order history", "product catalog",
                       "user sessions", "notification queue"],
            "table": ["users table", "orders table", "products table",
                      "transactions", "session store", "audit_log",
                      "permissions", "inventory"],
        },
        "ui_ux": {
            "ui_element": ["modal dialog", "navigation sidebar", "data card grid",
                           "dropdown menu", "toast notification", "hero banner",
                           "tab interface", "carousel", "data table",
                           "search bar", "progress indicator"],
        },
        "devops": {
            "tech_stack": ["FastAPI & React", "Node.js microservice",
                           "Python backend", "Next.js app", "Go API service",
                           "Django & Vue", "Spring Boot"],
            "deploy_target": ["AWS ECS", "Google Cloud Run", "DigitalOcean Droplet",
                              "Vercel", "Kubernetes cluster", "Azure AKS",
                              "Heroku", "Fly.io"],
        },
        "api": {
            "feature": ["user registration", "payment processing", "file uploading",
                        "notifications", "search & filtering", "analytics events",
                        "content management", "real-time messaging"],
        },
        "fullstack": {
            "app_type": ["SaaS analytics platform", "real-time chat app",
                         "e-commerce portal", "project management tool",
                         "AI code assistant", "social media platform",
                         "learning management system", "IoT dashboard"],
            "frontend_tech": ["React", "Vue", "Next.js", "Svelte", "Vanilla JS",
                              "Angular", "Solid.js"],
            "backend_tech": ["FastAPI", "Node.js", "Django", "Go Fiber",
                             "NestJS", "Express", "Spring Boot"],
        },
    }

    dataset = []
    for name in guilds_dict.keys():
        if name not in templates or name not in fillers:
            continue
        for _ in range(500):
            tmpl = random.choice(templates[name])
            try:
                fill_dict = {}
                for k, v in fillers[name].items():
                    if f"{{{k}}}" in tmpl:
                        fill_dict[k] = random.choice(v)
                text = tmpl.format(**fill_dict)
            except (KeyError, IndexError):
                continue
            dataset.append({"text": text, "label": name})

    DATA_DIR.mkdir(exist_ok=True)
    output_file = DATA_DIR / "intent_dataset.jsonl"
    with open(output_file, "w") as f:
        for d in dataset:
            f.write(json.dumps(d) + "\n")

    print(f"  Generated {len(dataset)} intent examples -> {output_file}")


# ================================================================
# 2. CODE REPAIR DATASET (10,000 pairs)
# ================================================================

def corrupt_code(code: str) -> str:
    """Apply 1-3 random corruptions to clean code."""
    corruptions = [
        lambda c: c.replace('{', '', 1) if '{' in c else c,
        lambda c: c.replace('}', '', 1) if '}' in c else c,
        lambda c: c.replace(')', '', 1) if ')' in c else c,
        lambda c: c.replace('(', '', 1) if '(' in c else c,
        lambda c: c.replace('function', 'functoin', 1) if 'function' in c else c,
        lambda c: c.replace('function', 'funciton', 1) if 'function' in c else c,
        lambda c: c.replace('return', 'retun', 1) if 'return' in c else c,
        lambda c: c.replace('return', 'retrun', 1) if 'return' in c else c,
        lambda c: c.replace('const', 'cosnt', 1) if 'const' in c else c,
        lambda c: c.replace('const', 'conts', 1) if 'const' in c else c,
        lambda c: c.replace('let ', 'lat ', 1) if 'let ' in c else c,
        lambda c: c.replace('===', '==', 1) if '===' in c else c,
        lambda c: c.replace('!==', '!=', 1) if '!==' in c else c,
        lambda c: c.replace('=>', '=', 1) if '=>' in c else c,
        lambda c: c.replace(';', '', 1) if ';' in c else c,
        lambda c: c.replace('async ', 'asyc ', 1) if 'async ' in c else c,
        lambda c: c.replace('await ', 'awiat ', 1) if 'await ' in c else c,
        lambda c: c.replace('import', 'ipmort', 1) if 'import' in c else c,
        lambda c: c.replace('export', 'exoprt', 1) if 'export' in c else c,
        lambda c: c.replace('console', 'consol', 1) if 'console' in c else c,
        lambda c: c.replace('document', 'docuemnt', 1) if 'document' in c else c,
        lambda c: c.replace('.length', '.lenght', 1) if '.length' in c else c,
        lambda c: c.replace('null', 'nul', 1) if 'null' in c else c,
        lambda c: c.replace('true', 'tru', 1) if 'true' in c else c,
        lambda c: c.replace('false', 'flase', 1) if 'false' in c else c,
    ]

    corrupted = code
    num_corruptions = random.randint(1, 3)
    for _ in range(num_corruptions):
        func = random.choice(corruptions)
        corrupted = func(corrupted)

    # If nothing changed, delete a random character
    if corrupted == code and len(code) > 5:
        idx = random.randint(0, len(code) - 1)
        corrupted = code[:idx] + code[idx + 1:]

    return corrupted


def generate_synthetic_clean_codes(count=5000):
    """Generate diverse clean JavaScript code snippets."""
    fn_names = [
        "calculateTotal", "fetchUserData", "renderComponent", "parsePayload",
        "validateAuth", "formatCurrency", "handleFilter", "processQueue",
        "syncState", "initializeApp", "handleSubmit", "transformData",
        "parseResponse", "validateInput", "generateToken", "buildQuery",
        "serializeData", "handleError", "processEvent", "computeHash",
    ]
    params = [
        "data", "config", "req, res", "id, options", "items", "event",
        "ctx", "payload, headers", "user, token", "query, params",
    ]
    body_templates = [
        "const result = items.map(x => x * 2);\n  return result.filter(Boolean);",
        "if (!data) {\n    throw new Error('Invalid data payload');\n  }\n  return data.id;",
        "try {\n    const res = await fetch('/api/v1/data');\n    return await res.json();\n  } catch (err) {\n    console.error(err);\n  }",
        "let total = 0;\n  for (let i = 0; i < items.length; i++) {\n    total += items[i].price;\n  }\n  return total;",
        "const { user, token } = req.body;\n  if (!token) return res.status(401).send('Unauthorized');\n  return res.json({ user });",
        "const filtered = data.filter(item => item.active === true);\n  return filtered.sort((a, b) => b.score - a.score);",
        "const cache = new Map();\n  if (cache.has(id)) return cache.get(id);\n  const result = await fetchFromDB(id);\n  cache.set(id, result);\n  return result;",
        "const element = document.querySelector('#app');\n  element.innerHTML = '';\n  items.forEach(item => {\n    const div = document.createElement('div');\n    div.textContent = item.name;\n    element.appendChild(div);\n  });",
        "return new Promise((resolve, reject) => {\n    setTimeout(() => {\n      if (data) resolve(data);\n      else reject(new Error('No data'));\n    }, 1000);\n  });",
        "const headers = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };\n  const response = await fetch(url, { method: 'POST', headers, body: JSON.stringify(payload) });\n  return response.json();",
        "export default class EventEmitter {\n    constructor() { this.events = {}; }\n    on(event, fn) { (this.events[event] = this.events[event] || []).push(fn); }\n    emit(event, ...args) { (this.events[event] || []).forEach(fn => fn(...args)); }\n  }",
        "const debounce = (fn, delay) => {\n    let timer;\n    return (...args) => {\n      clearTimeout(timer);\n      timer = setTimeout(() => fn(...args), delay);\n    };\n  };\n  return debounce(callback, 300);",
    ]

    clean_codes = []
    for _ in range(count):
        fn = random.choice(fn_names)
        p = random.choice(params)
        b = random.choice(body_templates)
        is_async = "await" in b or "fetch" in b or "Promise" in b
        prefix = "async " if is_async else ""
        code = f"{prefix}function {fn}({p}) {{\n  {b}\n}}"
        clean_codes.append(code)
    return clean_codes


def generate_repair_dataset(target_count=10000):
    print("Generating code repair dataset (10,000 pairs)...")
    clean_codes = generate_synthetic_clean_codes(target_count)

    DATA_DIR.mkdir(exist_ok=True)
    repair_file = DATA_DIR / "repair_dataset.jsonl"
    with open(repair_file, "w") as f:
        for clean in clean_codes:
            broken = corrupt_code(clean)
            f.write(json.dumps({"broken": broken, "fixed": clean}) + "\n")

    print(f"  Generated {len(clean_codes)} broken/fixed pairs -> {repair_file}")


# ================================================================
# 3. MULTI-GUILD TRAINING DATASET (500+ per guild)
# ================================================================

def generate_scaled_multi_guild_train(target_per_guild=500):
    print(f"Generating multi-guild training data ({target_per_guild}+ per guild)...")
    guilds_dict = load_guilds()

    guild_code_generators = {
        "debugger": [
            ("Fix null pointer error in function {fn}", "function {fn}(data) {{\n  if (!data) return null;\n  return data.property;\n}}"),
            ("Resolve uncaught exception in {fn}", "async function {fn}() {{\n  try {{\n    await executeTask();\n  }} catch (err) {{\n    console.error('Handled error:', err);\n  }}\n}}"),
            ("Fix scope reference error for variable {var_name}", "let {var_name} = 0;\nfunction increment() {{\n  {var_name} += 1;\n  return {var_name};\n}}"),
            ("Debug race condition in {fn}", "async function {fn}() {{\n  const lock = new Mutex();\n  await lock.acquire();\n  try {{\n    await processData();\n  }} finally {{\n    lock.release();\n  }}\n}}"),
            ("Fix memory leak in event listener {fn}", "function {fn}(element) {{\n  const handler = (e) => console.log(e);\n  element.addEventListener('click', handler);\n  return () => element.removeEventListener('click', handler);\n}}"),
        ],
        "webgl": [
            ("Create a 3D {shape} render scene in Three.js", "const scene = new THREE.Scene();\nconst camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);\nconst renderer = new THREE.WebGLRenderer();\nrenderer.setSize(window.innerWidth, window.innerHeight);\nconst geometry = new THREE.{shape_geom}();\nconst material = new THREE.MeshStandardMaterial({{ color: 0x{color_hex} }});\nconst mesh = new THREE.Mesh(geometry, material);\nscene.add(mesh);\nrenderer.render(scene, camera);"),
            ("Implement GLSL fragment shader for {effect} effect", "precision mediump float;\nuniform float u_time;\nvarying vec2 v_uv;\nvoid main() {{\n  vec3 color = vec3(v_uv.x, v_uv.y, sin(u_time));\n  gl_FragColor = vec4(color, 1.0);\n}}"),
            ("Create particle system with {shape} emitters", "const particles = new THREE.BufferGeometry();\nconst positions = new Float32Array(1000 * 3);\nfor (let i = 0; i < 1000; i++) {{\n  positions[i * 3] = Math.random() * 10 - 5;\n  positions[i * 3 + 1] = Math.random() * 10;\n  positions[i * 3 + 2] = Math.random() * 10 - 5;\n}}\nparticles.setAttribute('position', new THREE.BufferAttribute(positions, 3));"),
        ],
        "ai_ml": [
            ("Build PyTorch linear classifier for {task_name}", "import torch\nimport torch.nn as nn\nclass {task_name}Model(nn.Module):\n  def __init__(self, in_features, out_classes):\n    super().__init__()\n    self.fc = nn.Linear(in_features, out_classes)\n  def forward(self, x):\n    return self.fc(x)"),
            ("Generate text embeddings using SentenceTransformers", "from sentence_transformers import SentenceTransformer\nmodel = SentenceTransformer('all-MiniLM-L6-v2')\nembeddings = model.encode(['sample text query'])"),
            ("Create training loop for {task_name}", "optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5)\nfor epoch in range(10):\n  for batch in dataloader:\n    optimizer.zero_grad()\n    outputs = model(**batch)\n    loss = outputs.loss\n    loss.backward()\n    optimizer.step()\n    print(f'Epoch {{epoch}}, Loss: {{loss.item():.4f}}')"),
        ],
        "qa": [
            ("Write Jest unit test for {fn}", "describe('{fn}', () => {{\n  it('should return correct result', () => {{\n    const result = {fn}(mockData);\n    expect(result).toBeDefined();\n    expect(result.status).toBe('success');\n  }});\n\n  it('should handle null input', () => {{\n    expect(() => {fn}(null)).toThrow();\n  }});\n}});"),
            ("Create Cypress e2e test for login flow", "describe('Login Flow', () => {{\n  it('should login successfully', () => {{\n    cy.visit('/login');\n    cy.get('#email').type('test@example.com');\n    cy.get('#password').type('password123');\n    cy.get('#submit').click();\n    cy.url().should('include', '/dashboard');\n  }});\n}});"),
            ("Write pytest test for {fn}", "import pytest\n\ndef test_{fn}_success():\n    result = {fn}(valid_input)\n    assert result is not None\n    assert result['status'] == 'ok'\n\ndef test_{fn}_invalid_input():\n    with pytest.raises(ValueError):\n        {fn}(None)"),
        ],
        "security": [
            ("Implement JWT validation for route {route}", "const jwt = require('jsonwebtoken');\nfunction verifyAuth(req, res, next) {{\n  const token = req.headers.authorization?.split(' ')[1];\n  if (!token) return res.status(401).json({{ error: 'Unauthorized' }});\n  jwt.verify(token, process.env.SECRET_KEY, (err, decoded) => {{\n    if (err) return res.status(403).json({{ error: 'Forbidden' }});\n    req.user = decoded;\n    next();\n  }});\n}}"),
            ("Sanitize input string against XSS injection", "function sanitizeInput(inputStr) {{\n  return String(inputStr).replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\"/g, '&quot;').replace(/'/g, '&#x27;');\n}}"),
            ("Implement bcrypt password hashing", "const bcrypt = require('bcrypt');\nasync function hashPassword(password) {{\n  const salt = await bcrypt.genSalt(12);\n  return bcrypt.hash(password, salt);\n}}\nasync function verifyPassword(password, hash) {{\n  return bcrypt.compare(password, hash);\n}}"),
        ],
        "performance": [
            ("Implement debouncing utility function {fn}", "function {fn}(fn, delay) {{\n  let timer;\n  return function(...args) {{\n    clearTimeout(timer);\n    timer = setTimeout(() => fn.apply(this, args), delay);\n  }};\n}}"),
            ("Optimize list rendering with memoization", "import React, {{ memo }} from 'react';\nconst MemoizedItem = memo(({{ title, value }}) => (\n  <div className='item'>{{title}}: {{value}}</div>\n));\nexport default MemoizedItem;"),
            ("Implement LRU cache for {fn}", "class LRUCache {{\n  constructor(capacity) {{\n    this.capacity = capacity;\n    this.cache = new Map();\n  }}\n  get(key) {{\n    if (!this.cache.has(key)) return -1;\n    const val = this.cache.get(key);\n    this.cache.delete(key);\n    this.cache.set(key, val);\n    return val;\n  }}\n  put(key, value) {{\n    this.cache.delete(key);\n    this.cache.set(key, value);\n    if (this.cache.size > this.capacity) {{\n      this.cache.delete(this.cache.keys().next().value);\n    }}\n  }}\n}}"),
        ],
        "database": [
            ("Write PostgreSQL table schema for {entity_name}", "CREATE TABLE {entity_name} (\n  id SERIAL PRIMARY KEY,\n  name VARCHAR(100) NOT NULL,\n  status VARCHAR(50) DEFAULT 'active',\n  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n);\nCREATE INDEX idx_{entity_name}_status ON {entity_name}(status);"),
            ("Create parameterized SQL query for {entity_name}", "SELECT * FROM {entity_name} WHERE status = $1 AND created_at >= $2 ORDER BY id DESC;"),
            ("Design migration script for {entity_name}", "-- Migration: Add columns to {entity_name}\nALTER TABLE {entity_name} ADD COLUMN updated_at TIMESTAMP;\nALTER TABLE {entity_name} ADD COLUMN metadata JSONB DEFAULT '{{}}';\nCREATE INDEX idx_{entity_name}_updated ON {entity_name}(updated_at);"),
        ],
        "ui_ux": [
            ("Create responsive CSS grid layout for {element_name}", ".{element_name}-grid {{\n  display: grid;\n  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));\n  gap: 1.5rem;\n  padding: 1rem;\n}}"),
            ("Design modern glassmorphism container", ".glass-container {{\n  background: rgba(255, 255, 255, 0.08);\n  backdrop-filter: blur(16px);\n  border-radius: 1rem;\n  border: 1px solid rgba(255, 255, 255, 0.15);\n}}"),
            ("Create animated loading skeleton for {element_name}", ".{element_name}-skeleton {{\n  background: linear-gradient(90deg, #1a1a2e 25%, #16213e 50%, #1a1a2e 75%);\n  background-size: 200% 100%;\n  animation: shimmer 1.5s infinite;\n  border-radius: 0.5rem;\n  height: 1rem;\n}}\n@keyframes shimmer {{\n  0% {{ background-position: 200% 0; }}\n  100% {{ background-position: -200% 0; }}\n}}"),
        ],
        "devops": [
            ("Write multi-stage Dockerfile for {app_name}", "FROM node:18-alpine AS build\nWORKDIR /app\nCOPY package*.json ./\nRUN npm ci\nCOPY . .\nRUN npm run build\nFROM nginx:alpine\nCOPY --from=build /app/dist /usr/share/nginx/html\nEXPOSE 80\nCMD [\"nginx\", \"-g\", \"daemon off;\"]"),
            ("Configure Nginx reverse proxy for {app_name}", "server {{\n  listen 80;\n  server_name localhost;\n  location / {{\n    proxy_pass http://127.0.0.1:8000;\n    proxy_set_header Host $host;\n    proxy_set_header X-Real-IP $remote_addr;\n  }}\n}}"),
            ("Create GitHub Actions CI pipeline for {app_name}", "name: CI\non: [push, pull_request]\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-node@v4\n        with:\n          node-version: 18\n      - run: npm ci\n      - run: npm test\n      - run: npm run build"),
        ],
        "api": [
            ("Create RESTful FastAPI POST route for {endpoint_name}", "from fastapi import FastAPI\nfrom pydantic import BaseModel\napp = FastAPI()\nclass {endpoint_name}Payload(BaseModel):\n  name: str\n  value: int\n@app.post('/api/v1/{endpoint_name}')\nasync def handle_{endpoint_name}(payload: {endpoint_name}Payload):\n  return {{'status': 'success', 'data': payload}}"),
            ("Write OpenAPI schema response model for {endpoint_name}", "from pydantic import BaseModel\nclass {endpoint_name}Response(BaseModel):\n  id: str\n  success: bool\n  message: str = ''"),
            ("Create Express.js middleware for {endpoint_name}", "const rateLimit = require('express-rate-limit');\nconst limiter = rateLimit({{\n  windowMs: 15 * 60 * 1000,\n  max: 100,\n  message: 'Too many requests'\n}});\napp.use('/api/{endpoint_name}', limiter);"),
        ],
        "fullstack": [
            ("Architect full-stack monorepo layout for {system_name}", "// System Architecture Blueprint: {system_name}\n// Frontend: React + Vite + Tailwind CSS\n// Backend: FastAPI + PostgreSQL\n// State: Redux Toolkit / Zustand\n// Infra: Docker + Nginx"),
            ("Create fetch API client wrapper for {system_name}", "async function apiCall(url, method = 'GET', data = null) {{\n  const options = {{ method, headers: {{ 'Content-Type': 'application/json' }} }};\n  if (data) options.body = JSON.stringify(data);\n  const res = await fetch(url, options);\n  if (!res.ok) throw new Error(`API Error: ${{res.status}}`);\n  return await res.json();\n}}"),
            ("Create WebSocket real-time handler for {system_name}", "const ws = new WebSocket('ws://localhost:8080');\nws.onopen = () => console.log('Connected');\nws.onmessage = (event) => {{\n  const data = JSON.parse(event.data);\n  handleUpdate(data);\n}};\nws.onerror = (err) => console.error('WS Error:', err);\nws.onclose = () => setTimeout(connect, 3000);"),
        ],
    }

    fillers = {
        "fn": ["parseUser", "handleData", "calculateTotal", "validateRequest",
               "renderView", "formatPayload", "processEvent", "syncData",
               "buildIndex", "resolveQuery"],
        "var_name": ["token", "counter", "retryLimit", "authHeader",
                     "sessionData", "requestId", "cacheKey"],
        "shape": ["Cube", "Sphere", "Torus", "Cylinder", "Cone", "Octahedron"],
        "shape_geom": ["BoxGeometry", "SphereGeometry", "TorusGeometry",
                       "CylinderGeometry", "ConeGeometry"],
        "color_hex": ["00ff00", "ff0055", "3388ff", "ffaa00", "9933ff",
                      "00ccff", "ff6600"],
        "effect": ["ripple", "color pulse", "wave distortion", "neon glow",
                   "chromatic aberration", "vignette"],
        "route": ["/login", "/dashboard", "/checkout", "/user/settings",
                  "/admin", "/api/data", "/webhook"],
        "entity_name": ["users", "orders", "products", "invoices",
                        "audit_logs", "sessions", "events"],
        "element_name": ["card", "navbar", "sidebar", "dashboard", "modal",
                         "tooltip", "drawer"],
        "app_name": ["concode_brain", "web_app", "api_gateway", "auth_service",
                     "data_pipeline"],
        "endpoint_name": ["UserRegistration", "OrderPlacement", "AnalyticsEvent",
                          "FileUpload", "Notification"],
        "task_name": ["IntentClassification", "SentimentAnalysis",
                      "TextEmbedding", "CodeGeneration"],
        "system_name": ["ConcodeNeuralBrain", "ECommercePlatform",
                        "AIAnalytics", "ChatPlatform"],
    }

    multi_guild_entries = []

    for guild_name, guild_info in guilds_dict.items():
        sys_prompt = guild_info.get("system_prompt", "You are a helpful AI assistant.")
        # Truncate system prompt for training data
        sys_prompt = sys_prompt.strip()[:300]
        generators = guild_code_generators.get(guild_name, [])

        for _ in range(target_per_guild):
            if not generators:
                continue
            instr_tmpl, code_tmpl = random.choice(generators)

            try:
                fill_dict = {}
                for k, v in fillers.items():
                    if f"{{{k}}}" in instr_tmpl or f"{{{k}}}" in code_tmpl:
                        fill_dict[k] = random.choice(v)
                instr = instr_tmpl.format(**fill_dict)
                code_output = code_tmpl.format(**fill_dict)
            except (KeyError, IndexError):
                continue

            multi_guild_entries.append({
                "system": sys_prompt,
                "instruction": instr,
                "output": code_output,
            })

    output_file = DATA_DIR / "multi_guild_train.jsonl"
    with open(output_file, "w") as f:
        for entry in multi_guild_entries:
            f.write(json.dumps(entry) + "\n")

    # Count per guild
    guild_counts = {}
    for entry in multi_guild_entries:
        sys = entry["system"][:30]
        guild_counts[sys] = guild_counts.get(sys, 0) + 1

    print(f"  Generated {len(multi_guild_entries)} multi-guild training examples -> {output_file}")


# ================================================================
# MAIN
# ================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  CONCODE Neural Brain — Data Generator")
    print("=" * 60)
    generate_intent_dataset()
    generate_repair_dataset(10000)
    generate_scaled_multi_guild_train(500)
    print("=" * 60)
    print("  All datasets generated successfully!")
    print("=" * 60)
