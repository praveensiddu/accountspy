function ExportModal({ open, path, onClose }) {
  if (!open) return null;
  return (
    <div
      role="dialog"
      aria-modal="true"
      style={{ position: 'fixed', inset: 0, zIndex: 2000, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
    >
      <div style={{ position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.45)' }} onClick={onClose} />
      <div style={{ position: 'relative', background: 'white', width: 'min(92vw, 560px)', borderRadius: 12, boxShadow: '0 10px 30px rgba(0,0,0,0.25)' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #eee', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ fontSize: 18, fontWeight: 600 }}>Export Successful</div>
          <button onClick={onClose} title="Close" style={{ border: 0, background: 'transparent', fontSize: 20, lineHeight: 1, cursor: 'pointer' }}>×</button>
        </div>
        <div style={{ padding: '16px 20px' }}>
          <div style={{ marginBottom: 8 }}>Exported to:</div>
          <div style={{ wordBreak: 'break-all', background: '#f7f7f7', padding: '10px 12px', borderRadius: 8 }}>
            {path ? (
              <a href={'/api/export-accounts/download'} target="_blank" rel="noopener noreferrer" style={{ color: '#0b6bcb', textDecoration: 'underline' }}>
                {path}
              </a>
            ) : (
              <span>file created</span>
            )}
          </div>
        </div>
        <div style={{ padding: '12px 20px', display: 'flex', justifyContent: 'flex-end', gap: 8, borderTop: '1px solid #eee' }}>
          <button onClick={onClose} className="btn" style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #ddd', background: '#fff', cursor: 'pointer' }}>Close</button>
          {path && (
            <a href={'/api/export-accounts/download'} target="_blank" rel="noopener noreferrer" style={{ padding: '8px 12px', borderRadius: 8, background: '#0b6bcb', color: '#fff', textDecoration: 'none' }}>Open File</a>
          )}
        </div>
      </div>
    </div>
  );
}

window.ExportModal = ExportModal;
