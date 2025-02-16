import { useState } from 'react';
import { Anchor } from '../../types/anchors';
import { formatScientific } from '../../utils/format';
import { anchorsApi } from '../../api/anchorsApi';

interface AnchorCardProps {
    anchor: Anchor;
    label: string;
    onDelete: (label: string) => void;
    onUpdate: () => void;
    onGroupClick?: (group: string) => void;
}

export const AnchorCard = ({ anchor, label, onDelete, onUpdate, onGroupClick }: AnchorCardProps) => {
    const [isEditing, setIsEditing] = useState(false);
    const [editedAnchor, setEditedAnchor] = useState({
        ...anchor,
        label: label
    });
    const [showOriginal, setShowOriginal] = useState<{[key: string]: boolean}>({});

    const handleSave = async () => {
        try {
            const updates: Record<string, any> = {};
            
            if (editedAnchor.label !== label) {
                updates.label = editedAnchor.label;
            }
            if (editedAnchor.name !== anchor.name) {
                updates.name = editedAnchor.name;
            }
            if (editedAnchor.value !== anchor.value) {
                updates.value = editedAnchor.value;
            }
            if (JSON.stringify(editedAnchor.groups) !== JSON.stringify(anchor.groups)) {
                updates.groups = editedAnchor.groups;
            }

            if (Object.keys(updates).length > 0) {
                await anchorsApi.updateAnchor(label, updates);
                setIsEditing(false);
                onUpdate();
            } else {
                setIsEditing(false);
            }
        } catch (error) {
            alert('Failed to save changes: ' + (error as Error).message);
        }
    };

    const handleContentEdit = (field: keyof typeof editedAnchor, content: string) => {
        setEditedAnchor(prev => ({
            ...prev,
            [field]: content
        }));
    };

    const addGroup = () => {
        const newGroup = prompt('Enter new group name:');
        if (newGroup?.trim()) {
            setEditedAnchor(prev => ({
                ...prev,
                groups: [...prev.groups, newGroup.trim()]
            }));
        }
    };

    const removeGroup = (groupToRemove: string) => {
        setEditedAnchor(prev => ({
            ...prev,
            groups: prev.groups.filter(g => g !== groupToRemove)
        }));
    };

    const toggleOriginal = (field: string) => {
        setShowOriginal(prev => ({
            ...prev,
            [field]: !prev[field]
        }));
    };

    return (
        <div className="anchor-card card" data-anchor={label}>
            <div className="card__header">
                <h3 className="card__title">{label}</h3>
                <div className="anchor-card__controls">
                    {!isEditing ? (
                        <button 
                            className="btn btn--icon btn--edit"
                            onClick={() => setIsEditing(true)}
                        >
                            <i className="material-icons">edit</i>
                        </button>
                    ) : (
                        <div className="anchor-card__edit-controls">
                            <button 
                                className="btn btn--icon btn--delete"
                                onClick={() => onDelete(label)}
                            >
                                <i className="material-icons">delete</i>
                            </button>
                            <button 
                                className="btn btn--icon btn--save"
                                onClick={handleSave}
                            >
                                <i className="material-icons">save</i>
                            </button>
                            <button 
                                className="btn btn--icon btn--cancel"
                                onClick={() => {
                                    setIsEditing(false);
                                    setEditedAnchor({ ...anchor, label });
                                }}
                            >
                                <i className="material-icons">close</i>
                            </button>
                        </div>
                    )}
                </div>
            </div>

            <div className="card__body">
                <div className="anchor-card__info">
                    <div className="anchor-card__row">
                        <span className="anchor-card__label">Name:</span>
                        <span 
                            className={`anchor-card__value ${isEditing ? 'editing' : ''}`}
                            contentEditable={isEditing}
                            onInput={(e) => handleContentEdit('name', e.currentTarget.textContent || '')}
                            suppressContentEditableWarning
                        >
                            {editedAnchor.name}
                        </span>
                    </div>

                    <div className="anchor-card__row">
                        <span className="anchor-card__label">Value:</span>
                        <span 
                            className={`anchor-card__value ${isEditing ? 'editing' : ''}`}
                            contentEditable={isEditing}
                            onInput={(e) => handleContentEdit('value', e.currentTarget.textContent || '')}
                            suppressContentEditableWarning
                        >
                            {isEditing ? editedAnchor.value : formatScientific(editedAnchor.value, 20)}
                        </span>
                    </div>

                    {anchor.formats && (
                        <div className="anchor-card__row">
                            <span className="anchor-card__label">Formats:</span>
                            <div className="anchor-card__formats">
                                {anchor.formats.map((format, index) => (
                                    <div key={index} className="anchor-card__format">
                                        {format.format && (
                                            <span className="anchor-card__format-type">
                                                {format.format}
                                            </span>
                                        )}
                                        {format.units && (
                                            <span className="anchor-card__format-units">
                                                {Array.isArray(format.units) ? format.units.join(', ') : ''}
                                            </span>
                                        )}
                                        {format.style && (
                                            <span className="anchor-card__format-style">
                                                {format.style}
                                            </span>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {anchor.uncertainty && (
                        <div className="anchor-card__row">
                            <span className="anchor-card__label">Uncertainty:</span>
                            <div className="anchor-card__uncertainty">
                                <div>Absolute: {anchor.uncertainty.absolute}</div>
                                <div>Relative: {anchor.uncertainty.relative}</div>
                                {anchor.uncertainty.confidence_95 && (
                                    <div>
                                        95% Confidence: [{anchor.uncertainty.confidence_95[0]}, {anchor.uncertainty.confidence_95[1]}]
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    <div className="anchor-card__row">
                        <span className="anchor-card__label">Groups:</span>
                        <div className="groups">
                            {anchor.groups.map((group, index) => (
                                <span 
                                    key={index} 
                                    className="groups__tag"
                                    onClick={() => !isEditing && onGroupClick?.(group)}
                                >
                                    <span className="groups__name">{group}</span>
                                    {isEditing && (
                                        <i 
                                            className="groups__remove material-icons"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                setEditedAnchor(prev => ({
                                                    ...prev,
                                                    groups: prev.groups.filter(g => g !== group)
                                                }));
                                            }}
                                        >
                                            close
                                        </i>
                                    )}
                                </span>
                            ))}
                            {isEditing && (
                                <button 
                                    className="groups__add"
                                    onClick={() => {
                                        const newGroup = prompt('Enter new group name:');
                                        if (newGroup?.trim()) {
                                            setEditedAnchor(prev => ({
                                                ...prev,
                                                groups: [...prev.groups, newGroup.trim()]
                                            }));
                                        }
                                    }}
                                >
                                    <i className="material-icons">add</i>
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );

};
