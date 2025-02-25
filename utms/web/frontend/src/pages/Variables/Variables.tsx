import { useEffect, useState } from "react";
import { Card } from "../../components/common/Card/Card";
import { variablesApi } from "../../api/variables";
import { Variable } from "../../types/variables";

interface VariableCardContentProps {
  name: string;
  variable: Variable;
}

const VariableCardContent = ({ name, variable }: VariableCardContentProps) => {
  const [showOriginal, setShowOriginal] = useState(false);

  return (
    <div className="variable-card__info">
      <div className="variable-card__row">
        <span className="variable-card__label">Type:</span>
        <span className="variable-card__type">{variable.type}</span>
      </div>
      <div className="variable-card__row">
        <span className="variable-card__label">Value:</span>
        <div className="variable-card__value-container">
          <div className="variable-card__evaluated-value">
            <span className="variable-card__value">{variable.value}</span>
            <button
              className="variable-card__original-btn"
              onClick={() => setShowOriginal(!showOriginal)}
              title={
                showOriginal
                  ? "Hide original expression"
                  : "Show original expression"
              }
            >
              <i className="material-icons">code</i>
            </button>
            <div
              className="variable-card__original-code"
              style={{ display: showOriginal ? "block" : "none" }}
            >
              <pre className="variable-card__code">
                {variable.value_original}
              </pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export const Variables = () => {
  const [data, setData] = useState<Record<string, Variable> | null>(null);

  useEffect(() => {
    variablesApi.getVariables().then(setData);
  }, []);

  if (!data) return <div>Loading...</div>;

  return (
    <div className="variables">
      <div className="variables__grid">
        {Object.entries(data).map(([name, variable]) => (
          <Card key={name} title={name}>
            <VariableCardContent name={name} variable={variable} />
          </Card>
        ))}
      </div>
    </div>
  );
};
