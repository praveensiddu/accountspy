const { useState } = React;

// Hook for TransactionTypesPanelExt add/edit/delete behavior (rename stays in panel)
function useTransactionTypeForm({ reload }) {
  const empty = { transactiontype: '' };
  const [form, setForm] = useState(empty);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState('add');
  const [originalKey, setOriginalKey] = useState('');

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
      setForm(empty);
      setOriginalKey('');
      setMode('add');
      setOpen(false);
      await reload();
    } catch (err) { setError(err.message || 'Error'); } finally { setSaving(false); }
  };

  const onDelete = async (tt) => {
    if (!(await window.showConfirm(`Delete ${tt}?`))) return;
    try { await window.api.removeTransactionType(tt); await reload(); } catch (err) { alert(err.message || 'Error'); }
  };

  const onEdit = (t) => {
    setMode('edit');
    setOriginalKey(t.transactiontype);
    setForm({ transactiontype: t.transactiontype });
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

window.useTransactionTypeForm = useTransactionTypeForm;
