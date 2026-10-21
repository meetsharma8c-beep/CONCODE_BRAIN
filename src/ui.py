"""
CONCODE Neural Brain — Monochromatic Black and White Web Interface
"""

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CONCODE Neural Brain — Cognitive Engine Dashboard</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-dark: #000000;
      --card-bg: #0a0a0a;
      --card-border: #262626;
      --primary: #ffffff;
      --text-main: #ffffff;
      --text-muted: #888888;
      --font-sans: 'Inter', -apple-system, sans-serif;
      --font-code: 'JetBrains Mono', monospace;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      background-color: var(--bg-dark);
      color: var(--text-main);
      font-family: var(--font-sans);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }

    header {
      border-bottom: 1px solid var(--card-border);
      background: #000000;
      position: sticky;
      top: 0;
      z-index: 100;
      padding: 1rem 2rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }

    .brand-title {
      font-size: 1.25rem;
      font-weight: 800;
      letter-spacing: -0.02em;
    }

    .status-badge {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      background: #171717;
      border: 1px solid #333333;
      color: #ffffff;
      padding: 0.35rem 0.85rem;
      border-radius: 9999px;
      font-size: 0.85rem;
      font-weight: 600;
    }

    .status-dot {
      width: 8px;
      height: 8px;
      background-color: #ffffff;
      border-radius: 50%;
    }

    .header-links {
      display: flex;
      align-items: center;
      gap: 1rem;
    }

    .nav-btn {
      color: var(--text-muted);
      text-decoration: none;
      font-size: 0.85rem;
      font-weight: 500;
      padding: 0.4rem 0.8rem;
      border-radius: 0.35rem;
      border: 1px solid var(--card-border);
      transition: all 0.2s ease;
    }

    .nav-btn:hover {
      color: #ffffff;
      border-color: #ffffff;
    }

    .nav-btn.primary {
      background: #ffffff;
      color: #000000;
      font-weight: 700;
    }

    .nav-btn.primary:hover {
      background: #cccccc;
    }

    main {
      flex: 1;
      max-width: 1400px;
      width: 100%;
      margin: 0 auto;
      padding: 2rem;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 2rem;
    }

    @media (max-width: 1024px) {
      main { grid-template-columns: 1fr; }
    }

    .card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 0.75rem;
      padding: 1.5rem;
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
    }

    .card-title {
      font-size: 1.05rem;
      font-weight: 700;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 1px solid var(--card-border);
      padding-bottom: 0.75rem;
    }

    .chip-container {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
    }

    .chip {
      background: #121212;
      border: 1px solid #2a2a2a;
      color: var(--text-muted);
      padding: 0.35rem 0.75rem;
      border-radius: 0.35rem;
      font-size: 0.8rem;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .chip:hover {
      border-color: #ffffff;
      color: #ffffff;
    }

    textarea {
      width: 100%;
      height: 140px;
      background: #000000;
      border: 1px solid var(--card-border);
      border-radius: 0.5rem;
      padding: 1rem;
      color: var(--text-main);
      font-family: var(--font-sans);
      font-size: 0.95rem;
      resize: vertical;
      outline: none;
    }

    textarea:focus {
      border-color: #ffffff;
    }

    .controls {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
    }

    .btn-submit {
      background: #ffffff;
      color: #000000;
      border: none;
      padding: 0.75rem 1.75rem;
      border-radius: 0.5rem;
      font-family: var(--font-sans);
      font-size: 0.9rem;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .btn-submit:hover {
      background: #cccccc;
    }

    .output-container {
      background: #000000;
      border: 1px solid var(--card-border);
      border-radius: 0.5rem;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      flex: 1;
      min-height: 280px;
    }

    .output-header {
      background: #121212;
      border-bottom: 1px solid var(--card-border);
      padding: 0.6rem 1rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-size: 0.8rem;
      color: var(--text-muted);
    }

    .output-meta {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }

    .guild-tag {
      background: #262626;
      color: #ffffff;
      padding: 0.2rem 0.5rem;
      border-radius: 0.25rem;
      font-weight: 600;
    }

    .btn-copy {
      background: transparent;
      border: 1px solid #333333;
      color: var(--text-muted);
      padding: 0.25rem 0.6rem;
      border-radius: 0.25rem;
      font-size: 0.75rem;
      cursor: pointer;
    }

    .btn-copy:hover {
      color: #ffffff;
      border-color: #ffffff;
    }

    pre {
      padding: 1rem;
      font-family: var(--font-code);
      font-size: 0.88rem;
      line-height: 1.6;
      color: #ffffff;
      overflow-x: auto;
      flex: 1;
      white-space: pre-wrap;
    }

    .guilds-section {
      grid-column: 1 / -1;
    }

    .guilds-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
      gap: 1rem;
    }

    .guild-card {
      background: #0d0d0d;
      border: 1px solid #222222;
      border-radius: 0.5rem;
      padding: 1rem;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .guild-card:hover {
      border-color: #ffffff;
    }

    .guild-info h4 {
      font-size: 0.9rem;
      font-weight: 700;
      margin-bottom: 0.25rem;
    }

    .guild-info p {
      font-size: 0.78rem;
      color: var(--text-muted);
    }

    .subsystems-bar {
      grid-column: 1 / -1;
      display: flex;
      flex-wrap: wrap;
      gap: 1.5rem;
      justify-content: space-around;
      background: #0a0a0a;
      border: 1px solid var(--card-border);
      border-radius: 0.75rem;
      padding: 1.25rem 2rem;
    }

    .subsystem-item {
      display: flex;
      align-items: center;
      gap: 0.6rem;
      font-size: 0.85rem;
      color: var(--text-muted);
    }

    .subsystem-status {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #ffffff;
    }
  </style>
</head>
<body>

  <header>
    <div class="brand">
      <div class="brand-title">CONCODE NEURAL BRAIN</div>
      <div class="status-badge" id="service-status">
        <span class="status-dot"></span> Status: Online (7B Parameters)
      </div>
    </div>
    <div class="header-links">
      <a href="/docs" target="_blank" class="nav-btn">Swagger API Docs</a>
      <a href="file:///Users/ms/Desktop/CONCODE_BRAIN/concode-neural-brain/CONCODE-Neural-Brain-Map.canvas" target="_blank" class="nav-btn primary">Open Obsidian Canvas</a>
    </div>
  </header>

  <main>
    <div class="card">
      <div class="card-title">
        <span>Cognitive Prompt Engine</span>
        <span style="font-size:0.8rem; font-weight:normal; color:var(--text-muted);">Select or type a prompt</span>
      </div>

      <div class="chip-container">
        <div class="chip" onclick="setPrompt('Fix null pointer crash in login form')">Fix Null Pointer</div>
        <div class="chip" onclick="setPrompt('Create 3D particle sphere using Three.js shader')">3D WebGL Shader</div>
        <div class="chip" onclick="setPrompt('Implement JWT auth middleware in FastAPI')">JWT Auth Middleware</div>
        <div class="chip" onclick="setPrompt('Optimize SQL query with index for user search')">Optimize Postgres Query</div>
        <div class="chip" onclick="setPrompt('Write Jest unit test suite for payment processor')">Jest Test Suite</div>
        <div class="chip" onclick="setPrompt('Create responsive Flutter login screen')">Flutter Login Screen</div>
        <div class="chip" onclick="setPrompt('Write ERC-20 smart contract in Solidity')">Solidity ERC-20</div>
      </div>

      <textarea id="user-prompt" placeholder="Ask the neural brain to generate code, fix bugs, optimize performance, or design architecture..."></textarea>

      <div class="controls">
        <div style="font-size:0.8rem; color:var(--text-muted);">
          Workspace Context: <strong style="color:#ffffff;">Active</strong>
        </div>
        <button class="btn-submit" id="btn-run" onclick="runPipeline()">Execute Brain</button>
      </div>
    </div>

    <div class="card">
      <div class="card-title">
        <span>Neural Output</span>
        <div id="latency-tag" style="font-size:0.8rem; color:var(--text-muted);">Ready</div>
      </div>

      <div class="output-container">
        <div class="output-header">
          <div class="output-meta">
            <span class="guild-tag" id="guild-badge">fullstack</span>
            <span id="confidence-score">Confidence: --%</span>
            <span id="repair-badge" style="display:none;">Repair Applied</span>
          </div>
          <button class="btn-copy" onclick="copyCode()">Copy Code</button>
        </div>
        <pre id="code-output">// Output generated by CodeLlama-7B will appear here...</pre>
      </div>
    </div>

    <div class="card guilds-section">
      <div class="card-title">
        <span>13 Expert Guilds (Mixture-of-Experts Routing)</span>
        <span style="font-size:0.85rem; color:var(--text-muted);">Select a guild persona</span>
      </div>
      <div class="guilds-grid" id="guilds-grid"></div>
    </div>

    <div class="subsystems-bar" id="subsystems-bar">
      <div class="subsystem-item"><div class="subsystem-status"></div> Subsystem 1: DistilBERT Intent Classifier</div>
      <div class="subsystem-item"><div class="subsystem-status"></div> Subsystem 2: MiniLM + FAISS Retriever</div>
      <div class="subsystem-item"><div class="subsystem-status"></div> Subsystem 3: CodeLlama-7B GGUF Generator</div>
      <div class="subsystem-item"><div class="subsystem-status"></div> Subsystem 4: CodeT5 Code Repairer</div>
      <div class="subsystem-item"><div class="subsystem-status"></div> Subsystem 5: Session Memory Store</div>
    </div>
  </main>

  <script>
    const GUILDS = [
      { name: "debugger", title: "Debugger Guild", desc: "Runtime errors, stack traces, null pointer checks", prompt: "Fix the null reference error in user profile service" },
      { name: "webgl", title: "WebGL Guild", desc: "Three.js, GLSL vertex & fragment shaders, 3D scenes", prompt: "Create a 3D animated particle galaxy in Three.js" },
      { name: "ai_ml", title: "AI / ML Guild", desc: "PyTorch models, transformers, RAG, quantization", prompt: "Build a PyTorch transformer classifier model" },
      { name: "qa", title: "QA Guild", desc: "Jest, Cypress, pytest, unit testing, TDD automation", prompt: "Write unit tests for user authentication using Jest" },
      { name: "security", title: "Security Guild", desc: "JWT, OAuth2, XSS/SQLi defense, OWASP hardening", prompt: "Implement rate limiting and JWT auth middleware" },
      { name: "performance", title: "Performance Guild", desc: "Latency reduction, memoization, web workers", prompt: "Optimize React component render performance" },
      { name: "database", title: "Database Guild", desc: "SQL DDL, indexes, ORM migrations, query plans", prompt: "Design normalized PostgreSQL database schema" },
      { name: "ui_ux", title: "UI / UX Guild", desc: "Responsive CSS Grid, layout components, animations", prompt: "Build a responsive dashboard layout" },
      { name: "devops", title: "DevOps Guild", desc: "Docker, Kubernetes, GitHub Actions, Nginx IaC", prompt: "Write multi-stage Dockerfile for FastAPI app" },
      { name: "api", title: "API Guild", desc: "RESTful endpoints, GraphQL, WebSockets, OpenAPI", prompt: "Design REST API endpoint with Pydantic validation" },
      { name: "fullstack", title: "Fullstack Guild", desc: "Generalist architecture, monorepos, integration", prompt: "Scaffold full-stack project architecture" },
      { name: "mobile", title: "Mobile Guild", desc: "iOS Swift, Android Kotlin, Flutter cross-platform", prompt: "Build a responsive Flutter login screen" },
      { name: "blockchain", title: "Blockchain Guild", desc: "Solidity smart contracts, Solana Rust programs", prompt: "Write secure ERC-20 smart contract in Solidity" }
    ];

    function renderGuilds() {
      const grid = document.getElementById('guilds-grid');
      grid.innerHTML = GUILDS.map(g => `
        <div class="guild-card" onclick="setPrompt('${g.prompt}')">
          <div class="guild-info">
            <h4>${g.title}</h4>
            <p>${g.desc}</p>
          </div>
        </div>
      `).join('');
    }

    function setPrompt(text) {
      document.getElementById('user-prompt').value = text;
    }

    async function runPipeline() {
      const promptText = document.getElementById('user-prompt').value.trim();
      if (!promptText) return;

      const btn = document.getElementById('btn-run');
      const codeOutput = document.getElementById('code-output');
      const guildBadge = document.getElementById('guild-badge');
      const confidenceScore = document.getElementById('confidence-score');
      const repairBadge = document.getElementById('repair-badge');
      const latencyTag = document.getElementById('latency-tag');

      btn.disabled = true;
      btn.textContent = 'Processing...';
      codeOutput.textContent = '// Running neural cognitive pipeline across subsystems...';
      latencyTag.textContent = 'Executing...';

      try {
        const res = await fetch('/api/v1/cognitive', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: promptText })
        });

        const data = await res.json();
        
        codeOutput.textContent = data.code;
        guildBadge.textContent = data.guild;
        confidenceScore.textContent = `Confidence: ${(data.confidence * 100).toFixed(0)}%`;
        repairBadge.style.display = data.repair_applied ? 'inline-flex' : 'none';
        latencyTag.textContent = `Latency: ${data.latency_ms} ms`;
      } catch (err) {
        codeOutput.textContent = `// Error calling Neural Brain API: ${err.message}`;
      } finally {
        btn.disabled = false;
        btn.textContent = 'Execute Brain';
      }
    }

    function copyCode() {
      const text = document.getElementById('code-output').textContent;
      navigator.clipboard.writeText(text).then(() => {
        alert('Code copied to clipboard!');
      });
    }

    renderGuilds();
  </script>
</body>
</html>
"""
