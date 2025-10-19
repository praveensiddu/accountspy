const Modal = ({ title, open, onClose, children, onSubmit, submitLabel = 'Save', submitDisabled = false }) => {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-3xl p-6 overflow-y-auto max-h-[85vh]">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-semibold m-0">{title}</h3>
          <button onClick={onClose} className="px-3 py-1.5 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300">Close</button>
        </div>
        <div className="space-y-3">
          {children}
        </div>
        {onSubmit && (
          <div className="flex gap-2 justify-end mt-4">
            <button onClick={onSubmit} disabled={submitDisabled} className={`px-4 py-2 rounded-md text-white ${submitDisabled ? 'bg-blue-600/70 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'}`}>{submitLabel}</button>
            <button onClick={onClose} className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300">Cancel</button>
          </div>
        )}
      </div>
    </div>
  );
};

window.Modal = Modal;
