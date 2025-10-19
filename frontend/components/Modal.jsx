const Modal = ({ title, open, onClose, children, onSubmit, submitLabel = 'Save' }) => {
  if (!open) return null;
  return (
    <div style={{position:'fixed', inset:0, background:'rgba(0,0,0,0.4)', display:'flex', alignItems:'center', justifyContent:'center', zIndex:50}}>
      <div style={{background:'#fff', borderRadius:8, padding:16, width:'min(680px, 92vw)', boxShadow:'0 10px 25px rgba(0,0,0,0.2)'}}>
        <div style={{display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:12}}>
          <h3 style={{margin:0}}>{title}</h3>
          <button onClick={onClose} style={{background:'#e5e7eb', color:'#111827'}}>Close</button>
        </div>
        <div style={{maxHeight:'70vh', overflow:'auto'}}>
          {children}
        </div>
        {onSubmit && (
          <div style={{display:'flex', gap:8, justifyContent:'flex-end', marginTop:12}}>
            <button onClick={onSubmit}>{submitLabel}</button>
            <button onClick={onClose} style={{background:'#e5e7eb', color:'#111827'}}>Cancel</button>
          </div>
        )}
      </div>
    </div>
  );
};

window.Modal = Modal;
