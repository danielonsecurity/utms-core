import { useState, useEffect } from 'react';
import { resolveApi } from '../../api/resolveApi';
import { ResolveResult } from '../../types/resolve';
import { Anchor } from '../../types/anchors';

interface ResolveProps {
    anchors: Record<string, Anchor>;
}

export const Resolve = ({ anchors }: ResolveProps) => {
    const [input, setInput] = useState('');
    const [selectedAnchors, setSelectedAnchors] = useState<Set<string>>(new Set());
    const [results, setResults] = useState<ResolveResult | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    // Initialize selected anchors when anchors prop changes
    useEffect(() => {
        if (anchors && Object.keys(anchors).length > 0) {
            setSelectedAnchors(new Set(Object.keys(anchors)));
        }
    }, [anchors]);


    const handleResolve = async () => {
        if (!input.trim()) {
            alert('Please enter a time expression');
            return;
        }

        if (selectedAnchors.size === 0) {
            alert('Please select at least one anchor');
            return;
        }

        setIsLoading(true);
	try {
            const requestData = {
		input: input.trim(),
		anchors: Array.from(selectedAnchors)
            };
            console.log('Sending request:', requestData); // Debug log

            const result = await resolveApi.resolveTime(requestData);
            console.log('Received response:', result); // Debug log
            setResults(result);
	} catch (error) {
            console.error('Resolve error:', error); // More detailed error logging
            alert((error as Error).message);
	} finally {
            setIsLoading(false);
	}
    };

    const handleSelectAll = () => {
        if (anchors) {
            setSelectedAnchors(new Set(Object.keys(anchors)));
        }
    };

    const handleDeselectAll = () => {
        setSelectedAnchors(new Set());
    };

    const toggleAnchor = (label: string) => {
        setSelectedAnchors(prev => {
            const next = new Set(prev);
            if (next.has(label)) {
                next.delete(label);
            } else {
                next.add(label);
            }
            return next;
        });
    };

    if (!anchors) {
        return null; // or return some loading state
    }

    const formatDate = (isoDate: string) => {
        const date = new Date(isoDate);
        return date.toLocaleString();
    };

    return (
        <div className="resolve">
            <div className="resolve__search">
            <div className="resolve__search-container">
            <input
        type="text"
        className="resolve__search-input"
        placeholder="Enter time expression (e.g., 'end of ww2')"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyPress={(e) => {
            if (e.key === 'Enter') {
                handleResolve();
            }
        }}
            />
            <button 
        className="btn btn--primary"
        onClick={handleResolve}
        disabled={isLoading}
            >
            <i className="material-icons">
            {isLoading ? 'hourglass_empty' : 'schedule'}
        </i>
            {isLoading ? 'Resolving...' : 'Resolve'}
        </button>
            </div>
            </div>

            <div className="resolve__anchors">
            <div className="resolve__anchors-header">
            <h3 className="resolve__anchors-title">Select Anchors</h3>
            <div className="resolve__anchors-controls">
            <button 
        className="btn btn--secondary"
        onClick={handleSelectAll}
            >
            Select All
        </button>
            <button 
        className="btn btn--secondary"
        onClick={handleDeselectAll}
            >
            Deselect All
        </button>
            </div>
            </div>
            <div className="resolve__anchors-grid">
            {Object.entries(anchors || {}).map(([label, anchor]) => (
                <div key={label} className="resolve__anchor-item">
                    <label className="resolve__anchor-label">
                    <input
                type="checkbox"
                className="resolve__anchor-checkbox"
                checked={selectedAnchors.has(label)}
                onChange={() => toggleAnchor(label)}
                    />
                    <span className="resolve__anchor-name">{anchor.name}</span>
                    </label>
                    </div>
            ))}
        </div>
            </div>

            {results && (
    <div className="resolve__results" style={{ display: 'block' }}>
        <div className="resolve__result-header">
            <h3>Resolved Date: {formatDate(results.resolved_date)}</h3>
        </div>
        <div className="resolve__result-grid">
            {Object.entries(results.results).map(([label, result]) => (
                <div key={label} className="resolve__result-card">
                    <div className="resolve__result-title">{result.name}</div>
                    <div className="resolve__result-formats">
                        {result.formats.map((format, index) => {
                            // Create a container div with the HTML content
                            return (
                                <div 
                                    key={index} 
                                    className="resolve__result-format"
                                >
                                    <div dangerouslySetInnerHTML={{ __html: format }} />
                                </div>
                            );
                        })}
                    </div>
                </div>
            ))}
        </div>
    </div>
)}

        </div>
    );

};
