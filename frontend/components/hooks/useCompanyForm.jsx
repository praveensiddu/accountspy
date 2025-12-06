const { useState } = React;

// Hook encapsulating the full CompaniesPanelExt behavior, including
// add/edit modes, originalKey tracking, modal open state, and error handling.
function useCompanyForm({ reload }) {
  const empty = { companyname: '', rentPercentage: 0 };
  const [form, setForm] = useState(empty);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState('add');
  const [originalKey, setOriginalKey] = useState('');

  const onChange = (e) => {
    const { name, value } = e.target;
    if (name === 'rentPercentage') setForm({ ...form, [name]: Number(value || 0) });
    else if (name === 'companyname') setForm({ ...form, [name]: (value || '').toLowerCase().replace(/[^a-z0-9]/g, '') });
    else setForm({ ...form, [name]: value });
  };

  const onSubmit = async (e) => {
    e.preventDefault(); setSaving(true); setError('');
    try {
      if (!form.companyname) throw new Error('companyname is required');
      const payload = { ...form, companyname: form.companyname.trim().toLowerCase() };
      if (mode === 'edit' && originalKey) {
        await window.api.removeCompanyRecord(originalKey);
      }
      await window.api.addCompanyRecord(payload);
      setForm(empty);
      setOriginalKey('');
      setMode('add');
      setOpen(false);
      await reload();
    } catch (e2) { setError(e2.message || 'Error'); } finally { setSaving(false); }
  };

  const onDelete = async (name) => {
    if (!(await window.showConfirm(`Delete ${name}?`))) return;
    try { await window.api.removeCompanyRecord(name); await reload(); } catch (e2) { alert(e2.message || 'Error'); }
  };

  const onEdit = (x) => {
    setMode('edit');
    setOriginalKey(x.companyname);
    setForm({ companyname: x.companyname, rentPercentage: x.rentPercentage });
    setOpen(true);
  };

  return {
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
  };
}

window.useCompanyForm = useCompanyForm;
