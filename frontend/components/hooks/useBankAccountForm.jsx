const { useState } = React;

// Hook encapsulating the BankAccountsPanelExt add/edit/delete behavior
// (upload logic stays in the panel). Uses window.api and reload().
function useBankAccountForm({ reload }) {
  const empty = { bankaccountname: '', bankname: '', statement_location: '' };
  const [form, setForm] = useState(empty);
  const [saving, setSaving] = useState(false);
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState('add');
  const [originalKey, setOriginalKey] = useState('');

  const onChange = (e) => {
    const { name, value } = e.target;
    if (name === 'bankaccountname') setForm({ ...form, [name]: (value || '').toLowerCase().replace(/[^a-z0-9_]/g, '') });
    else if (name === 'bankname') setForm({ ...form, [name]: (value || '').toLowerCase() });
    else if (name === 'statement_location') setForm({ ...form, [name]: value });
  };

  const onSubmit = async (e) => {
    e.preventDefault(); setSaving(true);
    try {
      if (!form.bankaccountname || !form.bankname) throw new Error('bankaccountname and bankname are required');
      if (mode === 'edit' && originalKey) {
        await window.api.updateBankaccount(originalKey, form);
      } else {
        await window.api.addBankaccount(form);
      }
      setForm(empty);
      setOriginalKey('');
      setMode('add');
      setOpen(false);
      await reload();
    } catch (e2) { alert(e2.message || 'Error'); } finally { setSaving(false); }
  };

  const onDelete = async (name) => {
    if (!(await window.showConfirm(`Delete ${name}?`))) return;
    try { await window.api.removeBankaccount(name); await reload(); }
    catch (e2) { alert(e2.message || 'Error'); }
  };

  const onEdit = (x) => {
    setMode('edit');
    setOriginalKey(x.bankaccountname);
    setForm({ bankaccountname: x.bankaccountname, bankname: x.bankname, statement_location: x.statement_location || '' });
    setOpen(true);
  };

  return {
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
  };
}

window.useBankAccountForm = useBankAccountForm;
