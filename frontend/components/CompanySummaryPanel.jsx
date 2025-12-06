const { useMemo } = React;

function CompanySummaryPanel({
  loading,
  rows,
  filters,
  setFilters,
  isCSVerified,
  verifyCSCell,
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
    'income','rentpassedtoowners','bankfees','c_auto','c_donate','c_entertainment','c_internet',
    'c_license','c_mobile','c_off_exp','c_parktoll','c_phone','c_website','ignore','insurane',
    'proffees','utilities','profit'
  ];

  return (
    <div className="tabcontent">
      <div className="card">
        {loading ? (
          <div>Loading...</div>
        ) : (
          <div className="overflow-x-auto" style={{ overflowX: 'auto', maxWidth: '100%' }}>
            <table className="min-w-full" style={{ tableLayout: 'fixed', width: '100%' }}>
              <thead>
                <tr>
                  <th style={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>Name</th>
                  {metricFields.map(f => (
                    <th key={f} style={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>{f}</th>
                  ))}
                </tr>
                <tr>
                  <th>
                    <input
                      name="Name"
                      value={filters.Name}
                      onChange={(e)=> onFilterChange('Name', e.target.value)}
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
                  <tr key={`cs-${idx}`}>
                    <td style={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>{r.Name}</td>
                    {metricFields.map((f,i)=> (
                      <td
                        key={`cc-${i}`}
                        className={`break-words whitespace-pre-wrap ${isCSVerified && isCSVerified(r,f) ? 'bg-green-100' : ''}`}
                      >
                        <div className="flex flex-col items-end gap-1">
                          <span
                            style={{ wordBreak:'break-word', whiteSpace:'pre-wrap' }}
                            className="self-start"
                          >
                            {r[f]}
                          </span>
                          <button
                            type="button"
                            title={isCSVerified && isCSVerified(r,f) ? 'Unverify' : 'Mark verified'}
                            className={`text-white rounded disabled:opacity-50 ${isCSVerified && isCSVerified(r,f) ? 'bg-emerald-600 hover:bg-emerald-700' : 'bg-gray-500 hover:bg-gray-600'}`}
                            style={{ width: '6px', height: '6px', padding: 0, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: '6px', lineHeight: '6px' }}
                            onClick={()=> verifyCSCell && verifyCSCell(r, f)}
                          >
                            ✓
                          </button>
                        </div>
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

window.CompanySummaryPanel = CompanySummaryPanel;
