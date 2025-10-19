const BanksPanelExt = ({ banks, loading, reload }) => {
  const [form, setForm] = React.useState({
    name: '',
    date_format: 'M/d/yyyy',
    delim: '',
    ignore_lines_contains: '',
    ignore_lines_startswith: '',
    col_checkno: '',
    col_credit: '',
    col_date: '',
    col_debit: '',
    col_description: '',
    col_fees: '',
    col_memo: '',
  });
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState('');
  const [open, setOpen] = React.useState(false);
  const Modal = window.Modal;
  const [mode, setMode] = React.useState('add');
  const [originalKey, setOriginalKey] = React.useState('');
  const [filter, setFilter] = React.useState({ name:'', date_format:'', delim:'', ignore_lines_contains:'', ignore_lines_startswith:'', columns:'' });
  const onChange = (e) => {
    const { name, value } = e.target;
    if (name.startsWith('col_')) {
      const v = value === '' ? '' : String(parseInt(value, 10) || '');
      setForm(prev => ({ ...prev, [name]: v }));
    } else {
      setForm(prev => ({ ...prev, [name]: value }));
    }
  };
  const onEdit = (b) => {
    setMode('edit');
    setOriginalKey(b.name);
    const colObj = Array.isArray(b.columns) && b.columns.length > 0 ? b.columns[0] || {} : (b.columns || {});
    setForm({
      name: b.name,
      date_format: b.date_format || '',
      delim: b.delim || '',
      ignore_lines_contains: (b.ignore_lines_contains || []).join('\n'),
      ignore_lines_startswith: (b.ignore_lines_startswith || []).join('\n'),
      col_checkno: colObj.checkno != null ? String(colObj.checkno) : '',
      col_credit: colObj.credit != null ? String(colObj.credit) : '',
      col_date: colObj.date != null ? String(colObj.date) : '',
      col_debit: colObj.debit != null ? String(colObj.debit) : '',
      col_description: colObj.description != null ? String(colObj.description) : '',
      col_fees: colObj.fees != null ? String(colObj.fees) : '',
      col_memo: colObj.memo != null ? String(colObj.memo) : '',
    });
    setOpen(true);
  };
  const onSubmit = async (e) => {
    e.preventDefault(); setSaving(true); setError('');
    try {
      const name = (form.name || '').trim().toLowerCase();
      if (!name) throw new Error('name is required');
      const ignore_lines_contains = (form.ignore_lines_contains || '').split(/\r?\n/).map(s=>s.trim()).filter(Boolean);
      const ignore_lines_startswith = (form.ignore_lines_startswith || '').split(/\r?\n/).map(s=>s.trim()).filter(Boolean);
      // required column mappings
      if (form.col_date === '' || Number.isNaN(parseInt(form.col_date, 10))) throw new Error('date column is required');
      if (form.col_debit === '' || Number.isNaN(parseInt(form.col_debit, 10))) throw new Error('debit column is required');
      if (form.col_description === '' || Number.isNaN(parseInt(form.col_description, 10))) throw new Error('description column is required');
      const colMap = {};
      const addIfNum = (key, val) => {
        if (val !== '' && !Number.isNaN(parseInt(val, 10))) colMap[key] = parseInt(val, 10);
      };
      addIfNum('checkno', form.col_checkno);
      addIfNum('credit', form.col_credit);
      addIfNum('date', form.col_date);
      addIfNum('debit', form.col_debit);
      addIfNum('description', form.col_description);
      addIfNum('fees', form.col_fees);
      addIfNum('memo', form.col_memo);
      const columns = Object.keys(colMap).length ? [colMap] : [];
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
      setForm({ name: '', date_format: 'M/d/yyyy', delim: '', ignore_lines_contains: '', ignore_lines_startswith: '', col_checkno: '', col_credit: '', col_date: '', col_debit: '', col_description: '', col_fees: '', col_memo: '' });
      setOriginalKey('');
      setMode('add');
      setOpen(false);
      await reload();
    } catch (err) { setError(err.message || 'Error'); } finally { setSaving(false); }
  };
  const onDelete = async (name) => {
    if (!(await window.showConfirm(`Delete ${name}?`))) return;
    try { await window.api.removeBank(name); await reload(); } catch (err) { alert(err.message || 'Error'); }
  };
  return (
    <React.Fragment>
      <h2>Banks</h2>
      <div className="actions" style={{ marginBottom: 12 }}>
        <button type="button" onClick={() => { setForm({ name: '', date_format: 'M/d/yyyy', delim: '', ignore_lines_contains: '', ignore_lines_startswith: '', col_checkno: '', col_credit: '', col_date: '', col_debit: '', col_description: '', col_fees: '', col_memo: '' }); setMode('add'); setOriginalKey(''); setOpen(true); }} className="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">Add bank</button>
        <button type="button" onClick={reload} disabled={loading} className="px-3 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 disabled:opacity-60">Refresh</button>
      </div>
      <Modal title={mode==='edit' ? 'Edit Bank' : 'Add Bank'} open={open} onClose={() => { setOpen(false); setMode('add'); setOriginalKey(''); }} onSubmit={onSubmit} submitLabel={saving ? 'Saving...' : 'Save'} submitDisabled={!((form.name || '').trim()) || !((form.date_format || '').trim())}>
        <form onSubmit={onSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label className="block text-sm font-medium text-gray-700">name</label>
            <input
              name="name"
              value={form.name}
              onChange={onChange}
              placeholder="lowercase id [a-z0-9_]"
              required
              readOnly={mode === 'edit'}
              className={`mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500 ${mode === 'edit' ? 'bg-gray-100 text-gray-600 cursor-not-allowed' : ''}`}
            />
            <p className="text-xs text-gray-500 mt-1">Unique lowercase id</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">date_format</label>
            <input name="date_format" value={form.date_format} onChange={onChange} placeholder="%m/%d/%Y" required className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500" />
            <p className="text-xs text-gray-500 mt-1">Python strptime format</p>
          </div>
          <div className="md:col-span-2 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">date<span className="text-red-600">*</span></label>
              <input name="col_date" type="number" value={form.col_date} onChange={onChange} placeholder="2" required className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">debit<span className="text-red-600">*</span></label>
              <input name="col_debit" type="number" value={form.col_debit} onChange={onChange} placeholder="5" required className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">description<span className="text-red-600">*</span></label>
              <input name="col_description" type="number" value={form.col_description} onChange={onChange} placeholder="3" required className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500" />
            </div>
          </div>
          <div className="md:col-span-2 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">checkno</label>
              <input name="col_checkno" type="number" value={form.col_checkno} onChange={onChange} placeholder="8" className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">credit</label>
              <input name="col_credit" type="number" value={form.col_credit} onChange={onChange} placeholder="6" className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">fees</label>
              <input name="col_fees" type="number" value={form.col_fees} onChange={onChange} placeholder="9" className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">memo</label>
              <input name="col_memo" type="number" value={form.col_memo} onChange={onChange} placeholder="4" className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">delim</label>
            <input name="delim" value={form.delim} onChange={onChange} placeholder="," className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500" />
            <p className="text-xs text-gray-500 mt-1">CSV delimiter</p>
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700">ignore_lines_contains (one per line)</label>
            <textarea name="ignore_lines_contains" value={form.ignore_lines_contains} onChange={onChange} rows="4" placeholder={'foo\nbar'} className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500" />
            <p className="text-xs text-gray-500 mt-1">One filter per line</p>
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700">ignore_lines_startswith (one per line)</label>
            <textarea name="ignore_lines_startswith" value={form.ignore_lines_startswith} onChange={onChange} rows="4" placeholder={'Header\nTotal'} className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500" />
            <p className="text-xs text-gray-500 mt-1">One prefix per line</p>
          </div>
          {error && <div className="md:col-span-2 text-red-600 mt-2">{error}</div>}
        </form>
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
              <tr>
                <th><input placeholder="filter" value={filter.name} onChange={(e)=> setFilter(f=>({...f, name: e.target.value }))} /></th>
                <th><input placeholder="filter" value={filter.date_format} onChange={(e)=> setFilter(f=>({...f, date_format: e.target.value }))} /></th>
                <th><input placeholder="filter" value={filter.delim} onChange={(e)=> setFilter(f=>({...f, delim: e.target.value }))} /></th>
                <th><input placeholder="filter" value={filter.ignore_lines_contains} onChange={(e)=> setFilter(f=>({...f, ignore_lines_contains: e.target.value }))} /></th>
                <th><input placeholder="filter" value={filter.ignore_lines_startswith} onChange={(e)=> setFilter(f=>({...f, ignore_lines_startswith: e.target.value }))} /></th>
                <th><input placeholder="filter" value={filter.columns} onChange={(e)=> setFilter(f=>({...f, columns: e.target.value }))} /></th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {banks
                .filter(b => {
                  const ilc = (b.ignore_lines_contains || []).join(' ').toLowerCase();
                  const ils = (b.ignore_lines_startswith || []).join(' ').toLowerCase();
                  const cols = JSON.stringify(b.columns || []).toLowerCase();
                  return (
                    (filter.name ? (b.name||'').toLowerCase().includes(filter.name.toLowerCase()) : true) &&
                    (filter.date_format ? (b.date_format||'').toLowerCase().includes(filter.date_format.toLowerCase()) : true) &&
                    (filter.delim ? (b.delim||'').toLowerCase().includes(filter.delim.toLowerCase()) : true) &&
                    (filter.ignore_lines_contains ? ilc.includes(filter.ignore_lines_contains.toLowerCase()) : true) &&
                    (filter.ignore_lines_startswith ? ils.includes(filter.ignore_lines_startswith.toLowerCase()) : true) &&
                    (filter.columns ? cols.includes(filter.columns.toLowerCase()) : true)
                  );
                })
                .map(b => (
                <tr key={b.name}>
                  <td>{b.name}</td>
                  <td>{b.date_format}</td>
                  <td>{b.delim}</td>
                  <td>{(b.ignore_lines_contains || []).join(' | ')}</td>
                  <td>{(b.ignore_lines_startswith || []).join(' | ')}</td>
                  <td><pre style={{margin:0, whiteSpace:'pre-wrap'}}>{JSON.stringify(b.columns || [], null, 2)}</pre></td>
                  <td>
                    <button onClick={() => onEdit(b)} className="px-2 py-1 mr-2 bg-gray-700 text-white rounded hover:bg-gray-800">Edit</button>
                    <button onClick={() => onDelete(b.name)} className="px-2 py-1 bg-red-600 text-white rounded hover:bg-red-700">Delete</button>
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
