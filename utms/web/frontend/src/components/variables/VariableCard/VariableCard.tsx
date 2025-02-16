import { useState } from 'react';
import styles from './VariableCard.module.css';
import { Variable } from '../../../types/variables';

interface VariableCardProps {
  name: string;
  variable: Variable;
}

export const VariableCard = ({ name, variable }: VariableCardProps) => {
  const [showOriginal, setShowOriginal] = useState(false);

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <h3 className={styles.title}>{name}</h3>
      </div>
      <div className={styles.body}>
        <div className={styles.info}>
          <div className={styles.row}>
            <span className={styles.label}>Type:</span>
            <span className={styles.type}>{variable.type}</span>
          </div>
          <div className={styles.row}>
            <span className={styles.label}>Value:</span>
            <div className={styles.valueContainer}>
              <div className={styles.evaluatedValue}>
                <span className={styles.value}>{variable.value}</span>
                <button
                  className={styles.originalBtn}
                  onClick={() => setShowOriginal(!showOriginal)}
                  title={showOriginal ? "Hide original expression" : "Show original expression"}
                >
                  <i className="material-icons">code</i>
                </button>
                {showOriginal && (
                  <div className={styles.originalCode}>
                    <pre className={styles.code}>{variable.value_original}</pre>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
