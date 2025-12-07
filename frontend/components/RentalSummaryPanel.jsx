const { useMemo, useState } = React;

function RentalSummaryPanel({
  loading,
  rows,
  filters,
  setFilters,
  isRSVerified,
  verifyRSCell,
}) {
  const [reversePanel, setReversePanel] = useState({ open: false, property: '', field: '', lines: [] });
  const filteredRows = useMemo(() => {
    const list = Array.isArray(rows) ? rows : [];
    return list.filter(r => {
      const f = filters || {};
      const keys = Object.keys(f);
      for (let k of keys) {
        const fv = (f[k] || '').toString().trim();
        if (!fv) continue;
        const rv = (r[k] == null ? '' : String(r[k])).toLowerCase();
        if (!rv.includes(fv.toLowerCase())) return false;
      }
      return true;
    });
  }, [rows, filters]);

  const onFilterChange = (field, value) => {
    if (!setFilters) return;
    setFilters(prev => ({ ...(prev || {}), [field]: value }));
  };

  const metricFields = [
    'rent','commissions','insurance','proffees','mortgageinterest','repairs','tax','utilities',
    'depreciation','hoa','other','costbasis','renteddays','profit'
  ];

  const totals = useMemo(() => {
    const list = Array.isArray(filteredRows) ? filteredRows : [];
    const sum = (f) => {
      try {
        return list.reduce((acc, row) => {
          const v = row && row[f];
          const n = Number(v);
          return Number.isFinite(n) ? acc + n : acc;
        }, 0);
      } catch (_) { return 0; }
    };
    const out = {};
    metricFields.forEach(f => { out[f] = sum(f); });
    return out;
  }, [filteredRows]);

  const buildReverseLines = (row, field) => {
    try {
      const rev = row && row._reverse;
      if (!rev || typeof rev !== 'object') return [];
      const lines = [];
      const key = String(field || '').toLowerCase();
      const arr = rev[key];
      if (Array.isArray(arr) && arr.length > 0) {
        arr.forEach((x) => {
          lines.push(`${x.bankaccountname||''} | ${x.description||''} | ${x.credit!=null?x.credit:''}`);
        });
      }
      return lines;
    } catch (_) { return []; }
  };

  const handleCellClick = (row, field) => {
    const lines = buildReverseLines(row, field);
    if (!lines || lines.length === 0) return;
    setReversePanel({
      open: true,
      property: row && row.property ? String(row.property) : '',
      field,
      lines,
    });
  };

  return (
    <div className="tabcontent">
      <div className="card">
        {loading ? (
          <div>Loading...</div>
        ) : (
          <div className="overflow-x-auto" style={{ overflowX: 'auto', maxWidth: '100%' }}>
            <table className="min-w-full" style={{ tableLayout: 'fixed' }}>
              <thead>
                <tr>
                  <th style={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>property</th>
                  {metricFields.map(f => (
                    <th key={f} style={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>{f}</th>
                  ))}
                </tr>
                <tr>
                  <th>
                    <input
                      name="property"
                      value={filters.property}
                      onChange={(e)=> onFilterChange('property', e.target.value)}
                      placeholder="filter"
                    />
                  </th>
                  {metricFields.map(f => (
                    <th key={`filter-${f}`}>
                      <input
                        name={f}
                        value={filters[f]}
                        onChange={(e)=> onFilterChange(f, e.target.value)}
                        placeholder="filter"
                      />
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filteredRows.length === 0 ? (
                  <tr><td colSpan={1 + metricFields.length} className="muted">No rows</td></tr>
                ) : filteredRows.map((r, idx) => (
                  <tr key={`rs-${idx}`}>
                    <td className="break-words whitespace-pre-wrap">{r.property}</td>
                    {metricFields.map((f,i)=> {
                      const lines = buildReverseLines(r, f);
                      const hasLines = lines && lines.length > 0;
                      return (
                        <td
                          key={`c-${i}`}
                          className={`break-words whitespace-pre-wrap ${isRSVerified && isRSVerified(r,f) ? 'bg-green-100' : ''}`}
                        >
                          <div className="flex flex-col items-end gap-1">
                            <span
                              style={{ wordBreak:'break-word', whiteSpace:'pre-wrap', cursor: hasLines ? 'pointer' : 'default' }}
                              className="self-start"
                              onClick={() => hasLines && handleCellClick(r, f)}
                            >
                              {r[f]}
                            </span>
                            <button
                              type="button"
                              title={isRSVerified && isRSVerified(r,f) ? 'Unverify' : 'Mark verified'}
                              className={`text-white rounded ${isRSVerified && isRSVerified(r,f) ? 'bg-emerald-600 hover:bg-emerald-700' : 'bg-gray-500 hover:bg-gray-600'}`}
                              style={{ width: '6px', height: '6px', padding: 0, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: '6px', lineHeight: '6px' }}
                              onClick={()=> verifyRSCell && verifyRSCell(r, f)}
                            >
                              ✓
                            </button>
                          </div>
                        </td>
                      );
                    })}
                  </tr>
                ))}
                {filteredRows.length > 0 && (
                  <tr key="rs-total">
                    <td className="font-semibold">total</td>
                    {metricFields.map((f, i) => (
                      <td key={`t-${i}`} className="font-semibold">{Math.round(totals[f] || 0)}</td>
                    ))}
                  </tr>
                )}
              </tbody>
            </table>
            {reversePanel.open && (
              <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40">
                <div className="bg-white rounded shadow-lg max-w-3xl w-full mx-4 max-h-[80vh] flex flex-col">
                  <div className="flex justify-between items-center px-4 py-2 border-b">
                    <div className="font-semibold text-sm">
                      Details for {reversePanel.property || 'N/A'}{reversePanel.field ? ` / ${reversePanel.field}` : ''}
                    </div>
                    <button
                      type="button"
                      className="px-2 py-1 bg-gray-600 text-white rounded-md text-xs hover:bg-gray-700"
                      onClick={() => setReversePanel({ open: false, property: '', field: '', lines: [] })}
                    >
                      Close
                    </button>
                  </div>
                  <div className="px-4 py-2 text-xs overflow-y-auto whitespace-pre-wrap break-words" style={{ maxHeight: '60vh' }}>
                    {reversePanel.lines.map((line, idx) => (
                      <div key={`rev-${idx}`}>{line}</div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

window.RentalSummaryPanel = RentalSummaryPanel;
