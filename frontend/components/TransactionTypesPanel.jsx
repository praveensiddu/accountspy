const TransactionTypesPanelExt = ({ transactionTypes, loading, reload }) => {
  const Modal = window.Modal;
  const [form, setForm] = React.useState({ transactiontype: '' });
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState('');
  const [open, setOpen] = React.useState(false);
  const [mode, setMode] = React.useState('add');
  const [originalKey, setOriginalKey] = React.useState('');
  const onChange = (e) => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: name === 'transactiontype' ? (value || '').trim().toLowerCase() : value }));
  };
  const onSubmit = async (e) => {
    e.preventDefault(); setSaving(true); setError('');
    try {
      const transactiontype = (form.transactiontype || '').trim().toLowerCase();
      if (!transactiontype) throw new Error('transactiontype is required');
      if (mode === 'edit' && originalKey) {
        await window.api.removeTransactionType(originalKey);
      }
      await window.api.addTransactionType({ transactiontype });
      setForm({ transactiontype: '' });
      setOriginalKey('');
      setMode('add');
      setOpen(false);
      await reload();
    } catch (err) { setError(err.message || 'Error'); } finally { setSaving(false); }
  };
  const onDelete = async (tt) => {
    if (!confirm(`Delete ${tt}?`)) return;
    try { await window.api.removeTransactionType(tt); await reload(); } catch (err) { alert(err.message || 'Error'); }
  };
  const onEdit = (t) => {
    setMode('edit');
    setOriginalKey(t.transactiontype);
    setForm({ transactiontype: t.transactiontype });
    setOpen(true);
  };
  return (
    <React.Fragment>
      <h2>Transaction Types</h2>
      <div className="actions" style={{ marginBottom: 12 }}>
        <button type="button" onClick={() => { setForm({ transactiontype: '' }); setMode('add'); setOriginalKey(''); setOpen(true); }} className="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">Add type</button>
        <button type="button" onClick={reload} disabled={loading} className="px-3 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 disabled:opacity-60">Refresh</button>
      </div>
      <Modal title={mode==='edit' ? 'Edit Transaction Type' : 'Add Transaction Type'} open={open} onClose={() => { setOpen(false); setMode('add'); setOriginalKey(''); }} onSubmit={onSubmit} submitLabel={saving ? 'Saving...' : 'Save'}>
        <form onSubmit={onSubmit} className="grid grid-cols-1 gap-5">
          <div>
            <label className="block text-sm font-medium text-gray-700">transactiontype</label>
            <input name="transactiontype" value={form.transactiontype} onChange={onChange} placeholder="lowercase [a-z0-9_]" className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500" />
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
            </thead>
            <tbody>
              {transactionTypes.map(t => (
                <tr key={t.transactiontype}>
                  <td>{t.transactiontype}</td>
                  <td>
                    <button onClick={() => onEdit(t)} className="px-2 py-1 mr-2 bg-gray-700 text-white rounded hover:bg-gray-800">Edit</button>
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
