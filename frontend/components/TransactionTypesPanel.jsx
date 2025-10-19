const TransactionTypesPanelExt = ({ transactionTypes, loading, reload }) => {
  const [form, setForm] = React.useState({ transactiontype: '' });
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState('');
  const onChange = (e) => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: name === 'transactiontype' ? (value || '').trim().toLowerCase() : value }));
  };
  const onSubmit = async (e) => {
    e.preventDefault(); setSaving(true); setError('');
    try {
      const transactiontype = (form.transactiontype || '').trim().toLowerCase();
      if (!transactiontype) throw new Error('transactiontype is required');
      await window.api.addTransactionType({ transactiontype });
      setForm({ transactiontype: '' });
      await reload();
    } catch (err) { setError(err.message || 'Error'); } finally { setSaving(false); }
  };
  const onDelete = async (tt) => {
    if (!confirm(`Delete ${tt}?`)) return;
    try { await window.api.removeTransactionType(tt); await reload(); } catch (err) { alert(err.message || 'Error'); }
  };
  return (
    <React.Fragment>
      <h2>Transaction Types</h2>
      <div className="card">
        <form onSubmit={onSubmit}>
          <div className="row">
            <div className="col"><label>transactiontype<br/>
              <input name="transactiontype" value={form.transactiontype} onChange={onChange} placeholder="lowercase [a-z0-9_]" />
            </label></div>
          </div>
          <div className="actions" style={{ marginTop: 12 }}>
            <button type="submit" disabled={saving}>Add type</button>
            <button type="button" onClick={reload} disabled={loading}>Refresh</button>
          </div>
          {error && <div className="error" style={{ marginTop: 8 }}>{error}</div>}
        </form>
      </div>
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
                  <td><button onClick={() => onDelete(t.transactiontype)}>Delete</button></td>
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
