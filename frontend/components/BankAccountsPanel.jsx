const BankAccountsPanelExt = ({ bankaccounts, loading, reload }) => {
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
        <button type="button" onClick={() => { setForm(empty); setMode('add'); setOriginalKey(''); setOpen(true); }}>Add bank account</button>
        <button type="button" onClick={reload} disabled={loading}>Refresh</button>
      </div>
      <Modal title={mode==='edit' ? 'Edit Bank Account' : 'Add Bank Account'} open={open} onClose={() => { setOpen(false); setMode('add'); setOriginalKey(''); }} onSubmit={onSubmit} submitLabel={saving ? 'Saving...' : 'Save'}>
        <div className="row" style={{display:'block'}}>
          <div className="col" style={{display:'flex', gap:8, alignItems:'center', marginBottom:8}}>
            <label style={{flex:1}}>bankaccountname<br/>
              <input name="bankaccountname" value={form.bankaccountname} onChange={onChange} placeholder="lowercase [a-z0-9_]" />
            </label>
            <span className="muted" style={{flex:1}}>Lowercase id</span>
          </div>
          <div className="col" style={{display:'flex', gap:8, alignItems:'center', marginBottom:8}}>
            <label style={{flex:1}}>bankname<br/>
              <input name="bankname" value={form.bankname} onChange={onChange} placeholder="bank name" />
            </label>
            <span className="muted" style={{flex:1}}>Bank provider</span>
          </div>
        </div>
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
                    <button onClick={() => onEdit(x)} style={{marginRight:8, background:'#374151'}}>Edit</button>
                    <button onClick={() => onDelete(x.bankaccountname)}>Delete</button>
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
