import React from 'react';

export interface WidgetProps {
    id: string;
    title: string;
    onRemove: (id: string) => void;
    onConfigure?: () => void;
}

export const BaseWidget: React.FC<WidgetProps> = ({ 
    id, 
    title, 
    onRemove, 
    onConfigure, 
    children 
}) => {
    return (
	<div className="widget">
	    <div className="widget__header">
            <span className="widget__title">{title}</span>
            <div className="widget__controls">
            {onConfigure && (
		<button 
		className="btn btn--icon" 
		onClick={onConfigure}
		title="Configure widget"
		    >
		    <i className="material-icons">settings</i>
		    </button>
            )}
            <button 
        className="btn btn--icon" 
        onClick={() => onRemove(id)}
        title="Remove widget"
            >
            <i className="material-icons">close</i>
            </button>
            </div>
	    </div>
	    <div className="widget__content">
            {children}
	</div>
	    </div>
    );
};
