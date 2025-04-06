import { useState, useEffect, useCallback } from "react";
import { configApi } from "../../api/configApi";
import { ConfigData, ConfigValue } from "../../types/config";
import { ConfigCard } from "../../components/config/ConfigCard";
import { CreateConfigModal } from "../../components/config/CreateConfigModal";

export const Config = () => {
  const [config, setConfig] = useState<ConfigData | null>(null);
  const [labelSearch, setLabelSearch] = useState("");
  const [valueSearch, setValueSearch] = useState("");
  const [showDynamicOnly, setShowDynamicOnly] = useState(false);
  const [sortType, setSortType] = useState("label-asc");
  const [editingLabel, setEditingLabel] = useState<string | null>(null);
  const [newLabel, setNewLabel] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);

  const loadConfig = useCallback(async () => {
    try {
      const data = await configApi.getConfig();
      console.log("config.data=", data);
      setConfig(data);
    } catch (error) {
      alert("Failed to load config: " + (error as Error).message);
    }
  }, []);

  useEffect(() => {
    loadConfig();
  }, [loadConfig]);

  const handleLabelEdit = async (oldKey: string) => {
    if (!newLabel || newLabel === oldKey) {
      setEditingLabel(null);
      return;
    }

    try {
      await configApi.renameConfigKey(oldKey, newLabel);
      await loadConfig();
      setEditingLabel(null);
    } catch (error) {
      alert(
        `Error renaming: ${error instanceof Error ? error.message : error}`,
      );
    }
  };

  const filteredAndSortedConfig = config
    ? Object.entries(config)
        .filter(([key]) => !key.endsWith("-choices"))
        .filter(([key, value]) => {
          // Label search
          const matchesLabel = key
            .toLowerCase()
            .includes(labelSearch.toLowerCase());

          // Value search (both original and evaluated)
          const originalValue = value.value;
          const matchesValue = String(originalValue)
            .toLowerCase()
            .includes(valueSearch.toLowerCase());

          // Dynamic filter
          const matchesDynamicFilter = !showDynamicOnly || value.is_dynamic;

          return matchesLabel && matchesValue && matchesDynamicFilter;
        })
        .sort(([labelA], [labelB]) => {
          switch (sortType) {
            case "label-asc":
              return labelA.localeCompare(labelB);
            case "label-desc":
              return labelB.localeCompare(labelA);
            default:
              return 0;
          }
        })
    : [];

  return (
    <div className="config">
      <div className="config__controls">
        <button
          className="btn btn--create"
          onClick={() => setIsModalOpen(true)}
        >
          <i className="material-icons">add</i>Create Config
        </button>
        <div className="config__search">
          <div className="config__search-field">
            <i className="material-icons config__search-icon">label</i>
            <input
              type="text"
              className="config__search-input"
              placeholder="Search by label..."
              value={labelSearch}
              onChange={(e) => setLabelSearch(e.target.value)}
            />
          </div>
          <div className="config__search-field">
            <i className="material-icons config__search-icon">title</i>
            <input
              type="text"
              className="config__search-input"
              placeholder="Search by value..."
              value={valueSearch}
              onChange={(e) => setValueSearch(e.target.value)}
            />
          </div>
        </div>

        <div className="config__controls-row">
          <div className="config__filters">
            <label className="config__dynamic-toggle">
              <input
                type="checkbox"
                checked={showDynamicOnly}
                onChange={() => setShowDynamicOnly(!showDynamicOnly)}
              />
              Show Dynamic Only
            </label>
          </div>

          <div className="sort">
            <select
              className="sort__select"
              value={sortType}
              onChange={(e) => setSortType(e.target.value)}
            >
              <option value="label-asc">Label A-Z</option>
              <option value="label-desc">Label Z-A</option>
            </select>
          </div>
        </div>
      </div>

      <div className="config__grid">
        {filteredAndSortedConfig.map(([key, value]) => (
          <ConfigCard
            key={key}
            configKey={key}
            value={value}
            onUpdate={loadConfig}
          />
        ))}
      </div>

      <CreateConfigModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onCreateSuccess={loadConfig}
      />
    </div>
  );
};

const ConfigItem = ({
  configKey,
  value,
  onUpdate,
}: {
  configKey: string;
  value: ConfigValue;
  onUpdate: () => Promise<void>;
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [localLabel, setLocalLabel] = useState(configKey);
  const [localValue, setLocalValue] = useState(
    value.is_dynamic && value.original ? value.original : value.value,
  );

  const handleSave = async () => {
    try {
      // Rename key if changed
      if (localLabel !== configKey) {
        await configApi.renameConfigKey(configKey, localLabel);
      }

      // Update value
      await configApi.updateConfig(localLabel, localValue);

      await onUpdate();
      setIsEditing(false);
    } catch (error) {
      alert(`Error saving: ${error instanceof Error ? error.message : error}`);
    }
  };
  const renderValue = () => {
    if (value.is_dynamic) {
      return (
        <>
          <div className="config-card__row">
            <span className="config-card__label">Evaluated Value:</span>
            <span className="config-card__value">{value.value}</span>
          </div>
          <div className="config-card__row">
            <span className="config-card__label">Original Expression:</span>
            <span
              className={`config-card__value ${isEditing ? "edit-target editing" : ""}`}
              contentEditable={isEditing}
              onInput={(e) =>
                setLocalValue((e.target as HTMLSpanElement).textContent || "")
              }
            >
              {value.original}
            </span>
          </div>
        </>
      );
    }

    return (
      <div className="config-card__row">
        <span className="config-card__label">Value:</span>
        <span
          className={`config-card__value ${isEditing ? "edit-target editing" : ""}`}
          contentEditable={isEditing}
          onInput={(e) =>
            setLocalValue((e.target as HTMLSpanElement).textContent || "")
          }
        >
          {String(value.value)}
        </span>
      </div>
    );
  };

  return (
    <div className="config-card card" data-config={configKey}>
      <div className="card__header">
        <h3
          className={`card__title ${isEditing ? "edit-target editing" : ""}`}
          contentEditable={isEditing}
          onInput={(e) =>
            setLocalLabel((e.target as HTMLHeadingElement).textContent || "")
          }
        >
          {localLabel}
        </h3>
        <div className="config-card__controls">
          {!isEditing ? (
            <button
              className="btn btn--icon btn--edit"
              onClick={() => setIsEditing(true)}
              title="Edit config"
            >
              <i className="material-icons">edit</i>
            </button>
          ) : (
            <div className="config-card__edit-controls">
              <button className="btn btn--icon btn--save" onClick={handleSave}>
                <i className="material-icons">save</i>
              </button>
              <button
                className="btn btn--icon btn--cancel"
                onClick={() => {
                  setIsEditing(false);
                  setLocalLabel(configKey);
                  setLocalValue(value.value);
                }}
              >
                <i className="material-icons">close</i>
              </button>
            </div>
          )}
        </div>
      </div>
      <div className="card__body">
        <div className="config-card__info">
          {renderValue()}

          {value.is_dynamic && (
            <div className="config-card__row">
              <span className="config-card__label">Original Expression:</span>
              <span
                className={`config-card__value ${isEditing ? "edit-target editing" : ""}`}
                contentEditable={isEditing}
                onInput={(e) =>
                  setLocalValue((e.target as HTMLSpanElement).textContent || "")
                }
              >
                {String(value.value)}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
