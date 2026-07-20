let names = [];
let currentIndex = 0;
let bookmarks = new Set(JSON.parse(localStorage.getItem('lalithaBookmarks') || '[]'));
let bookmarkMode = false;
let summaryMaxScroll = 0;
let meaningMode = 'summary';

const $ = id => document.getElementById(id);
const esc = s => (s || '').replace(/[&<>]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
const paras = lines => (lines || []).map(x => `<p>${esc(x)}</p>`).join('');

function renderMeaning(entry) {
  return paras(meaningMode === 'esoteric' ? entry.esoteric : entry.summary);
}

function updateMeaningTabs() {
  const isEsoteric = meaningMode === 'esoteric';
  $('summaryTab').classList.toggle('active', !isEsoteric);
  $('esotericTab').classList.toggle('active', isEsoteric);
  $('summaryTab').setAttribute('aria-selected', String(!isEsoteric));
  $('esotericTab').setAttribute('aria-selected', String(isEsoteric));
}

function renderList() {
  const q = $('search').value.trim().toLowerCase();
  const list = $('nameList');
  const rows = names.filter(n =>
    (!bookmarkMode || bookmarks.has(n.number)) &&
    (!q || n.searchText.includes(q))
  );

  list.innerHTML = rows.map(n =>
    `<button class="name-item ${n.number === names[currentIndex].number ? 'active' : ''}" data-num="${n.number}">
      <span class="num">${n.number}</span>
      <span class="nm">${esc(n.name)}</span>
      <span class="star">${bookmarks.has(n.number) ? '★' : ''}</span>
    </button>`
  ).join('');

  list.querySelectorAll('.name-item').forEach(btn =>
    btn.addEventListener('click', () => selectByNumber(+btn.dataset.num))
  );
}

function renderEntry() {
  const n = names[currentIndex];
  meaningMode = 'summary';
  $('nameNumber').textContent = `Nāma ${n.number}`;
  $('nameTitle').textContent = n.name;
  $('samasa').innerHTML = paras(n.samasa);
  $('wordByWord').innerHTML = paras(n.wordByWord);
  $('summary').innerHTML = renderMeaning(n);
  $('bookmarkBtn').textContent = bookmarks.has(n.number) ? '★' : '☆';
  updateMeaningTabs();
  $('summary').scrollTop = 0;
  updateSummarySlider();
  renderList();
}

function setMeaningMode(mode) {
  meaningMode = mode;
  $('summary').innerHTML = renderMeaning(names[currentIndex]);
  updateMeaningTabs();
  $('summary').scrollTop = 0;
  updateSummarySlider();
}

function selectByNumber(num) {
  const idx = names.findIndex(n => n.number === num);
  if (idx >= 0) {
    currentIndex = idx;
    renderEntry();
  }
}

function updateSummarySlider() {
  const summary = $('summary');
  const slider = $('summaryScroll');
  const thumb = $('summaryScrollThumb');
  summaryMaxScroll = Math.max(0, summary.scrollHeight - summary.clientHeight);
  const pct = summaryMaxScroll ? Math.min(1, summary.scrollTop / summaryMaxScroll) : 0;

  slider.classList.toggle('disabled', summaryMaxScroll === 0);
  slider.setAttribute('aria-valuemax', String(summaryMaxScroll || 1));
  slider.setAttribute('aria-valuenow', String(Math.round(summary.scrollTop)));
  thumb.style.top = `${pct * 100}%`;
}

function setSummaryScrollFromClientY(clientY) {
  if (summaryMaxScroll === 0) return;
  const track = $('summaryScroll').getBoundingClientRect();
  const pct = Math.max(0, Math.min(1, (clientY - track.top) / track.height));
  $('summary').scrollTop = Math.round(summaryMaxScroll * pct);
}

function startSummarySliderDrag(event) {
  if (summaryMaxScroll === 0) return;
  event.preventDefault();
  const slider = $('summaryScroll');
  slider.setPointerCapture?.(event.pointerId);
  setSummaryScrollFromClientY(event.clientY);
  slider.addEventListener('pointermove', moveSummarySlider);
  slider.addEventListener('pointerup', stopSummarySliderDrag, { once: true });
  slider.addEventListener('pointercancel', stopSummarySliderDrag, { once: true });
}

function moveSummarySlider(event) {
  setSummaryScrollFromClientY(event.clientY);
}

function stopSummarySliderDrag(event) {
  const slider = $('summaryScroll');
  slider.releasePointerCapture?.(event.pointerId);
  slider.removeEventListener('pointermove', moveSummarySlider);
}

function handleSummarySliderKey(event) {
  if (summaryMaxScroll === 0) return;
  const summary = $('summary');
  const smallStep = Math.max(24, Math.round(summary.clientHeight * 0.12));
  const largeStep = Math.max(60, Math.round(summary.clientHeight * 0.75));
  const movement = {
    ArrowDown: smallStep,
    ArrowRight: smallStep,
    ArrowUp: -smallStep,
    ArrowLeft: -smallStep,
    PageDown: largeStep,
    PageUp: -largeStep,
    Home: -summaryMaxScroll,
    End: summaryMaxScroll
  }[event.key];

  if (movement === undefined) return;
  event.preventDefault();
  summary.scrollTop = Math.max(0, Math.min(summaryMaxScroll, summary.scrollTop + movement));
}

$('prevBtn').addEventListener('click', () => {
  if (currentIndex > 0) {
    currentIndex--;
    renderEntry();
  }
});

$('nextBtn').addEventListener('click', () => {
  if (currentIndex < names.length - 1) {
    currentIndex++;
    renderEntry();
  }
});

$('bookmarkBtn').addEventListener('click', () => {
  const num = names[currentIndex].number;
  bookmarks.has(num) ? bookmarks.delete(num) : bookmarks.add(num);
  localStorage.setItem('lalithaBookmarks', JSON.stringify([...bookmarks]));
  renderEntry();
});

$('search').addEventListener('input', renderList);
$('showAll').addEventListener('click', () => {
  bookmarkMode = false;
  $('showAll').classList.add('active');
  $('showBookmarks').classList.remove('active');
  renderList();
});

$('showBookmarks').addEventListener('click', () => {
  bookmarkMode = true;
  $('showBookmarks').classList.add('active');
  $('showAll').classList.remove('active');
  renderList();
});

$('summary').addEventListener('scroll', updateSummarySlider);
$('summaryTab').addEventListener('click', () => setMeaningMode('summary'));
$('esotericTab').addEventListener('click', () => setMeaningMode('esoteric'));
$('summaryScroll').addEventListener('pointerdown', startSummarySliderDrag);
$('summaryScroll').addEventListener('keydown', handleSummarySliderKey);
window.addEventListener('resize', updateSummarySlider);

document.addEventListener('keydown', e => {
  if (e.key === 'ArrowLeft') $('prevBtn').click();
  if (e.key === 'ArrowRight') $('nextBtn').click();
});

names = window.LALITHA_NAMES || [];
renderEntry();
