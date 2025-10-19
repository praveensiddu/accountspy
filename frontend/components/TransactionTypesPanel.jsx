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
        <button type="button" onClick={() => setOpen(true)}>Add type</button>
        <button type="button" onClick={reload} disabled={loading}>Refresh</button>
      </div>
      <Modal title={mode==='edit' ? 'Edit Transaction Type' : 'Add Transaction Type'} open={open} onClose={() => { setOpen(false); setMode('add'); setOriginalKey(''); }} onSubmit={onSubmit} submitLabel={saving ? 'Saving...' : 'Save'}>
        <div className="row" style={{display:'block'}}>
          <div className="col" style={{display:'flex', gap:8, alignItems:'center', marginBottom:8}}>
            <label style={{flex:1}}>transactiontype<br/>
              <input name="transactiontype" value={form.transactiontype} onChange={onChange} placeholder="lowercase [a-z0-9_]" />
            </label>
            <span className="muted" style={{flex:1}}>Lowercase identifier</span>
          </div>
          {error && <div className="error" style={{ marginTop: 8 }}>{error}</div>}
        </div>
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
                    <button onClick={() => onEdit(t)} style={{marginRight:8, background:'#374151'}}>Edit</button>
                    <button onClick={() => onDelete(t.transactiontype)}>Delete</button>
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
