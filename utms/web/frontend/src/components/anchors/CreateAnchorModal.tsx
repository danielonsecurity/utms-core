import { useState } from 'react';
import { CreateAnchorData } from '../../types/anchors';

interface CreateAnchorModalProps {
    isOpen: boolean;
    onClose: () => void;
    onCreate: (data: CreateAnchorData) => Promise<void>;
}

export const CreateAnchorModal = ({ isOpen, onClose, onCreate }: CreateAnchorModalProps) => {
    const [formData, setFormData] = useState<CreateAnchorData>({
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
	    alert('Failed to create anchor: ' + (error as Error).message);
	}
    };

    if (!isOpen) return null;

    return (
	<div className="modal" onClick={onClose}>
	    <div className="modal__content" onClick={e => e.stopPropagation()}>
            <div className="modal__header">
            <h2 className="modal__title">Create New Anchor</h2>
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
            <div className="modal__footer">
            <button type="submit" className="modal__btn modal__btn--create">Create</button>
            </div>
            </form>
            </div>
	    </div>
	    </div>
    );
};
