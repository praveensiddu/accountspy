const { useMemo } = React;

function RentalSummaryPanel({
  loading,
  rows,
  filters,
  setFilters,
  isRSVerified,
  verifyRSCell,
}) {
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
                      const tooltip = (() => {
                        try {
                          const rev = r && r._reverse;
                          if (!rev || typeof rev !== 'object') return '';
                          const lines = [];
                          Object.keys(rev).forEach((k) => {
                            const arr = rev[k];
                            if (!Array.isArray(arr) || arr.length === 0) return;
                            arr.forEach((x) => {
                              lines.push(`${x.bankaccountname||''} | ${x.description||''} | ${x.credit!=null?x.credit:''}`);
                            });
                          });
                          if (lines.length === 0) return '';
                          return lines.join('\n');
                        } catch(_) { return ''; }
                      })();
                      return (
                        <td
                          key={`c-${i}`}
                          className={`break-words whitespace-pre-wrap ${isRSVerified && isRSVerified(r,f) ? 'bg-green-100' : ''}`}
                        >
                          <div className="flex flex-col items-end gap-1">
                            <span
                              title={tooltip}
                              style={{ wordBreak:'break-word', whiteSpace:'pre-wrap' }}
                              className="self-start"
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
          </div>
        )}
      </div>
    </div>
  );
}

window.RentalSummaryPanel = RentalSummaryPanel;
