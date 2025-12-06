const BankAccountsPanelExt = ({ bankaccounts, loading, reload, banks }) => {
  const Modal = window.Modal;
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
  } = window.useBankAccountForm({ reload });
  const [filter, setFilter] = React.useState({ bankaccountname: '', bankname: '', statement_location: '' });
  const [uploadOpen, setUploadOpen] = React.useState(false);
  const [uploadTarget, setUploadTarget] = React.useState('');
  const [uploadFile, setUploadFile] = React.useState(null);
  const [uploadErr, setUploadErr] = React.useState('');
  const [uploading, setUploading] = React.useState(false);
  const onOpenUpload = (baName) => {
    setUploadTarget(baName);
    setUploadFile(null);
    setUploadErr('');
    setUploadOpen(true);
  };
  const onSubmitUpload = async (e) => {
    e && e.preventDefault();
    try {
      setUploadErr('');
      if (!uploadTarget) throw new Error('Missing bankaccountname');
      if (!uploadFile) throw new Error('Please choose a .csv file');
      const name = uploadFile.name || '';
      if (!name.toLowerCase().endsWith('.csv')) throw new Error('Only .csv files are supported');
      const fd = new FormData();
      fd.append('file', uploadFile);
      setUploading(true);
      const resp = await fetch(`/api/bankaccounts/${encodeURIComponent(uploadTarget)}/upload-statement`, { method: 'POST', body: fd });
      if (!resp.ok) {
        const t = await resp.text().catch(()=> '');
        throw new Error(t || 'Upload failed');
      }
      setUploadOpen(false);
      await reload();
    } catch (err) {
      setUploadErr(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };
  return (
    <React.Fragment>
      <h2>Bank Accounts</h2>
      <div className="actions" style={{ marginBottom: 12 }}>
        <span className="mr-3 text-gray-600">Total: {bankaccounts.length}</span>
        <button type="button" onClick={() => { setForm(empty); setMode('add'); setOriginalKey(''); setOpen(true); }} className="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">Add bank account</button>
        <button type="button" onClick={reload} disabled={loading} className="px-3 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 disabled:opacity-60">Refresh</button>
      </div>
      <Modal title={mode==='edit' ? 'Edit Bank Account' : 'Add Bank Account'} open={open} onClose={() => { setOpen(false); setMode('add'); setOriginalKey(''); }} onSubmit={onSubmit} submitLabel={saving ? 'Saving...' : 'Save'} submitDisabled={!(((form.bankaccountname||'').trim()) && ((form.bankname||'').trim()) && ((form.statement_location||'').trim()))}>
        <form onSubmit={onSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label className="block text-sm font-medium text-gray-700">bankaccountname</label>
            <input
              name="bankaccountname"
              value={form.bankaccountname}
              onChange={onChange}
              placeholder="lowercase [a-z0-9_]"
              required
              readOnly={mode === 'edit'}
              className={`mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500 ${mode === 'edit' ? 'bg-gray-100 text-gray-600 cursor-not-allowed' : ''}`}
            />
            <p className="text-xs text-gray-500 mt-1">Lowercase id</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">bankname</label>
            <select name="bankname" value={form.bankname} onChange={onChange} className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500">
              <option value="">Select bank</option>
              {(banks || []).map(b => (
                <option key={b.name} value={(b.name || '').toLowerCase()}>{b.name}</option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-1">Bank provider</p>
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700">statement_location</label>
            <input name="statement_location" value={form.statement_location} onChange={onChange} placeholder="e.g., /path/or/url" className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500" />
            <p className="text-xs text-gray-500 mt-1">Optional path or URL to statements 20XX/bank_stmts will be appended</p>
          </div>
          
        </form>
      </Modal>
      <div className="card">
        {loading ? (<div>Loading...</div>) : (
          <table>
            <thead>
              <tr>
                <th>bankaccountname</th>
                <th>bankname</th>
                <th>statement_location</th>
                <th></th>
              </tr>
              <tr>
                <th>
                  <input placeholder="filter" value={filter.bankaccountname} onChange={(e)=> setFilter(f=>({...f, bankaccountname: e.target.value }))} />
                </th>
                <th>
                  <input placeholder="filter" value={filter.bankname} onChange={(e)=> setFilter(f=>({...f, bankname: e.target.value }))} />
                </th>
                <th>
                  <input placeholder="filter" value={filter.statement_location} onChange={(e)=> setFilter(f=>({...f, statement_location: e.target.value }))} />
                </th>
                
                <th></th>
              </tr>
            </thead>
            <tbody>
              {bankaccounts
                .slice()
                .sort((a, b) => {
                  const an = (a.bankaccountname || '').toLowerCase();
                  const bn = (b.bankaccountname || '').toLowerCase();
                  if (an < bn) return -1; if (an > bn) return 1; return 0;
                })
                .filter(x => {
                  const matchesText = (val, query) => { const s = (val||'').toString().toLowerCase(); const t = (query||'').toString().toLowerCase().trim(); if (!t) return true; const isNeg = t.startsWith('!'); const needle = isNeg ? t.slice(1) : t; if (!needle) return true; const has = s.includes(needle); return isNeg ? !has : has; };
                  return (
                    matchesText(x.bankaccountname, filter.bankaccountname) &&
                    matchesText(x.bankname, filter.bankname) &&
                    matchesText(String(x.statement_location||''), filter.statement_location)
                  );
                })
                .map(x => (
                <tr key={x.bankaccountname}>
                  <td>{x.bankaccountname}</td>
                  <td>{x.bankname}</td>
                  <td className="whitespace-pre-wrap">{x.statement_location}</td>
                  <td>
                    <button onClick={() => onOpenUpload(x.bankaccountname)} className="px-2 py-1 mr-2 bg-blue-600 text-white rounded hover:bg-blue-700">Upload Statement</button>
                    <button onClick={() => onEdit(x)} className="px-2 py-1 mr-2 bg-gray-700 text-white rounded hover:bg-gray-800">Edit</button>
                    <button onClick={() => onDelete(x.bankaccountname)} className="px-2 py-1 bg-red-600 text-white rounded hover:bg-red-700">Delete</button>
                  </td>
                </tr>
              ))}
              {bankaccounts.length === 0 && (<tr><td colSpan="3" className="muted">No bank accounts</td></tr>)}
            </tbody>
          </table>
        )}
      </div>
      <Modal
        title={`Upload Statement${uploadTarget ? `: ${uploadTarget}` : ''}`}
        open={uploadOpen}
        onClose={() => setUploadOpen(false)}
        onSubmit={onSubmitUpload}
        submitLabel={uploading ? 'Uploading...' : 'Upload'}
        submitDisabled={uploading || !uploadFile}
      >
        <form onSubmit={onSubmitUpload} className="grid grid-cols-1 gap-4">
          <p className="text-sm text-gray-600">
            Upload backstatement for bankaccountname starting from Jan 1st till current date  or Dec 31
          </p>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">File (.csv)</label>
            <input type="file" accept=".csv" onChange={(e)=> setUploadFile(e.target.files && e.target.files[0] ? e.target.files[0] : null)} />
          </div>
          {uploadErr && <div className="text-sm text-red-600">{uploadErr}</div>}
        </form>
      </Modal>
    </React.Fragment>
  );
};

window.BankAccountsPanelExt = BankAccountsPanelExt;
