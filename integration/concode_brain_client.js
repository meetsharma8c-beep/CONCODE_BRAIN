/**
 * CONCODE Neural Brain — Website Integration Client
 * 
 * Drop this script into your Antigravity-built website to connect
 * to the local CONCODE Neural Brain API running on your MacBook.
 * 
 * Usage:
 *   1. Start the brain server: cd CONCODE_BRAIN && ./start.sh
 *   2. Include this script in your HTML: <script src="concode_brain_client.js"></script>
 *   3. Call: ConcodeBrain.query("Fix this bug in my login form")
 */

const ConcodeBrain = (() => {
  // ── Configuration ──────────────────────────────────────────
  const API_BASE = 'http://localhost:8000';
  const COGNITIVE_ENDPOINT = `${API_BASE}/api/v1/cognitive`;
  const AGENT_ENDPOINT = `${API_BASE}/api/v1/agent`;
  const GUILDS_ENDPOINT = `${API_BASE}/api/v1/guilds`;
  const STATUS_ENDPOINT = `${API_BASE}/api/v1/status`;

  let sessionId = crypto.randomUUID ? crypto.randomUUID() : 
    'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
      const r = Math.random() * 16 | 0;
      return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
    });

  // ── Guild Icons ────────────────────────────────────────────
  const GUILD_ICONS = {
    debugger: '[DEBUG]', webgl: '[WEBGL]', ai_ml: '[AI_ML]', qa: '[QA]',
    security: '[SEC]', performance: '[PERF]', database: '[DB]',
    ui_ux: '[UIUX]', devops: '[DEVOPS]', api: '[API]', fullstack: '[FULLSTACK]'
  };

  // ── Collect Open Editor Files ──────────────────────────────
  function collectWorkspaceFiles() {
    const files = {};

    // Try to collect from Antigravity editor API
    if (window.antigravity && window.antigravity.getOpenFiles) {
      try {
        const openFiles = window.antigravity.getOpenFiles();
        openFiles.forEach(file => {
          files[file.name] = file.content;
        });
        return files;
      } catch (e) {
        console.warn('[ConcodeBrain] Could not access Antigravity editor API:', e);
      }
    }

    // Fallback: try to collect from CodeMirror / Monaco / Ace editors
    // CodeMirror
    const cmElements = document.querySelectorAll('.CodeMirror');
    cmElements.forEach((el, i) => {
      if (el.CodeMirror) {
        files[`editor_${i}.js`] = el.CodeMirror.getValue();
      }
    });

    // Monaco Editor
    if (window.monaco && window.monaco.editor) {
      const models = window.monaco.editor.getModels();
      models.forEach((model, i) => {
        const uri = model.uri.toString();
        const name = uri.split('/').pop() || `monaco_${i}.js`;
        files[name] = model.getValue();
      });
    }

    // Ace Editor
    const aceElements = document.querySelectorAll('.ace_editor');
    aceElements.forEach((el, i) => {
      if (el.env && el.env.editor) {
        files[`ace_${i}.js`] = el.env.editor.getValue();
      }
    });

    return files;
  }

  // ── Main Query Function ────────────────────────────────────
  async function query(userPrompt, options = {}) {
    const {
      includeWorkspace = true,
      mode = 'text',
      onGuildDetected = null,
      onCodeGenerated = null,
    } = options;

    const workspaceFiles = includeWorkspace ? collectWorkspaceFiles() : {};

    const payload = {
      query: userPrompt,
      workspace_files: workspaceFiles,
      session_id: sessionId,
      mode: mode,
    };

    try {
      const response = await fetch(COGNITIVE_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`Brain API error: ${response.status} ${response.statusText}`);
      }

      const result = await response.json();

      // Callbacks
      if (onGuildDetected) {
        onGuildDetected(result.guild, result.guild_icon, result.confidence);
      }
      if (onCodeGenerated) {
        onCodeGenerated(result.code, result.repair_applied);
      }

      return result;
    } catch (error) {
      console.error('[ConcodeBrain] Query failed:', error);
      throw error;
    }
  }

  // ── Insert Code into Editor ────────────────────────────────
  function insertCode(code) {
    // Antigravity editor
    if (window.antigravity && window.antigravity.insertText) {
      window.antigravity.insertText(code);
      return true;
    }

    // Monaco Editor
    if (window.monaco && window.monaco.editor) {
      const editor = window.monaco.editor.getEditors()[0];
      if (editor) {
        const selection = editor.getSelection();
        editor.executeEdits('concode-brain', [{
          range: selection,
          text: code,
          forceMoveMarkers: true,
        }]);
        return true;
      }
    }

    // CodeMirror
    const cm = document.querySelector('.CodeMirror');
    if (cm && cm.CodeMirror) {
      const doc = cm.CodeMirror.getDoc();
      const cursor = doc.getCursor();
      doc.replaceRange(code, cursor);
      return true;
    }

    // Ace Editor
    const ace = document.querySelector('.ace_editor');
    if (ace && ace.env && ace.env.editor) {
      ace.env.editor.insert(code);
      return true;
    }

    // Fallback: copy to clipboard
    navigator.clipboard.writeText(code).then(() => {
      console.log('[ConcodeBrain] Code copied to clipboard (no editor detected)');
    });
    return false;
  }

  // ── Full Pipeline: Query + Insert ──────────────────────────
  async function queryAndInsert(userPrompt, options = {}) {
    const result = await query(userPrompt, options);
    if (result && result.code) {
      insertCode(result.code);
    }
    return result;
  }

  // ── Bounded Coding Agent ───────────────────────────────────
  // The agent returns whole-file replacements. It does not modify the
  // host project unless the integrating application explicitly applies them.
  async function agent(goal, options = {}) {
    const {
      workspaceFiles = collectWorkspaceFiles(),
      maxIterations = 3,
      onPlan = null,
      onEdits = null,
    } = options;

    const response = await fetch(AGENT_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        goal,
        workspace_files: workspaceFiles,
        session_id: sessionId,
        max_iterations: maxIterations,
      }),
    });

    if (!response.ok) {
      throw new Error(`Brain agent API error: ${response.status} ${response.statusText}`);
    }

    const result = await response.json();
    if (onPlan) {
      onPlan(result.plan, result);
    }
    if (result.success && result.edits.length && onEdits) {
      await onEdits(result.edits, result);
    }
    return result;
  }

  // ── Status & Health ────────────────────────────────────────
  async function getStatus() {
    const response = await fetch(STATUS_ENDPOINT);
    return response.json();
  }

  async function getGuilds() {
    const response = await fetch(GUILDS_ENDPOINT);
    return response.json();
  }

  async function isOnline() {
    try {
      const response = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(2000) });
      const data = await response.json();
      return data.status === 'healthy';
    } catch {
      return false;
    }
  }

  // ── Session Management ─────────────────────────────────────
  function resetSession() {
    sessionId = crypto.randomUUID ? crypto.randomUUID() :
      Date.now().toString(36) + Math.random().toString(36).slice(2);
  }

  // ── Public API ─────────────────────────────────────────────
  return {
    query,
    agent,
    insertCode,
    queryAndInsert,
    getStatus,
    getGuilds,
    isOnline,
    resetSession,
    collectWorkspaceFiles,
    GUILD_ICONS,
    get sessionId() { return sessionId; },
  };
})();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ConcodeBrain;
}
