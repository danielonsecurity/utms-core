import { ReactNode } from 'react';

interface CardProps {
  title?: string;
  children: ReactNode;
  actions?: ReactNode;
}

export const Card = ({ title, children, actions }: CardProps) => {
  return (
    <div className="card">
      {(title || actions) && (
        <div className="card__header">
          {title && <h3 className="card__title">{title}</h3>}
          {actions}
        </div>
      )}
      <div className="card__body">
        {children}
      </div>
    </div>
  );
};
