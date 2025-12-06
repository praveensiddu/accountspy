function matchesText(val, query) {
  const s = (val || '').toString().toLowerCase();
  const t = (query || '').toString().toLowerCase().trim();
  if (!t) return true;
  const isNeg = t.startsWith('!');
  const needle = isNeg ? t.slice(1) : t;
  if (!needle) return true;
  const has = s.includes(needle);
  return isNeg ? !has : has;
}

window.filterUtils = window.filterUtils || {};
window.filterUtils.matchesText = matchesText;
