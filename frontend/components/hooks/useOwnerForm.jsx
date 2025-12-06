const { useState } = React;

// Hook encapsulating the OwnersPanelExt add/edit/delete owner behavior.
// Prep and export actions remain in the panel.
function useOwnerForm({ reload }) {
  const empty = { name: '', bankaccounts: [], properties: [], companies: [], export_dir: '' };
  const [form, setForm] = useState(empty);
  const [saving, setSaving] = useState(false);
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState('add');
  const [originalKey, setOriginalKey] = useState('');

  const onChange = (e) => {
    const { name, value, multiple, selectedOptions } = e.target;
    if (name === 'name') {
      setForm({ ...form, [name]: (value || '').toLowerCase().replace(/[^a-z0-9_]/g, '') });
    } else if (multiple) {
      const selected = Array.from(selectedOptions || []).map(o => (o.value || '').toLowerCase());
      setForm({ ...form, [name]: selected });
    } else {
      setForm({ ...form, [name]: value });
    }
  };

  const onSubmit = async (e) => {
    e.preventDefault(); setSaving(true);
    try {
      if (!form.name) throw new Error('name is required');
      const payload = {
        name: form.name,
        bankaccounts: Array.from(new Set((form.bankaccounts || []).map(s => (s || '').toLowerCase()))),
        properties: Array.from(new Set((form.properties || []).map(s => (s || '').toLowerCase()))),
        companies: Array.from(new Set((form.companies || []).map(s => (s || '').toLowerCase()))),
        export_dir: (form.export_dir || '').trim(),
      };
      if (mode === 'edit' && originalKey) {
        await window.api.removeOwner(originalKey);
      }
      await window.api.addOwner(payload);
      setForm(empty);
      setOriginalKey('');
      setMode('add');
      setOpen(false);
      await reload();
    } catch (e2) { alert(e2.message || 'Error'); } finally { setSaving(false); }
  };

  const onDelete = async (name) => {
    if (!(await window.showConfirm(`Delete ${name}?`))) return;
    try { await window.api.removeOwner(name); await reload(); }
    catch (e2) { alert(e2.message || 'Error'); }
  };

  const onEdit = (x) => {
    setMode('edit');
    setOriginalKey(x.name);
    const lc = (arr) => (arr || []).map(v => (v || '').toLowerCase());
    setForm({
      name: (x.name || '').toLowerCase(),
      bankaccounts: lc(x.bankaccounts),
      properties: lc(x.properties),
      companies: lc(x.companies),
      export_dir: (x.export_dir || ''),
    });
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

window.useOwnerForm = useOwnerForm;
