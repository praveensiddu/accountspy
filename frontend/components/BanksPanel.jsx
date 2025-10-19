const BanksPanelExt = ({ banks, loading, reload }) => {
  const [form, setForm] = React.useState({ name: '', date_format: '', delim: '', ignore_lines_contains: '', ignore_lines_startswith: '', columnsText: '' });
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState('');
  const [open, setOpen] = React.useState(false);
  const Modal = window.Modal;
  const [mode, setMode] = React.useState('add');
  const [originalKey, setOriginalKey] = React.useState('');
  const onChange = (e) => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));
  };
  const onEdit = (b) => {
    setMode('edit');
    setOriginalKey(b.name);
    setForm({
      name: b.name,
      date_format: b.date_format || '',
      delim: b.delim || '',
      ignore_lines_contains: (b.ignore_lines_contains || []).join('|'),
      ignore_lines_startswith: (b.ignore_lines_startswith || []).join('|'),
      columnsText: (b.columns || []).map(obj => JSON.stringify(obj)).join('\n'),
    });
    setOpen(true);
  };
  const onSubmit = async (e) => {
    e.preventDefault(); setSaving(true); setError('');
    try {
      const name = (form.name || '').trim().toLowerCase();
      if (!name) throw new Error('name is required');
      const ignore_lines_contains = (form.ignore_lines_contains || '').split('|').map(s=>s.trim()).filter(Boolean);
      const ignore_lines_startswith = (form.ignore_lines_startswith || '').split('|').map(s=>s.trim()).filter(Boolean);
      let columns = [];
      if (form.columnsText && form.columnsText.trim()) {
        const lines = form.columnsText.split(/\r?\n/).map(s=>s.trim()).filter(Boolean);
        for (const ln of lines) {
          try { const obj = JSON.parse(ln); if (obj && typeof obj === 'object') columns.push(obj); } catch (_) {}
        }
      }
      const payload = {
        name,
        date_format: form.date_format || undefined,
        delim: form.delim || undefined,
        ignore_lines_contains: ignore_lines_contains.length ? ignore_lines_contains : undefined,
        ignore_lines_startswith: ignore_lines_startswith.length ? ignore_lines_startswith : undefined,
        columns: columns.length ? columns : undefined,
      };
      if (mode === 'edit' && originalKey) {
        if (originalKey !== name) {
          await window.api.removeBank(originalKey);
        } else {
          await window.api.removeBank(originalKey);
        }
      }
      await window.api.addBank(payload);
      setForm({ name: '', date_format: '', delim: '', ignore_lines_contains: '', ignore_lines_startswith: '', columnsText: '' });
      setOriginalKey('');
      setMode('add');
      setOpen(false);
      await reload();
    } catch (err) { setError(err.message || 'Error'); } finally { setSaving(false); }
  };
  const onDelete = async (name) => {
    if (!confirm(`Delete ${name}?`)) return;
    try { await window.api.removeBank(name); await reload(); } catch (err) { alert(err.message || 'Error'); }
  };
  return (
    <React.Fragment>
      <h2>Banks</h2>
      <div className="actions" style={{ marginBottom: 12 }}>
        <button type="button" onClick={() => { setForm({ name: '', date_format: '', delim: '', ignore_lines_contains: '', ignore_lines_startswith: '', columnsText: '' }); setMode('add'); setOriginalKey(''); setOpen(true); }}>Add bank</button>
        <button type="button" onClick={reload} disabled={loading}>Refresh</button>
      </div>
      <Modal title={mode==='edit' ? 'Edit Bank' : 'Add Bank'} open={open} onClose={() => { setOpen(false); setMode('add'); setOriginalKey(''); }} onSubmit={onSubmit} submitLabel={saving ? 'Saving...' : 'Save'}>
        <div className="row" style={{display:'block'}}>
          <div className="col" style={{display:'flex', gap:8, alignItems:'center', marginBottom:8}}>
            <label style={{flex:1}}>name<br/>
              <input name="name" value={form.name} onChange={onChange} placeholder="lowercase id [a-z0-9_]" />
            </label>
            <span className="muted" style={{flex:1}}>Unique lowercase id</span>
          </div>
          <div className="col" style={{display:'flex', gap:8, alignItems:'center', marginBottom:8}}>
            <label style={{flex:1}}>date_format<br/>
              <input name="date_format" value={form.date_format} onChange={onChange} placeholder="M/d/yyyy" />
            </label>
            <span className="muted" style={{flex:1}}>e.g., M/d/yyyy</span>
          </div>
          <div className="col" style={{display:'flex', gap:8, alignItems:'center', marginBottom:8}}>
            <label style={{flex:1}}>delim<br/>
              <input name="delim" value={form.delim} onChange={onChange} placeholder="," />
            </label>
            <span className="muted" style={{flex:1}}>CSV delimiter</span>
          </div>
          <div className="col" style={{display:'flex', gap:8, alignItems:'center', marginBottom:8}}>
            <label style={{flex:1}}>ignore_lines_contains (| separated)<br/>
              <input name="ignore_lines_contains" value={form.ignore_lines_contains} onChange={onChange} placeholder="foo|bar" />
            </label>
            <span className="muted" style={{flex:1}}>Pipe-separated filters</span>
          </div>
          <div className="col" style={{display:'flex', gap:8, alignItems:'center', marginBottom:8}}>
            <label style={{flex:1}}>ignore_lines_startswith (| separated)<br/>
              <input name="ignore_lines_startswith" value={form.ignore_lines_startswith} onChange={onChange} placeholder="Header|Total" />
            </label>
            <span className="muted" style={{flex:1}}>Pipe-separated prefixes</span>
          </div>
          <div className="col" style={{display:'flex', gap:8, alignItems:'flex-start', marginBottom:8}}>
            <label style={{flex:1}}>columns (one JSON per line)<br/>
              <textarea name="columnsText" value={form.columnsText} onChange={onChange} rows="6" placeholder='{"date":1}\n{"description":2}\n{"debit":3}' style={{width:'100%'}} />
            </label>
            <span className="muted" style={{flex:1}}>One JSON object per line</span>
          </div>
          {error && <div className="error" style={{ marginTop: 8 }}>{error}</div>}
        </div>
      </Modal>
      <div className="card">
        {loading ? (<div>Loading...</div>) : (
          <table>
            <thead>
              <tr>
                <th>name</th>
                <th>date_format</th>
                <th>delim</th>
                <th>ignore_lines_contains</th>
                <th>ignore_lines_startswith</th>
                <th>columns</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {banks.map(b => (
                <tr key={b.name}>
                  <td>{b.name}</td>
                  <td>{b.date_format || ''}</td>
                  <td>{b.delim || ''}</td>
                  <td>{(b.ignore_lines_contains || []).join(' | ')}</td>
                  <td>{(b.ignore_lines_startswith || []).join(' | ')}</td>
                  <td>{(b.columns || []).map((c, i) => (
                    <span key={i}>{Object.entries(c).map(([k,v]) => `${k}:${v}`).join(', ')}{i < (b.columns.length-1) ? ' | ' : ''}</span>
                  ))}</td>
                  <td>
                    <button onClick={() => onEdit(b)} style={{marginRight:8, background:'#374151'}}>Edit</button>
                    <button onClick={() => onDelete(b.name)}>Delete</button>
                  </td>
                </tr>
              ))}
              {banks.length === 0 && (<tr><td colSpan="7" className="muted">No bank configs</td></tr>)}
            </tbody>
          </table>
        )}
      </div>
    </React.Fragment>
  );
};

window.BanksPanelExt = BanksPanelExt;
