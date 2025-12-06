const OwnersPanelExt = ({ owners, loading, reload, bankaccounts, items, companies }) => {
  const Modal = window.Modal;
  const MultiSelect = window.MultiSelect;
  const {
    empty,
    form,
    setForm,
    saving,
    open,
    setOpen,
    mode,
    setMode,
    originalKey,
    setOriginalKey,
    onChange,
    onSubmit,
    onDelete,
    onEdit,
  } = window.useOwnerForm({ reload });
  const [filter, setFilter] = React.useState({ name: '', bankaccounts: '', properties: '', companies: '', export_dir: '' });
  const [exportOpen, setExportOpen] = React.useState(false);
  const [exportFiles, setExportFiles] = React.useState([]);
  const [exportTitle, setExportTitle] = React.useState('Export Successful');
  const onPrep = async (name) => {
    try {
      const res = await fetch('/api/owners/prepentities', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name }) });
      const text = await res.text();
      let data = {};
      try { data = text ? JSON.parse(text) : {}; } catch (_) { data = {}; }
      if (!res.ok) {
        const msg = data && data.detail ? data.detail : (text || 'Prep failed');
        throw new Error(msg);
      }
      if ((data && data.status) !== 'ok') {
        const msg = (data && (data.error || data.detail)) || 'Prep failed';
        throw new Error(msg);
      }
      const files = [];
      if (data && data.export_path) files.push(data.export_path);
      setExportTitle(`Prep Successful${data && data.owner ? `: ${data.owner}` : ''}`);
      setExportFiles(files);
      setExportOpen(true);
    } catch (e) {
      alert(e.message || 'Prep failed');
    }
  };
  const onExportAll = async () => {
    try {
      const res = await fetch('/api/export-accounts', { method: 'POST' });
      const text = await res.text();
      let data = {};
      try { data = text ? JSON.parse(text) : {}; } catch (_) { data = {}; }
      if (!res.ok) {
        const msg = data && data.error ? data.error : (text || 'Export failed');
        throw new Error(msg);
      }
      if ((data && data.status) === 'error') {
        const msg = data.error || 'Export failed';
        alert(`Export failed: ${msg}`);
        return;
      }
      const files = [];
      if (Array.isArray(data && data.results)) {
        data.results.forEach(r => { if (r && r.path) files.push(r.path); });
      }
      setExportTitle('Export Successful: All Owners');
      setExportFiles(files);
      setExportOpen(true);
    } catch (e) {
      alert(e.message || 'Export failed');
    }
  };
  const onExport = async (name) => {
    try {
      const res = await fetch('/api/owners/export', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name }) });
      const text = await res.text();
      let data = {};
      try { data = text ? JSON.parse(text) : {}; } catch (_) { data = {}; }
      if (!res.ok) {
        const msg = data && data.error ? data.error : (text || 'Export failed');
        throw new Error(msg);
      }
      if ((data && data.status) === 'error') {
        const msg = data.error || 'Export failed';
        alert(`Export failed: ${msg}`);
        return;
      }
      const files = [];
      if (data && data.path) files.push(data.path);
      if (Array.isArray(data.results)) {
        data.results.forEach(r => { if (r && r.path) files.push(r.path); });
      }
      setExportTitle(`Export Successful${data && data.owner ? `: ${data.owner}` : ''}`);
      setExportFiles(files);
      setExportOpen(true);
    } catch (e) {
      alert(e.message || 'Export failed');
    }
  };
  return (
    <React.Fragment>
      <h2>Owners</h2>
      <Modal title={exportTitle} open={exportOpen} onClose={() => setExportOpen(false)} onSubmit={() => setExportOpen(false)} submitLabel="Close">
        <div>
          {(exportFiles || []).length === 0 ? (
            <div>No files created</div>
          ) : (
            <ul className="list-disc pl-5">
              {(exportFiles || []).map((p, idx) => (
                <li key={idx} className="break-words">{p}</li>
              ))}
            </ul>
          )}
        </div>
      </Modal>
      <div className="actions" style={{ marginBottom: 12 }}>
        <span className="mr-3 text-gray-600">Total: {owners.length}</span>
        <button type="button" onClick={() => { setForm(empty); setMode('add'); setOriginalKey(''); setOpen(true); }} className="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">Add owner</button>
        <button type="button" onClick={reload} disabled={loading} className="px-3 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 disabled:opacity-60">Refresh</button>
        <button type="button" onClick={onExportAll} className="px-3 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700">Export All</button>
      </div>
      <Modal title={mode==='edit' ? 'Edit Owner' : 'Add Owner'} open={open} onClose={() => { setOpen(false); setMode('add'); setOriginalKey(''); }} onSubmit={onSubmit} submitLabel={saving ? 'Saving...' : 'Save'} submitDisabled={!((form.name || '').trim()) || !((form.properties || []).length) || !((form.bankaccounts || []).length)}>
        <form onSubmit={onSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label className="block text-sm font-medium text-gray-700">name</label>
            <input
              name="name"
              value={form.name}
              onChange={onChange}
              placeholder="lowercase [a-z0-9_]"
              readOnly={mode === 'edit'}
              className={`mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500 ${mode === 'edit' ? 'bg-gray-100 text-gray-600 cursor-not-allowed' : ''}`}
            />
            <p className="text-xs text-gray-500 mt-1">Lowercase identifier</p>
          </div>
          <div>
            <MultiSelect
              label="bankaccounts"
              options={(bankaccounts || []).map(ba => ({ value: (ba.bankaccountname || '').toLowerCase(), label: ba.bankaccountname }))}
              selected={form.bankaccounts}
              onChange={(vals) => setForm({ ...form, bankaccounts: (vals || []).map(v => (v || '').toLowerCase()) })}
              placeholder="Select bank accounts..."
            />
          </div>
          <div>
            <MultiSelect
              label="properties"
              options={(items || []).map(p => ({ value: (p.property || '').toLowerCase(), label: p.property }))}
              selected={form.properties}
              onChange={(vals) => setForm({ ...form, properties: (vals || []).map(v => (v || '').toLowerCase()) })}
              placeholder="Select properties..."
            />
          </div>
          <div>
            <MultiSelect
              label="companies"
              options={(companies || []).map(c => ({ value: (c || '').toLowerCase(), label: c }))}
              selected={form.companies}
              onChange={(vals) => setForm({ ...form, companies: (vals || []).map(v => (v || '').toLowerCase()) })}
              placeholder="Select companies..."
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700">export_dir</label>
            <input
              name="export_dir"
              value={form.export_dir}
              onChange={onChange}
              placeholder="optional absolute/relative export directory"
              className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </form>
      </Modal>
      <div className="card">
        {loading ? (<div>Loading...</div>) : (
          <table>
            <thead>
              <tr>
                <th>name</th>
                <th>bankaccounts</th>
                <th>properties</th>
                <th>companies</th>
                <th>export_dir</th>
                <th></th>
              </tr>
              <tr>
                <th><input placeholder="filter" value={filter.name} onChange={(e)=> setFilter(f=>({...f, name: e.target.value }))} /></th>
                <th><input placeholder="filter" value={filter.bankaccounts} onChange={(e)=> setFilter(f=>({...f, bankaccounts: e.target.value }))} /></th>
                <th><input placeholder="filter" value={filter.properties} onChange={(e)=> setFilter(f=>({...f, properties: e.target.value }))} /></th>
                <th><input placeholder="filter" value={filter.companies} onChange={(e)=> setFilter(f=>({...f, companies: e.target.value }))} /></th>
                <th><input placeholder="filter" value={filter.export_dir} onChange={(e)=> setFilter(f=>({...f, export_dir: e.target.value }))} /></th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {owners
                .filter(x => {
                  const matchesText = (val, query) => { const s = (val||'').toString().toLowerCase(); const t = (query||'').toString().toLowerCase().trim(); if (!t) return true; const isNeg = t.startsWith('!'); const needle = isNeg ? t.slice(1) : t; if (!needle) return true; const has = s.includes(needle); return isNeg ? !has : has; };
                  return (
                    matchesText(x.name, filter.name) &&
                    matchesText((x.bankaccounts||[]).join(' '), filter.bankaccounts) &&
                    matchesText((x.properties||[]).join(' '), filter.properties) &&
                    matchesText((x.companies||[]).join(' '), filter.companies) &&
                    matchesText((x.export_dir||''), filter.export_dir)
                  );
                })
                .map(x => (
                <tr key={x.name}>
                  <td>{x.name}</td>
                  <td>{x.bankaccounts.join(' | ')}</td>
                  <td>{x.properties.join(' | ')}</td>
                  <td>{x.companies.join(' | ')}</td>
                  <td className="whitespace-pre-wrap">{x.export_dir}</td>
                  <td>
                    <button onClick={() => onEdit(x)} className="px-2 py-1 mr-2 bg-gray-700 text-white rounded hover:bg-gray-800">Edit</button>
                    <button onClick={() => onPrep(x.name)} className="px-2 py-1 mr-2 bg-green-600 text-white rounded hover:bg-green-700">Prep</button>
                    <button onClick={() => onExport(x.name)} className="px-2 py-1 mr-2 bg-indigo-600 text-white rounded hover:bg-indigo-700">Export</button>
                    <button onClick={() => onDelete(x.name)} className="px-2 py-1 bg-red-600 text-white rounded hover:bg-red-700">Delete</button>
                  </td>
                </tr>
              ))}
              {owners.length === 0 && (<tr><td colSpan="5" className="muted">No owners</td></tr>)}
            </tbody>
          </table>
        )}
      </div>
    </React.Fragment>
  );
};

window.OwnersPanelExt = OwnersPanelExt;
