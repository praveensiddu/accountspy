const { useState } = React;

// Hook for BanksPanelExt add/edit/delete behavior
function useBankForm({ reload }) {
  const empty = {
    name: '',
    date_format: 'M/d/yyyy',
    delim: '',
    ignore_lines_contains: '',
    ignore_lines_startswith: '',
    col_checkno: '',
    col_credit: '',
    col_date: '',
    col_debit: '',
    col_description: '',
    col_fees: '',
    col_memo: '',
  };
  const [form, setForm] = useState(empty);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState('add');
  const [originalKey, setOriginalKey] = useState('');

  const onChange = (e) => {
    const { name, value } = e.target;
    if (name.startsWith('col_')) {
      const v = value === '' ? '' : String(parseInt(value, 10) || '');
      setForm(prev => ({ ...prev, [name]: v }));
    } else {
      setForm(prev => ({ ...prev, [name]: value }));
    }
  };

  const onEdit = (b) => {
    setMode('edit');
    setOriginalKey(b.name);
    const colObj = Array.isArray(b.columns) && b.columns.length > 0 ? b.columns[0] || {} : (b.columns || {});
    setForm({
      name: b.name,
      date_format: b.date_format || '',
      delim: b.delim || '',
      ignore_lines_contains: (b.ignore_lines_contains || []).join('\n'),
      ignore_lines_startswith: (b.ignore_lines_startswith || []).join('\n'),
      col_checkno: colObj.checkno != null ? String(colObj.checkno) : '',
      col_credit: colObj.credit != null ? String(colObj.credit) : '',
      col_date: colObj.date != null ? String(colObj.date) : '',
      col_debit: colObj.debit != null ? String(colObj.debit) : '',
      col_description: colObj.description != null ? String(colObj.description) : '',
      col_fees: colObj.fees != null ? String(colObj.fees) : '',
      col_memo: colObj.memo != null ? String(colObj.memo) : '',
    });
    setOpen(true);
  };

  const onSubmit = async (e) => {
    e.preventDefault(); setSaving(true); setError('');
    try {
      const name = (form.name || '').trim().toLowerCase();
      if (!name) throw new Error('name is required');
      const ignore_lines_contains = (form.ignore_lines_contains || '').split(/\r?\n/).map(s=>s.trim()).filter(Boolean);
      const ignore_lines_startswith = (form.ignore_lines_startswith || '').split(/\r?\n/).map(s=>s.trim()).filter(Boolean);
      if (form.col_date === '' || Number.isNaN(parseInt(form.col_date, 10))) throw new Error('date column is required');
      if (form.col_debit === '' || Number.isNaN(parseInt(form.col_debit, 10))) throw new Error('debit column is required');
      if (form.col_description === '' || Number.isNaN(parseInt(form.col_description, 10))) throw new Error('description column is required');
      const colMap = {};
      const addIfNum = (key, val) => {
        if (val !== '' && !Number.isNaN(parseInt(val, 10))) colMap[key] = parseInt(val, 10);
      };
      addIfNum('checkno', form.col_checkno);
      addIfNum('credit', form.col_credit);
      addIfNum('date', form.col_date);
      addIfNum('debit', form.col_debit);
      addIfNum('description', form.col_description);
      addIfNum('fees', form.col_fees);
      addIfNum('memo', form.col_memo);
      const columns = Object.keys(colMap).length ? [colMap] : [];
      const payload = {
        name,
        date_format: form.date_format || undefined,
        delim: form.delim || undefined,
        ignore_lines_contains: ignore_lines_contains.length ? ignore_lines_contains : undefined,
        ignore_lines_startswith: ignore_lines_startswith.length ? ignore_lines_startswith : undefined,
        columns: columns.length ? columns : undefined,
      };
      if (mode === 'edit' && originalKey) {
        if (originalKey !== name) {
          await window.api.removeBank(originalKey);
        } else {
          await window.api.removeBank(originalKey);
        }
      }
      await window.api.addBank(payload);
      setForm(empty);
      setOriginalKey('');
      setMode('add');
      setOpen(false);
      await reload();
    } catch (err) { setError(err.message || 'Error'); } finally { setSaving(false); }
  };

  const onDelete = async (name) => {
    if (!(await window.showConfirm(`Delete ${name}?`))) return;
    try { await window.api.removeBank(name); await reload(); } catch (err) { alert(err.message || 'Error'); }
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
    onEdit,
    onSubmit,
    onDelete,
  };
}

window.useBankForm = useBankForm;
