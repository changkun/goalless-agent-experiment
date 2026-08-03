(() => {
  const art = document.getElementById('art');
  const gridCanvas = document.getElementById('grid');
  const gctx = gridCanvas.getContext('2d');
  const ctx = art.getContext('2d', { willReadFrequently: true });

  let size = 16;
  let zoom = 10;
  let currentColor = '#89b4fa';
  let tool = 'pen';
  let mirror = false;

  const state = { pixels: null, undoStack: [], redoStack: [] };

  const PRESET_COLORS = [
    '#1e1e2e', '#89b4fa', '#a6e3a1', '#f5c2e7',
    '#f9e2af', '#f38ba8', '#eba0ac', '#94e2d5',
    '#ffffff', '#585b70', '#fab387', '#fab387'
  ];

  const svg = {
    pen: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 19l7-7 3 3-7 7-3-3z"/><path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18z"/><path d="M2 2l7.586 7.586"/><circle cx="11" cy="11" r="2"/></svg>',
    eraser: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 20H9"/><path d="M18 4l4 4L11 20l-4-4L18 4z"/></svg>',
    bucket: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 2v2"/><path d="M14 2v2"/><path d="M12 2v7"/><path d="M3 9l9 -7 9 7v2a5 5 0 0 1 -5 5h-8a5 5 0 0 1 -5 -5z"/><path d="M8 21h8"/></svg>',
    eyedrop: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 22l5-15 3 3 9-9 2 2-9 9 1 1 2-2 2 2-4 5-6-1z"/></svg>'
  };

  init();

  function init() {
    state.pixels = freshGrid(size);
    state.undoStack = [];
    state.redoStack = [];
    buildToolbar();
    buildSwatches();
    bindEvents();
    applyZoom();
  }

  function freshGrid(n) {
    return Array.from({ length: n }, () => Array(n).fill(null));
  }

  function buildToolbar() {
    const tb = document.getElementById('toolbar');
    const tools = [
      { id: 'pen', name: 'Pen', svg: svg.pen },
      { id: 'eraser', name: 'Eraser', svg: svg.eraser },
      { id: 'bucket', name: 'Fill', svg: svg.bucket },
      { id: 'eyedrop', name: 'Pick', svg: svg.eyedrop }
    ];
    tb.innerHTML = '';
    tools.forEach(t => {
      const b = document.createElement('button');
      b.className = 'tool-btn' + (t.id === tool ? ' active' : '');
      b.dataset.tool = t.id;
      b.innerHTML = t.svg + '<span>' + t.name + '</span>';
      b.addEventListener('click', () => setTool(t.id));
      tb.appendChild(b);
    });
  }

  function setTool(t) {
    tool = t;
    document.querySelectorAll('.tool-btn').forEach(b =>
      b.classList.toggle('active', b.dataset.tool === t));
  }

  function buildSwatches() {
    const sw = document.getElementById('swatches');
    sw.innerHTML = '';
    PRESET_COLORS.forEach(c => {
      const d = document.createElement('div');
      d.className = 'swatch' + (c === currentColor ? ' active' : '');
      d.style.background = c;
      d.addEventListener('click', () => selectColor(c, d));
      sw.appendChild(d);
    });
  }

  function selectColor(c, swatchEl) {
    currentColor = c;
    document.getElementById('custom').value = c;
    document.querySelectorAll('.swatch').forEach(s => s.classList.remove('active'));
    if (swatchEl) swatchEl.classList.add('active');
  }

  function bindEvents() {
    document.getElementById('custom').addEventListener('input', e => {
      currentColor = e.target.value;
      document.querySelectorAll('.swatch').forEach(s => s.classList.remove('active'));
    });

    document.getElementById('size').addEventListener('input', e => resize(parseInt(e.target.value, 10)));

    const zoomEl = document.getElementById('zoom');
    zoomEl.addEventListener('input', e => setZoom(parseInt(e.target.value, 10)));

    document.getElementById('symmetric').addEventListener('change', e => { mirror = e.target.checked; });
    document.getElementById('undo').addEventListener('click', undo);
    document.getElementById('redo').addEventListener('click', redo);
    document.getElementById('clear').addEventListener('click', () => { push(); state.pixels = freshGrid(size); render(); });
    document.getElementById('export').addEventListener('click', exportPNG);

    let drawing = false;
    art.addEventListener('contextmenu', e => e.preventDefault());
    art.addEventListener('pointerdown', e => {
      e.preventDefault();
      art.setPointerCapture(e.pointerId);
      drawing = true;
      const pt = eventToPixel(e);
      if (pt) { push(); paint(pt.x, pt.y, e); }
    });
    art.addEventListener('pointermove', e => {
      if (!drawing) return;
      const pt = eventToPixel(e);
      if (pt) paint(pt.x, pt.y, e);
    });
    const endDraw = () => { drawing = false; };
    art.addEventListener('pointerup', endDraw);
    art.addEventListener('pointerleave', endDraw);
  }

  function eventToPixel(e) {
    const rect = art.getBoundingClientRect();
    const x = Math.floor((e.clientX - rect.left) / rect.width * size);
    const y = Math.floor((e.clientY - rect.top) / rect.height * size);
    if (x < 0 || y < 0 || x >= size || y >= size) return null;
    return { x, y };
  }

  function paint(x, y, e) {
    if (tool === 'eyedrop') {
      const c = state.pixels[y][x];
      if (c) selectColor(c, null);
      return;
    }
    if (tool === 'bucket') { floodFill(x, y); render(); return; }

    const color = (e.button === 2 || tool === 'eraser') ? null : currentColor;
    setPixel(x, y, color);
    if (mirror) setPixel(size - 1 - x, y, color);
    render();
  }

  function setPixel(x, y, color) {
    if (x < 0 || y < 0 || x >= size || y >= size) return;
    state.pixels[y][x] = color;
  }

  function floodFill(sx, sy) {
    const target = state.pixels[sy][sx];
    const color = currentColor;
    if (target === color) return;
    const stack = [[sx, sy]];
    const visited = new Set();
    while (stack.length) {
      const [x, y] = stack.pop();
      const k = y * size + x;
      if (visited.has(k)) continue;
      visited.add(k);
      if (state.pixels[y][x] !== target) continue;
      state.pixels[y][x] = color;
      if (x > 0) stack.push([x - 1, y]);
      if (x < size - 1) stack.push([x + 1, y]);
      if (y > 0) stack.push([x, y - 1]);
      if (y < size - 1) stack.push([x, y + 1]);
    }
  }

  function resize(n) {
    if (n === size) return;
    const next = freshGrid(n);
    const copy = Math.min(n, size);
    for (let y = 0; y < copy; y++)
      for (let x = 0; x < copy; x++)
        next[y][x] = state.pixels[y][x];
    push();
    size = n;
    state.pixels = next;
    document.getElementById('sizeVal').textContent = n;
    applyZoom();
  }

  function setZoom(z) {
    zoom = z;
    document.getElementById('zoomVal').textContent = z;
    applyZoom();
  }

  function applyZoom() {
    const dim = size * zoom;
    art.width = dim;
    art.height = dim;
    gridCanvas.width = dim;
    gridCanvas.height = dim;
    art.style.width = dim + 'px';
    art.style.height = dim + 'px';
    gridCanvas.style.width = dim + 'px';
    gridCanvas.style.height = dim + 'px';
    render();
  }

  function render() {
    ctx.clearRect(0, 0, art.width, art.height);
    const cell = art.width / size;
    for (let y = 0; y < size; y++)
      for (let x = 0; x < size; x++) {
        const c = state.pixels[y][x];
        if (!c) continue;
        ctx.fillStyle = c;
        ctx.fillRect(x * cell, y * cell, cell + 0.5, cell + 0.5);
      }

    gctx.clearRect(0, 0, gridCanvas.width, gridCanvas.height);
    gctx.strokeStyle = 'rgba(205,214,244,0.15)';
    gctx.lineWidth = 1;
    const cellG = gridCanvas.width / size;
    gctx.beginPath();
    for (let i = 1; i < size; i++) {
      gctx.moveTo(i * cellG, 0);
      gctx.lineTo(i * cellG, gridCanvas.height);
      gctx.moveTo(0, i * cellG);
      gctx.lineTo(gridCanvas.width, i * cellG);
    }
    gctx.stroke();
  }

  function undo() {
    if (!state.undoStack.length) return;
    state.redoStack.push(state.pixels.map(r => r.slice()));
    state.pixels = state.undoStack.pop();
    render();
  }

  function redo() {
    if (!state.redoStack.length) return;
    state.undoStack.push(state.pixels.map(r => r.slice()));
    state.pixels = state.redoStack.pop();
    render();
  }

  function push() {
    state.undoStack.push(state.pixels.map(r => r.slice()));
    if (state.undoStack.length > 200) state.undoStack.shift();
    state.redoStack = [];
  }

  function exportPNG() {
    const out = document.createElement('canvas');
    out.width = size * zoom;
    out.height = size * zoom;
    const octx = out.getContext('2d');
    const cell = out.width / size;
    for (let y = 0; y < size; y++)
      for (let x = 0; x < size; x++) {
        const c = state.pixels[y][x];
        if (!c) continue;
        octx.fillStyle = c;
        octx.fillRect(x * cell, y * cell, cell, cell);
      }
    const link = document.createElement('a');
    link.download = 'pixel-art.png';
    link.href = out.toDataURL('image/png');
    link.click();
  }
})();
