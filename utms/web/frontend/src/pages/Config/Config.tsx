import { useEffect, useState } from 'react';
import { Card } from '../../components/common/Card/Card';
import { configApi } from '../../api/configApi';
import { ConfigData } from '../../types/config';

const ConfigItem = ({ 
  configKey, 
  value, 
  choices 
}: { 
  configKey: string; 
  value: string | string[]; 
  choices?: string[]; 
}) => {
  const handleSave = async (key: string, index?: number) => {
    try {
      if (typeof index === 'number') {
        const inputValue = (document.getElementById(`${key}_${index}`) as HTMLInputElement | HTMLSelectElement).value;
        await configApi.updateListItem(key, index, inputValue);
      } else {
        const inputValue = (document.getElementById(key) as HTMLInputElement | HTMLSelectElement).value;
        await configApi.updateConfig(key, inputValue);
      }
      alert('Saved successfully');
    } catch (error) {
      alert('Error saving: ' + (error as Error).message);
    }
  };

  const handleAddItem = async (key: string) => {
    try {
      await configApi.addNewListItem(key);
      window.location.reload();
    } catch (error) {
      alert('Error adding item: ' + (error as Error).message);
    }
  };

  const handleSelectChange = async (key: string, index?: number) => {
    const selectId = index !== undefined ? `${key}_${index}` : key;
    const select = document.getElementById(selectId) as HTMLSelectElement;
    
    if (select.value === '__new__') {
      const newValue = prompt('Enter new value:');
      if (newValue) {
        const option = document.createElement('option');
        option.value = newValue;
        option.textContent = newValue;
        select.insertBefore(option, select.lastElementChild);
        select.value = newValue;
        
        try {
          if (index !== undefined) {
            await configApi.updateListItem(key, index, newValue);
          } else {
            await configApi.updateConfig(key, newValue);
          }
        } catch (error) {
          alert('Error saving: ' + (error as Error).message);
          select.value = select.querySelector('option:checked')?.value || '';
        }
      } else {
        select.value = select.querySelector('option:checked')?.value || '';
      }
    }
  };

  return (
    <div className="config__item card">
      <div className="card__header">
        <label className="config__label" htmlFor={configKey}>{configKey}</label>
      </div>
      <div className="card__body">
        {Array.isArray(value) ? (
          <div className="config__list">
            {value.map((item, index) => (
              <div key={index} className="config__list-item">
                {choices ? (
                  <select
                    id={`${configKey}_${index}`}
                    className="config__select"
                    defaultValue={item}
                    onChange={() => handleSelectChange(configKey, index)}
                  >
                    {choices.map(choice => (
                      <option key={choice} value={choice}>
                        {choice}
                      </option>
                    ))}
                    <option value="__new__">Add New...</option>
                  </select>
                ) : (
                  <input
                    type="text"
                    className="config__input"
                    id={`${configKey}_${index}`}
                    defaultValue={item}
                  />
                )}
                <button 
                  className="config__btn config__btn--save"
                  onClick={() => handleSave(configKey, index)}
                >
                  <i className="material-icons">save</i>
                </button>
              </div>
            ))}
            <button 
              className="config__btn config__btn--add"
              onClick={() => handleAddItem(configKey)}
            >
              <i className="material-icons">add</i>
              Add Item
            </button>
          </div>
        ) : (
          <div className="config__field">
            {choices ? (
              <select
                id={configKey}
                className="config__select"
                defaultValue={value}
                onChange={() => handleSelectChange(configKey)}
              >
                {choices.map(choice => (
                  <option key={choice} value={choice}>
                    {choice}
                  </option>
                ))}
                <option value="__new__">Add New...</option>
              </select>
            ) : (
              <input
                type="text"
                className="config__input"
                id={configKey}
                defaultValue={value}
              />
            )}
            <button 
              className="config__btn config__btn--save"
              onClick={() => handleSave(configKey)}
            >
              <i className="material-icons">save</i>
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export const Config = () => {
  const [config, setConfig] = useState<ConfigData | null>(null);

  useEffect(() => {
    configApi.getConfig().then(setConfig);
  }, []);

  if (!config) return <div>Loading...</div>;

  return (
    <div className="config">
      {Object.entries(config)
        .filter(([key]) => !key.endsWith('-choices'))
        .map(([key, value]) => (
          <ConfigItem
            key={key}
            configKey={key}
            value={value}
            choices={config[`${key}-choices`] as string[] | undefined}
          />
        ))}
    </div>
  );
};
