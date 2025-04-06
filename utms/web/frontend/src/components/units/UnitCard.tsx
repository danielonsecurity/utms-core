import { useState } from "react";
import { Unit } from "../../types/units";
import { formatScientific } from "../../utils/format";
import { unitsApi } from "../../api/unitsApi";
import Decimal from "decimal.js";

interface UnitCardProps {
  unit: Unit;
  label: string;
  onDelete: (label: string) => void;
  onUpdate: () => void;
  onGroupClick?: (group: string) => void;
}

export const UnitCard = ({
  unit,
  label,
  onDelete,
  onUpdate,
  onGroupClick,
}: UnitCardProps) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedUnit, setEditedUnit] = useState({
    ...unit,
    label: label,
  });

  const handleSave = async () => {
    try {
      const updates: Record<string, any> = {};

      // Only include changed fields
      if (editedUnit.label !== label) {
        updates.label = editedUnit.label;
      }
      if (editedUnit.name !== unit.name) {
        updates.name = editedUnit.name;
      }
      if (editedUnit.value !== unit.value) {
        updates.value = editedUnit.value;
      }
      if (JSON.stringify(editedUnit.groups) !== JSON.stringify(unit.groups)) {
        updates.groups = editedUnit.groups;
      }

      // Only make the API call if there are changes
      if (Object.keys(updates).length > 0) {
        const result = await unitsApi.updateUnit(label, updates);
        setIsEditing(false);
        onUpdate();
      } else {
        setIsEditing(false);
      }
    } catch (error) {
      alert("Failed to save changes: " + (error as Error).message);
    }
  };

  const startEditing = () => {
    setEditedUnit((prev) => ({
      ...prev,
      label: label,
    }));
    setIsEditing(true);
  };

  const addGroup = () => {
    const newGroup = prompt("Enter new group name:");
    if (newGroup?.trim()) {
      setEditedUnit((prev) => ({
        ...prev,
        groups: [...prev.groups, newGroup.trim()],
      }));
    }
  };

  const removeGroup = (groupToRemove: string) => {
    setEditedUnit((prev) => ({
      ...prev,
      groups: prev.groups.filter((g) => g !== groupToRemove),
    }));
  };

  const handleContentEdit = (
    field: keyof typeof editedUnit,
    content: string,
  ) => {
    setEditedUnit((prev) => ({
      ...prev,
      [field]: content,
    }));
  };

  return (
    <div className="unit-card card" data-unit={label}>
      <div className="card__header">
        <h3
          className={`card__title edit-target ${isEditing ? "editing" : ""}`}
          data-field="label"
          contentEditable={isEditing}
          onBlur={(e) =>
            handleContentEdit("label", e.currentTarget.textContent || "")
          }
          suppressContentEditableWarning
        >
          {editedUnit.label}
        </h3>

        <div className="unit-card__controls">
          <button
            className={`btn btn--icon btn--edit ${isEditing ? "hidden" : ""}`}
            data-action="edit"
            title="Edit unit"
            onClick={startEditing}
          >
            <i className="material-icons">edit</i>
          </button>
          <div
            className={`unit-card__edit-controls ${isEditing ? "visible" : ""}`}
          >
            <button
              className="btn btn--icon btn--delete"
              data-action="delete"
              onClick={() => onDelete(label)}
            >
              <i className="material-icons">delete</i>
            </button>
            <button
              className="btn btn--icon btn--save"
              data-action="save"
              onClick={handleSave}
            >
              <i className="material-icons">save</i>
            </button>
            <button
              className="btn btn--icon btn--cancel"
              data-action="cancel"
              onClick={() => {
                setIsEditing(false);
                setEditedUnit(unit);
              }}
            >
              <i className="material-icons">close</i>
            </button>
          </div>
        </div>
      </div>

      <div className="card__body">
        <div className="unit-card__info">
          <div className="unit-card__row">
            <span className="unit-card__label">Name:</span>
            <span
              className={`unit-card__value edit-target ${isEditing ? "editing" : ""}`}
              data-field="name"
              contentEditable={isEditing}
              onBlur={(e) =>
                handleContentEdit("name", e.currentTarget.textContent || "")
              }
              suppressContentEditableWarning
            >
              {editedUnit.name}
            </span>
          </div>

          <div className="unit-card__row">
            <span className="unit-card__label">Value:</span>
            <span
              className={`unit-card__value edit-target ${isEditing ? "editing" : ""}`}
              data-field="value"
              data-full-value={unit.value}
              contentEditable={isEditing}
              onBlur={(e) =>
                handleContentEdit("value", e.currentTarget.textContent || "")
              }
              suppressContentEditableWarning
            >
              {isEditing ? unit.value : formatScientific(unit.value, 20)}
            </span>
          </div>

          <div className="unit-card__row">
            <span className="unit-card__label">Groups:</span>
            <span
              className={`groups edit-target ${isEditing ? "editing" : ""}`}
              data-field="groups"
            >
              {editedUnit.groups.map((group, index) => (
                <span key={`${group}-${index}`} className="groups__tag">
                  <span
                    className="groups__name"
                    data-group={group}
                    onClick={() => !isEditing && onGroupClick?.(group)}
                  >
                    {group}
                  </span>
                  {isEditing && (
                    <i
                      className="groups__remove material-icons"
                      onClick={() => removeGroup(group)}
                    >
                      close
                    </i>
                  )}
                </span>
              ))}
              {isEditing && (
                <button className="groups__add" onClick={addGroup}>
                  <i className="material-icons">add</i>
                </button>
              )}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
