const { useState } = React;

function useExportAccounts() {
  const [exporting, setExporting] = useState(false);
  const [exportResult, setExportResult] = useState({ open: false, path: '' });

  const handleExport = async () => {
    if (exporting) return;
    try {
      setExporting(true);
      const res = await fetch('/api/export-accounts', { method: 'POST' });
      if (!res.ok) { const t = await res.text().catch(()=> ''); throw new Error(t || 'Export failed'); }
      const data = await res.json().catch(()=> ({}));
      const outPath = (data && data.path) ? String(data.path) : '';
      setExportResult({ open: true, path: outPath });
    } catch (e) {
      alert(e.message || 'Export failed');
    } finally {
      setExporting(false);
    }
  };

  const closeExportModal = () => setExportResult({ open: false, path: '' });

  return { exporting, exportResult, handleExport, closeExportModal };
}

window.useExportAccounts = useExportAccounts;
