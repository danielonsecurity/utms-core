import { useState } from "react";
import { configApi } from "../../api/configApi";

interface CreateConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreateSuccess: () => void;
}

interface CreateConfigData {
  key: string;
  value: string | number;
  isDynamic?: boolean;
}

export const CreateConfigModal = ({
  isOpen,
  onClose,
  onCreateSuccess,
}: CreateConfigModalProps) => {
  const [formData, setFormData] = useState<CreateConfigData>({
    key: "",
    value: "",
    isDynamic: false,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      // Use updateConfig to create a new config entry
      await configApi.updateConfig(formData.key, formData.value);

      onCreateSuccess();
      onClose();

      // Reset form
      setFormData({ key: "", value: "", isDynamic: false });
    } catch (error) {
      alert("Failed to create config: " + (error as Error).message);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal" onClick={onClose}>
      <div className="modal__content" onClick={(e) => e.stopPropagation()}>
        <div className="modal__header">
          <h2 className="modal__title">Create New Config</h2>
          <span className="modal__close" onClick={onClose}>
            &times;
          </span>
        </div>
        <div className="modal__body">
          <form onSubmit={handleSubmit} className="modal__form">
            <div className="modal__form-group">
              <label className="modal__form-label">Key:</label>
              <input
                className="modal__form-input"
                value={formData.key}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, key: e.target.value }))
                }
                required
              />
            </div>
            <div className="modal__form-group">
              <label className="modal__form-label">Value:</label>
              <input
                className="modal__form-input"
                value={formData.value}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, value: e.target.value }))
                }
                required
              />
            </div>
            <div className="modal__form-group">
              <label className="modal__form-label">
                <input
                  type="checkbox"
                  checked={formData.isDynamic}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      isDynamic: e.target.checked,
                    }))
                  }
                />
                Dynamic Config
              </label>
            </div>
            <div className="modal-footer">
              <button type="submit" className="modal__btn modal__btn--create">
                Create
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
