import { ButtonHTMLAttributes, ReactNode } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'create' | 'edit' | 'save' | 'cancel' | 'delete' | 'clear' | 'icon';
  children: ReactNode;
}

export const Button = ({ 
  variant, 
  children, 
  className = '', 
  ...props 
}: ButtonProps) => {
  return (
    <button 
      className={`btn ${variant ? `btn--${variant}` : ''} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};
