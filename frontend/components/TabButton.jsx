function TabButton({ active, onClick, children }) {
  return (
    <button type="button" onClick={onClick} className={`tab ${active ? 'active' : ''}`}>
      {children}
    </button>
  );
}

window.TabButton = TabButton;
