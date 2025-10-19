const BankAccountsPanelExt = ({ bankaccounts, loading, reload, banks }) => {
  const Modal = window.Modal;
  const empty = { bankaccountname: '', bankname: '' };
  const [form, setForm] = React.useState(empty);
  const [saving, setSaving] = React.useState(false);
  const [open, setOpen] = React.useState(false);
  const [mode, setMode] = React.useState('add');
  const [originalKey, setOriginalKey] = React.useState('');
  const onChange = (e) => {
    const { name, value } = e.target;
    if (name === 'bankaccountname') setForm({ ...form, [name]: (value || '').toLowerCase().replace(/[^a-z0-9_]/g, '') });
    else if (name === 'bankname') setForm({ ...form, [name]: (value || '').toLowerCase() });
  };
  const onSubmit = async (e) => {
    e.preventDefault(); setSaving(true);
    try {
      if (!form.bankaccountname || !form.bankname) throw new Error('bankaccountname and bankname are required');
      if (mode === 'edit' && originalKey) {
        await window.api.removeBankaccount(originalKey);
      }
      await window.api.addBankaccount(form);
      setForm(empty);
      setOriginalKey('');
      setMode('add');
      setOpen(false);
      await reload();
    } catch (e) { alert(e.message || 'Error'); } finally { setSaving(false); }
  };
  const onDelete = async (name) => {
    if (!confirm(`Delete ${name}?`)) return;
    try { await window.api.removeBankaccount(name); await reload(); } catch (e) { alert(e.message || 'Error'); }
  };
  const onEdit = (x) => {
    setMode('edit');
    setOriginalKey(x.bankaccountname);
    setForm({ bankaccountname: x.bankaccountname, bankname: x.bankname });
    setOpen(true);
  };
  return (
    <React.Fragment>
      <h2>Bank Accounts</h2>
      <div className="actions" style={{ marginBottom: 12 }}>
        <button type="button" onClick={() => { setForm(empty); setMode('add'); setOriginalKey(''); setOpen(true); }} className="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">Add bank account</button>
        <button type="button" onClick={reload} disabled={loading} className="px-3 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 disabled:opacity-60">Refresh</button>
      </div>
      <Modal title={mode==='edit' ? 'Edit Bank Account' : 'Add Bank Account'} open={open} onClose={() => { setOpen(false); setMode('add'); setOriginalKey(''); }} onSubmit={onSubmit} submitLabel={saving ? 'Saving...' : 'Save'}>
        <form onSubmit={onSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label className="block text-sm font-medium text-gray-700">bankaccountname</label>
            <input name="bankaccountname" value={form.bankaccountname} onChange={onChange} placeholder="lowercase [a-z0-9_]" className="mt-1 w-full border border-gray-300 rounded-md p-2 shadow-sm focus:ring-blue-500 focus:border-blue-500" />
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
        </form>
      </Modal>
      <div className="card">
        {loading ? (<div>Loading...</div>) : (
          <table>
            <thead>
              <tr>
                <th>bankaccountname</th>
                <th>bankname</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {bankaccounts.map(x => (
                <tr key={x.bankaccountname}>
                  <td>{x.bankaccountname}</td>
                  <td>{x.bankname}</td>
                  <td>
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
    </React.Fragment>
  );
};

window.BankAccountsPanelExt = BankAccountsPanelExt;
