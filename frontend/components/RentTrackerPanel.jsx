const { useMemo } = React;

function RentTrackerPanel({ loading, rows }) {
  const sortedRows = useMemo(() => {
    const list = Array.isArray(rows) ? rows.slice() : [];
    return list.sort((a, b) => {
      const ap = (a.property || '').toLowerCase();
      const bp = (b.property || '').toLowerCase();
      if (ap < bp) return -1; if (ap > bp) return 1; return 0;
    });
  }, [rows]);

  const totals = useMemo(() => {
    const months = ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec'];
    const acc = { jan:0, feb:0, mar:0, apr:0, may:0, jun:0, jul:0, aug:0, sep:0, oct:0, nov:0, dec:0 };
    for (const r of (sortedRows || [])) {
      for (const m of months) {
        const raw = (r[m] == null ? 0 : r[m]);
        const v = Number(raw);
        if (Number.isFinite(v)) acc[m] += v;
      }
    }
    return acc;
  }, [sortedRows]);

  return (
    <div className="tabcontent">
      <div className="card">
        {loading ? (
          <div>Loading...</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>property</th>
                <th>Jan</th>
                <th>Feb</th>
                <th>Mar</th>
                <th>Apr</th>
                <th>May</th>
                <th>Jun</th>
                <th>Jul</th>
                <th>Aug</th>
                <th>Sep</th>
                <th>Oct</th>
                <th>Nov</th>
                <th>Dec</th>
              </tr>
            </thead>
            <tbody>
              {sortedRows.map((r) => (
                <tr key={r.property || ''}>
                  <td>{r.property}</td>
                  <td>{r.jan || 0}</td>
                  <td>{r.feb || 0}</td>
                  <td>{r.mar || 0}</td>
                  <td>{r.apr || 0}</td>
                  <td>{r.may || 0}</td>
                  <td>{r.jun || 0}</td>
                  <td>{r.jul || 0}</td>
                  <td>{r.aug || 0}</td>
                  <td>{r.sep || 0}</td>
                  <td>{r.oct || 0}</td>
                  <td>{r.nov || 0}</td>
                  <td>{r.dec || 0}</td>
                </tr>
              ))}
              {sortedRows.length === 0 && (
                <tr><td colSpan="13" className="muted">No rent tracker data</td></tr>
              )}
              {sortedRows.length > 0 && (
                <tr>
                  <td><strong>Total</strong></td>
                  <td>{totals.jan}</td>
                  <td>{totals.feb}</td>
                  <td>{totals.mar}</td>
                  <td>{totals.apr}</td>
                  <td>{totals.may}</td>
                  <td>{totals.jun}</td>
                  <td>{totals.jul}</td>
                  <td>{totals.aug}</td>
                  <td>{totals.sep}</td>
                  <td>{totals.oct}</td>
                  <td>{totals.nov}</td>
                  <td>{totals.dec}</td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

window.RentTrackerPanel = RentTrackerPanel;
