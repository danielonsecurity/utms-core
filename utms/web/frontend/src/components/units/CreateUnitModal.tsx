import { useState } from 'react';
import { CreateUnitData } from '../../types/units';

interface CreateUnitModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreate: (data: CreateUnitData) => Promise<void>;
}

export const CreateUnitModal = ({ isOpen, onClose, onCreate }: CreateUnitModalProps) => {
  const [formData, setFormData] = useState<CreateUnitData>({
    label: '',
    name: '',
    value: '',
    groups: []
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await onCreate(formData);
      onClose();
      setFormData({ label: '', name: '', value: '', groups: [] });
    } catch (error) {
      alert('Failed to create unit: ' + (error as Error).message);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal" onClick={onClose}>
      <div className="modal__content" onClick={e => e.stopPropagation()}>
        <div className="modal__header">
          <h2 className="modal__title">Create New Unit</h2>
          <span className="modal__close" onClick={onClose}>&times;</span>
        </div>
        <div className="modal__body">
          <form onSubmit={handleSubmit} className="modal__form">
            <div className="modal__form-group">
              <label className="modal__form-label">Label:</label>
              <input
                className="modal__form-input"
                value={formData.label}
                onChange={e => setFormData(prev => ({ ...prev, label: e.target.value }))}
                required
              />
            </div>
            <div className="modal__form-group">
              <label className="modal__form-label">Name:</label>
              <input
                className="modal__form-input"
                value={formData.name}
                onChange={e => setFormData(prev => ({ ...prev, name: e.target.value }))}
                required
              />
            </div>
            <div className="modal__form-group">
              <label className="modal__form-label">Value:</label>
              <input
                className="modal__form-input"
                value={formData.value}
                onChange={e => setFormData(prev => ({ ...prev, value: e.target.value }))}
                required
              />
            </div>
            <div className="modal__form-group">
              <label className="modal__form-label">Groups (comma-separated):</label>
              <input
                className="modal__form-input"
                value={formData.groups.join(', ')}
                onChange={e => setFormData(prev => ({
                  ...prev,
                  groups: e.target.value.split(',').map(g => g.trim()).filter(Boolean)
                }))}
              />
            </div>
            <div className="modal-footer">
              <button type="submit" className="modal__btn modal__btn--create">Create</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
