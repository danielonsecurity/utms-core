import { useState } from "react";
import { ConfigValue } from "../../types/config";
import { configApi } from "../../api/configApi";

interface ConfigCardProps {
  configKey: string;
  value: ConfigValue;
  onUpdate: () => void;
}

export const ConfigCard = ({ configKey, value, onUpdate }: ConfigCardProps) => {
  const [isEditing, setIsEditing] = useState(false);
  const [showOriginalCode, setShowOriginalCode] = useState(false);
  const [editedConfig, setEditedConfig] = useState({
    key: configKey,
    value: value.is_dynamic
      ? value.original || String(value.value)
      : String(value.value),
  });

  const handleSave = async () => {
    try {
      // Rename key if changed
      if (editedConfig.key !== configKey) {
        await configApi.renameConfigKey(configKey, editedConfig.key);
      }

      // Update value
      await configApi.updateConfig(editedConfig.key, editedConfig.value);

      setIsEditing(false);
      onUpdate();
    } catch (error) {
      alert("Failed to save changes: " + (error as Error).message);
    }
  };

  const renderValueContent = () => {
    // Ensure value is always converted to string
    const displayValue = String(value.value);
    const originalValue = value.original || displayValue;

    if (value.is_dynamic) {
      return (
        <>
          <div className="config-card__row">
            <span className="config-card__label">Value:</span>
            <span className="config-card__value">{displayValue}</span>

            {/* Code view toggle button */}
            <button
              className="btn btn--icon btn--code-toggle"
              onClick={() => setShowOriginalCode(!showOriginalCode)}
              title={showOriginalCode ? "Hide Code" : "Show Code"}
            >
              <i className="material-icons">
                {showOriginalCode ? "code_off" : "code"}
              </i>
            </button>
          </div>

          {showOriginalCode && (
            <div className="config-card__row config-card__row--code">
              <span className="config-card__label">Original:</span>
              <span
                className={`config-card__value edit-target ${isEditing ? "editing" : ""}`}
                data-field="value"
                contentEditable={isEditing}
                onBlur={(e) =>
                  setEditedConfig((prev) => ({
                    ...prev,
                    value: e.currentTarget.textContent || originalValue,
                  }))
                }
                suppressContentEditableWarning
              >
                {originalValue}
              </span>
            </div>
          )}
        </>
      );
    }

    return (
      <div className="config-card__row">
        <span className="config-card__label">Value:</span>
        <span
          className={`config-card__value edit-target ${isEditing ? "editing" : ""}`}
          data-field="value"
          contentEditable={isEditing}
          onBlur={(e) =>
            setEditedConfig((prev) => ({
              ...prev,
              value: e.currentTarget.textContent || displayValue,
            }))
          }
          suppressContentEditableWarning
        >
          {displayValue}
        </span>
      </div>
    );
  };

  return (
    <div className="config-card card" data-config={configKey}>
      <div className="card__header">
        <h3
          className={`card__title edit-target ${isEditing ? "editing" : ""}`}
          data-field="key"
          contentEditable={isEditing}
          onBlur={(e) =>
            setEditedConfig((prev) => ({
              ...prev,
              key: e.currentTarget.textContent || configKey,
            }))
          }
          suppressContentEditableWarning
        >
          {editedConfig.key}
        </h3>

        <div className="config-card__controls">
          <button
            className={`btn btn--icon btn--edit ${isEditing ? "hidden" : ""}`}
            data-action="edit"
            title="Edit config"
            onClick={() => setIsEditing(true)}
          >
            <i className="material-icons">edit</i>
          </button>
          <div
            className={`config-card__edit-controls ${isEditing ? "visible" : ""}`}
          >
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
                setShowOriginalCode(false);
                setEditedConfig({
                  key: configKey,
                  value: value.is_dynamic
                    ? value.original || String(value.value)
                    : String(value.value),
                });
              }}
            >
              <i className="material-icons">close</i>
            </button>
          </div>
        </div>
      </div>

      <div className="card__body">
        <div className="config-card__info">{renderValueContent()}</div>
      </div>
    </div>
  );
};
