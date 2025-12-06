const TransactionTypesPanelExt = ({ transactionTypes, loading, reload }) => {
  const Modal = window.Modal;
  const {
    empty,
    form,
    setForm,
    saving,
    error,
    setError,
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
  } = window.useTransactionTypeForm({ reload });
  const [filter, setFilter] = React.useState({ transactiontype: '' });
  const onRename = async (oldName) => {
    try {
      const input = window.prompt('New transaction type name (lowercase, a-z0-9_)', oldName);
      if (input == null) return;
      const to = (input || '').trim().toLowerCase();
      if (!to) { alert('Name is required'); return; }
      if (!/^[a-z0-9_]+$/.test(to)) { alert('Use lowercase letters, numbers, and underscore only (no spaces)'); return; }
      if (to === oldName) return;
      const res = await fetch('/api/transaction-types/rename', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ from_type: oldName, to_type: to })
      });
      if (!res.ok) { const t = await res.text().catch(()=> ''); throw new Error(t || 'Rename failed'); }
      await reload();
    } catch (err) {
      alert(err.message || 'Rename failed');
    }
  };
  return (
    <React.Fragment>
      <h2>Transaction Types</h2>
      <div className="actions" style={{ marginBottom: 12 }}>
        <span className="mr-3 text-gray-600">Total: {transactionTypes.length}</span>
        <button type="button" onClick={() => { setForm({ transactiontype: '' }); setMode('add'); setOriginalKey(''); setOpen(true); }} className="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">Add type</button>
        <button type="button" onClick={reload} disabled={loading} className="px-3 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 disabled:opacity-60">Refresh</button>
      </div>
      <Modal title={mode==='edit' ? 'Edit Transaction Type' : 'Add Transaction Type'} open={open} onClose={() => { setOpen(false); setMode('add'); setOriginalKey(''); }} onSubmit={onSubmit} submitLabel={saving ? 'Saving...' : 'Save'} submitDisabled={!((form.transactiontype || '').trim())}>
        <form onSubmit={onSubmit} className="grid grid-cols-1 gap-5">
          <div>
            <label className="block text-sm font-medium text-gray-700">transactiontype</label>
            <input name="transactiontype" value={form.transactiontype} onChange={onChange} placeholder="lowercase [a-z0-9_]" required className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500" />
            <p className="text-xs text-gray-500 mt-1">Lowercase identifier</p>
          </div>
          {error && <div className="text-red-600 mt-2">{error}</div>}
        </form>
      </Modal>
      <div className="card">
        {loading ? (<div>Loading...</div>) : (
          <table>
            <thead>
              <tr>
                <th>transactiontype</th>
                <th></th>
              </tr>
              <tr>
                <th><input placeholder="filter" value={filter.transactiontype} onChange={(e)=> setFilter({ transactiontype: e.target.value })} /></th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {transactionTypes
                .slice()
                .sort((a, b) => {
                  const at = (a.transactiontype || '').toLowerCase();
                  const bt = (b.transactiontype || '').toLowerCase();
                  if (at < bt) return -1; if (at > bt) return 1; return 0;
                })
                .filter(t => {
                  const matchesText = (val, query) => { const s = (val||'').toString().toLowerCase(); const t0 = (query||'').toString().toLowerCase().trim(); if (!t0) return true; const isNeg = t0.startsWith('!'); const needle = isNeg ? t0.slice(1) : t0; if (!needle) return true; const has = s.includes(needle); return isNeg ? !has : has; };
                  return matchesText(t.transactiontype, filter.transactiontype);
                })
                .map(t => (
                <tr key={t.transactiontype}>
                  <td>{t.transactiontype}</td>
                  <td>
                    <button onClick={() => onRename(t.transactiontype)} className="px-2 py-1 mr-2 bg-blue-600 text-white rounded hover:bg-blue-700">Rename</button>
                    <button onClick={() => onDelete(t.transactiontype)} className="px-2 py-1 bg-red-600 text-white rounded hover:bg-red-700">Delete</button>
                  </td>
                </tr>
              ))}
              {transactionTypes.length === 0 && (<tr><td colSpan="2" className="muted">No transaction types</td></tr>)}
            </tbody>
          </table>
        )}
      </div>
    </React.Fragment>
  );
};

window.TransactionTypesPanelExt = TransactionTypesPanelExt;
