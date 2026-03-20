<template>
  <div class="app">
    <nav>
      <div class="logo">
        <span class="logo-icon">📊</span>
        <span>Excel Insight Analyzer</span>
      </div>
      <div class="nav-badges">
        <span class="badge badge-ai">AI Powered</span>
        <span class="badge badge-green" v-if="result">✓ Análisis listo</span>
      </div>
    </nav>

    <main>
      <!-- HERO -->
      <div class="hero" v-if="!result && !loading">
        <p class="hero-eyebrow">Powered by Gemini AI</p>
        <h1>Transforma tu Excel<br>en insights inteligentes</h1>
        <p class="hero-sub">Sube cualquier archivo Excel y obtén métricas automáticas, perfilado de datos y un resumen ejecutivo generado por IA.</p>
      </div>

      <!-- UPLOAD -->
      <div v-if="!result && !loading">
        <div
          class="upload-zone"
          :class="{ 'drag-over': isDragging }"
          @click="triggerInput"
          @dragover.prevent="isDragging = true"
          @dragleave="isDragging = false"
          @drop.prevent="onDrop"
        >
          <div class="upload-icon">⬆</div>
          <h3>Arrastra tu archivo Excel aquí</h3>
          <p>o haz clic para seleccionar — .xlsx, .xls</p>
          <input type="file" ref="fileInput" @change="onFileChange" accept=".xlsx,.xls" />
          <div class="file-selected" v-if="selectedFile">
            ✓ {{ selectedFile.name }}
            <span class="file-size">({{ formatSize(selectedFile.size) }})</span>
          </div>
        </div>
        <div class="btn-wrapper">
          <button class="btn btn-primary" :disabled="!selectedFile" @click="analyze">
            🔍 Analizar con IA
          </button>
        </div>
      </div>

      <!-- LOADER -->
      <div class="loader-wrapper" v-if="loading">
        <div class="loader"></div>
        <p class="loader-title">Procesando tu archivo...</p>
        <p class="loader-sub">Esto puede tomar unos segundos</p>
        <div class="loader-steps">
          <div class="loader-step" :class="stepClass(0)"><span class="step-dot"></span> Leyendo archivo Excel</div>
          <div class="loader-step" :class="stepClass(1)"><span class="step-dot"></span> Perfilando dataset</div>
          <div class="loader-step" :class="stepClass(2)"><span class="step-dot"></span> Calculando métricas</div>
          <div class="loader-step" :class="stepClass(3)"><span class="step-dot"></span> Generando insights con Gemini</div>
        </div>
      </div>

      <!-- ERROR -->
      <div class="error-card" v-if="error && !loading">
        <h3>⚠ Error al analizar el archivo</h3>
        <p>{{ error }}</p>
        <button class="btn btn-ghost" @click="reset" style="margin-top:1rem;">Intentar de nuevo</button>
      </div>

      <!-- RESULTS -->
      <div class="results" v-if="result && !loading">

        <!-- KPIs -->
        <p class="section-label">Resumen del archivo</p>
        <div class="kpi-grid">
          <div class="kpi-card kpi-purple">
            <div class="kpi-label">Total de filas</div>
            <div class="kpi-value">{{ result.rows?.toLocaleString() ?? '—' }}</div>
            <div class="kpi-sub">registros</div>
          </div>
          <div class="kpi-card kpi-green">
            <div class="kpi-label">Columnas</div>
            <div class="kpi-value">{{ result.columns ?? '—' }}</div>
            <div class="kpi-sub">detectadas</div>
          </div>
          <div class="kpi-card kpi-amber">
            <div class="kpi-label">Numéricas</div>
            <div class="kpi-value">{{ result.numeric_columns?.length ?? 0 }}</div>
            <div class="kpi-sub">con métricas</div>
          </div>
          <div class="kpi-card kpi-teal">
            <div class="kpi-label">Texto</div>
            <div class="kpi-value">{{ result.descriptive_text_columns?.length ?? 0 }}</div>
            <div class="kpi-sub">descriptivas</div>
          </div>
        </div>

        <!-- PERFIL -->
        <p class="section-label">Perfil del dataset</p>
        <div class="two-col">
          <div class="card">
            <div class="card-title">Columnas detectadas</div>
            <div v-if="result.numeric_columns?.length" style="margin-bottom:12px">
              <div class="sub-label">Numéricas</div>
              <div class="tag-list">
                <span class="tag tag-num" v-for="c in result.numeric_columns" :key="c">{{ c }}</span>
              </div>
            </div>
            <div v-if="result.descriptive_text_columns?.length" style="margin-bottom:12px">
              <div class="sub-label">Texto descriptivo</div>
              <div class="tag-list">
                <span class="tag tag-txt" v-for="c in result.descriptive_text_columns" :key="c">{{ c }}</span>
              </div>
            </div>
            <div v-if="result.categorical_columns?.length" style="margin-bottom:12px">
              <div class="sub-label">Categóricas</div>
              <div class="tag-list">
                <span class="tag tag-cat" v-for="c in result.categorical_columns" :key="c">{{ c }}</span>
              </div>
            </div>
            <div v-if="result.date_columns?.length">
              <div class="sub-label">Fechas</div>
              <div class="tag-list">
                <span class="tag tag-date" v-for="c in result.date_columns" :key="c">{{ c }}</span>
              </div>
            </div>
          </div>

          <div class="card">
            <div class="card-title">Métricas numéricas</div>
            <div v-if="result.metrics?.numeric_summary">
              <div v-for="(stats, col) in result.metrics.numeric_summary" :key="col" style="margin-bottom:16px">
                <div class="sub-label">{{ col }}</div>
                <table class="metrics-table">
                  <tr><td>Promedio</td><td>{{ fmt(stats.mean) }}</td></tr>
                  <tr><td>Mínimo</td><td>{{ fmt(stats.min) }}</td></tr>
                  <tr><td>Máximo</td><td>{{ fmt(stats.max) }}</td></tr>
                  <tr><td>Registros</td><td>{{ stats.count }}</td></tr>
                </table>
              </div>
            </div>
            <p v-else class="empty-state">Sin columnas numéricas.</p>
          </div>
        </div>

        <!-- DISTRIBUCIÓN CATEGÓRICA -->
        <div class="chart-wrapper" v-if="hasCategorical">
          <p class="section-label" style="margin-top:0">Distribución categórica</p>
          <div class="chart-scroll">
            <div v-for="(dist, col) in result.metrics?.categorical_summary" :key="col" class="cat-block">
              <div class="sub-label" style="margin-bottom:10px">{{ col }}</div>
              <div v-for="(count, val) in dist" :key="val" class="bar-row">
                <span class="bar-label">{{ val }}</span>
                <div class="bar-track">
                  <div class="bar-fill" :style="{ width: barWidth(count, dist) + '%' }"></div>
                </div>
                <span class="bar-count">{{ count }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- AI ANALYSIS -->
        <p class="section-label">Análisis con Inteligencia Artificial</p>
        <div class="ai-card">
          <div class="ai-badge">● Gemini AI · Análisis ejecutivo</div>

          <!-- Si ai_summary es texto plano/markdown -->
          <div v-if="result.ai_summary" class="ai-text" v-html="renderMarkdown(result.ai_summary)"></div>

          <!-- Si viene del fallback estructurado -->
          <div v-else-if="result.fallback_summary">
            <div class="sub-label">Resumen ejecutivo</div>
            <p class="executive-summary">{{ result.fallback_summary.executive_summary }}</p>
            <div v-if="result.fallback_summary.key_findings?.length">
              <div class="sub-label">Hallazgos clave</div>
              <ul class="findings-list">
                <li class="finding-item" v-for="(f, i) in result.fallback_summary.key_findings" :key="i">
                  <span class="finding-num">{{ String(i+1).padStart(2,'0') }}</span>
                  <span>{{ f }}</span>
                </li>
              </ul>
            </div>
            <div v-if="result.fallback_summary.recommendation">
              <div class="sub-label">Recomendación</div>
              <div class="recommendation">→ {{ result.fallback_summary.recommendation }}</div>
            </div>
            <div class="ai-note">⚡ Análisis de respaldo — Gemini no disponible</div>
          </div>
        </div>

        <div class="reset-area">
          <button class="btn btn-ghost" @click="reset">↺ Analizar otro archivo</button>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { analyzeFile } from './services/api.js'

const fileInput = ref(null)
const selectedFile = ref(null)
const loading = ref(false)
const result = ref(null)
const error = ref(null)
const isDragging = ref(false)
const loadingStep = ref(0)
let stepTimer = null

const hasCategorical = computed(() => {
  const cs = result.value?.metrics?.categorical_summary
  return cs && Object.keys(cs).length > 0
})

function barWidth(count, dist) {
  const max = Math.max(...Object.values(dist))
  return Math.round((count / max) * 100)
}

function fmt(n) {
  if (n == null) return '—'
  return Number(n).toLocaleString('es-PE', { maximumFractionDigits: 2 })
}

// Convierte markdown básico a HTML seguro
function renderMarkdown(text) {
  if (!text) return ''
  return text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/### (.+)/g, '<h3>$1</h3>')
    .replace(/## (.+)/g, '<h2>$1</h2>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/^---$/gm, '<hr>')
    .replace(/^\d+\.\s+(.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>)/gs, '<ol>$1</ol>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/^(?!<[hol]|<hr)(.+)$/gm, '<p>$1</p>')
    .replace(/<p><\/p>/g, '')
}

function stepClass(idx) {
  if (loadingStep.value > idx) return 'done'
  if (loadingStep.value === idx) return 'active'
  return ''
}

function formatSize(bytes) {
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function triggerInput() { fileInput.value.click() }
function onFileChange(e) { const f = e.target.files[0]; if (f) selectedFile.value = f }
function onDrop(e) {
  isDragging.value = false
  const f = e.dataTransfer.files[0]
  if (f && (f.name.endsWith('.xlsx') || f.name.endsWith('.xls'))) selectedFile.value = f
}

function startStepTimer() {
  loadingStep.value = 0
  stepTimer = setInterval(() => { if (loadingStep.value < 3) loadingStep.value++ }, 1800)
}
function stopStepTimer() { clearInterval(stepTimer); loadingStep.value = 4 }

async function analyze() {
  if (!selectedFile.value) return
  loading.value = true; error.value = null; result.value = null
  startStepTimer()
  try {
    const data = await analyzeFile(selectedFile.value)
    stopStepTimer()
    result.value = data
  } catch (e) {
    stopStepTimer()
    error.value = e.message || 'Error al conectar con el servidor.'
  } finally {
    loading.value = false
  }
}

function reset() {
  selectedFile.value = null; result.value = null; error.value = null; loading.value = false
  if (fileInput.value) fileInput.value.value = ''
}
</script>

<style scoped>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
.app { font-family: 'Segoe UI', system-ui, sans-serif; background: #0a0a0f; color: #f0f0f8; min-height: 100vh; }
nav { display: flex; align-items: center; justify-content: space-between; padding: 1rem 2rem; border-bottom: 1px solid rgba(255,255,255,0.08); background: rgba(10,10,15,0.95); position: sticky; top: 0; z-index: 100; }
.logo { display: flex; align-items: center; gap: 10px; font-size: 1.05rem; font-weight: 700; }
.logo-icon { font-size: 20px; }
.nav-badges { display: flex; gap: 8px; }
.badge { font-size: 11px; padding: 3px 10px; border-radius: 999px; font-weight: 500; }
.badge-ai { background: rgba(108,99,255,0.2); color: #a78bfa; border: 1px solid rgba(108,99,255,0.3); }
.badge-green { background: rgba(34,211,160,0.15); color: #22d3a0; border: 1px solid rgba(34,211,160,0.25); }
main { max-width: 1050px; margin: 0 auto; padding: 3rem 2rem; }
.hero { text-align: center; margin-bottom: 3rem; }
.hero-eyebrow { font-size: 12px; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: #a78bfa; margin-bottom: 1rem; }
.hero h1 { font-size: clamp(2rem, 5vw, 3rem); font-weight: 700; letter-spacing: -0.03em; line-height: 1.15; margin-bottom: 1rem; background: linear-gradient(135deg, #fff 0%, #a78bfa 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.hero-sub { color: #8888aa; font-size: 1rem; max-width: 500px; margin: 0 auto; line-height: 1.6; }
.upload-zone { border: 1.5px dashed rgba(255,255,255,0.14); border-radius: 20px; padding: 3rem 2rem; text-align: center; cursor: pointer; transition: all 0.2s; background: #13131c; }
.upload-zone:hover, .upload-zone.drag-over { border-color: #6c63ff; background: rgba(108,99,255,0.06); }
.upload-zone input { display: none; }
.upload-icon { font-size: 2.5rem; margin-bottom: 1rem; display: block; }
.upload-zone h3 { font-size: 1.1rem; font-weight: 600; margin-bottom: 0.4rem; }
.upload-zone p { color: #8888aa; font-size: 0.9rem; }
.file-selected { margin-top: 1rem; display: inline-flex; align-items: center; gap: 8px; background: rgba(34,211,160,0.1); border: 1px solid rgba(34,211,160,0.25); border-radius: 8px; padding: 0.5rem 1rem; font-size: 0.88rem; color: #22d3a0; }
.file-size { opacity: 0.6; font-size: 11px; }
.btn-wrapper { text-align: center; margin-top: 1.5rem; }
.btn { display: inline-flex; align-items: center; gap: 8px; padding: 0.75rem 2rem; border-radius: 12px; font-size: 0.95rem; font-weight: 600; cursor: pointer; border: none; font-family: inherit; transition: all 0.2s; }
.btn-primary { background: linear-gradient(135deg, #6c63ff, #9333ea); color: white; box-shadow: 0 4px 20px rgba(108,99,255,0.35); }
.btn-primary:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 6px 28px rgba(108,99,255,0.5); }
.btn-primary:disabled { opacity: 0.45; cursor: not-allowed; }
.btn-ghost { background: transparent; border: 1px solid rgba(255,255,255,0.14); color: #8888aa; }
.btn-ghost:hover { border-color: #6c63ff; color: #a78bfa; }
.loader-wrapper { text-align: center; padding: 4rem 2rem; }
.loader { width: 44px; height: 44px; margin: 0 auto 1.5rem; border: 3px solid rgba(255,255,255,0.1); border-top-color: #6c63ff; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.loader-title { font-size: 1rem; font-weight: 600; margin-bottom: 0.4rem; }
.loader-sub { color: #8888aa; font-size: 0.88rem; margin-bottom: 1.5rem; }
.loader-steps { display: flex; flex-direction: column; gap: 6px; align-items: center; }
.loader-step { font-size: 0.85rem; color: #555577; display: flex; align-items: center; gap: 8px; transition: color 0.3s; }
.loader-step.active { color: #a78bfa; }
.loader-step.done { color: #22d3a0; }
.step-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; min-width: 6px; }
.error-card { background: rgba(248,113,113,0.08); border: 1px solid rgba(248,113,113,0.25); border-radius: 14px; padding: 1.5rem; text-align: center; color: #f87171; }
.error-card h3 { margin-bottom: 0.5rem; }
.results { animation: fadeUp 0.5s ease; }
@keyframes fadeUp { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }
.section-label { font-size: 11px; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: #8888aa; margin-bottom: 1rem; margin-top: 2rem; }
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin-bottom: 1rem; }
.kpi-card { background: #13131c; border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 1.25rem; }
.kpi-label { font-size: 12px; color: #8888aa; margin-bottom: 6px; font-weight: 500; }
.kpi-value { font-size: 1.75rem; font-weight: 700; letter-spacing: -0.03em; }
.kpi-sub { font-size: 11px; color: #8888aa; margin-top: 4px; }
.kpi-purple .kpi-value { color: #a78bfa; }
.kpi-green .kpi-value { color: #22d3a0; }
.kpi-amber .kpi-value { color: #f59e0b; }
.kpi-teal .kpi-value { color: #2dd4bf; }
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 1rem; }
@media (max-width: 680px) { .two-col { grid-template-columns: 1fr; } }
.card { background: #13131c; border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; padding: 1.5rem; }
.card-title { font-size: 0.95rem; font-weight: 600; margin-bottom: 1rem; }
.sub-label { font-size: 11px; font-weight: 600; letter-spacing: 0.07em; text-transform: uppercase; color: #8888aa; margin-bottom: 6px; }
.tag-list { display: flex; flex-wrap: wrap; gap: 7px; }
.tag { font-size: 12px; padding: 4px 10px; border-radius: 6px; font-weight: 500; }
.tag-num { background: rgba(108,99,255,0.15); color: #a78bfa; border: 1px solid rgba(108,99,255,0.2); }
.tag-txt { background: rgba(34,211,160,0.12); color: #22d3a0; border: 1px solid rgba(34,211,160,0.2); }
.tag-cat { background: rgba(245,158,11,0.12); color: #f59e0b; border: 1px solid rgba(245,158,11,0.2); }
.tag-date { background: rgba(45,212,191,0.12); color: #2dd4bf; border: 1px solid rgba(45,212,191,0.2); }
.empty-state { color: #8888aa; font-size: 0.85rem; font-style: italic; }
.metrics-table { width: 100%; border-collapse: collapse; }
.metrics-table tr { border-bottom: 1px solid rgba(255,255,255,0.05); }
.metrics-table tr:last-child { border-bottom: none; }
.metrics-table td { padding: 6px 4px; font-size: 0.85rem; }
.metrics-table td:first-child { color: #8888aa; }
.metrics-table td:last-child { text-align: right; font-weight: 500; }
.chart-wrapper { background: #13131c; border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; padding: 1.5rem; margin-bottom: 1rem; }
.chart-scroll { display: flex; flex-wrap: wrap; gap: 2rem; }
.cat-block { flex: 1 1 200px; }
.bar-row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.bar-label { font-size: 12px; color: #8888aa; min-width: 90px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.bar-track { flex: 1; background: rgba(255,255,255,0.06); border-radius: 4px; height: 8px; overflow: hidden; }
.bar-fill { height: 100%; background: linear-gradient(90deg, #6c63ff, #a78bfa); border-radius: 4px; transition: width 0.6s ease; }
.bar-count { font-size: 12px; color: #a78bfa; font-weight: 600; min-width: 20px; text-align: right; }
.ai-card { background: #13131c; border: 1px solid rgba(108,99,255,0.25); border-radius: 20px; padding: 2rem; position: relative; margin-bottom: 1rem; }
.ai-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, #6c63ff, #a78bfa, #22d3a0); border-radius: 20px 20px 0 0; }
.ai-badge { display: inline-flex; align-items: center; gap: 6px; font-size: 11px; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: #a78bfa; background: rgba(108,99,255,0.12); border: 1px solid rgba(108,99,255,0.25); padding: 4px 10px; border-radius: 999px; margin-bottom: 1.25rem; }
.ai-text { font-size: 0.93rem; line-height: 1.75; color: #d0d0e8; }
.ai-text :deep(h2) { font-size: 1rem; font-weight: 700; color: #a78bfa; margin: 1.25rem 0 0.5rem; }
.ai-text :deep(h3) { font-size: 0.95rem; font-weight: 600; color: #c4b5fd; margin: 1rem 0 0.4rem; }
.ai-text :deep(strong) { color: #f0f0f8; font-weight: 600; }
.ai-text :deep(p) { margin-bottom: 0.75rem; }
.ai-text :deep(ol) { padding-left: 1.25rem; margin: 0.5rem 0; }
.ai-text :deep(li) { margin-bottom: 0.5rem; }
.ai-text :deep(hr) { border: none; border-top: 1px solid rgba(255,255,255,0.08); margin: 1rem 0; }
.executive-summary { font-size: 0.97rem; line-height: 1.7; color: #f0f0f8; margin-bottom: 1.5rem; }
.findings-list { list-style: none; display: flex; flex-direction: column; gap: 9px; margin-bottom: 1.5rem; }
.finding-item { display: flex; gap: 12px; align-items: flex-start; background: rgba(108,99,255,0.06); border: 1px solid rgba(108,99,255,0.12); border-radius: 10px; padding: 0.85rem 1rem; font-size: 0.91rem; line-height: 1.5; }
.finding-num { width: 22px; height: 22px; min-width: 22px; border-radius: 6px; background: rgba(108,99,255,0.25); color: #a78bfa; font-size: 11px; font-weight: 700; display: flex; align-items: center; justify-content: center; }
.recommendation { background: rgba(34,211,160,0.08); border: 1px solid rgba(34,211,160,0.2); border-radius: 12px; padding: 1rem 1.25rem; font-size: 0.91rem; line-height: 1.6; }
.ai-note { margin-top: 1rem; font-size: 0.8rem; color: #555577; font-style: italic; }
.reset-area { text-align: center; margin-top: 2.5rem; padding-top: 2rem; border-top: 1px solid rgba(255,255,255,0.07); }
</style>