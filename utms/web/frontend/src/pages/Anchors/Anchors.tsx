import { useState, useEffect } from 'react';
import { anchorsApi } from '../../api/anchorsApi';
import { Anchor, CreateAnchorData } from '../../types/anchors';
import { AnchorCard } from '../../components/anchors/AnchorCard';
import { CreateAnchorModal } from '../../components/anchors/CreateAnchorModal';
import Decimal from 'decimal.js';

export const Anchors = () => {
    const [anchors, setAnchors] = useState<Record<string, Anchor>>({});
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [filters, setFilters] = useState<Set<string>>(new Set());
    const [labelSearch, setLabelSearch] = useState('');
    const [nameSearch, setNameSearch] = useState('');
    const [sortType, setSortType] = useState('value-asc');

    useEffect(() => {
        loadAnchors();
    }, []);

    useEffect(() => {
        const url = new URL(window.location.href);
        const filterParam = url.searchParams.get('filters');
        if (filterParam) {
            setFilters(new Set(filterParam.split(',')));
        }
    }, []);

    useEffect(() => {
        const url = new URL(window.location.href);
        if (filters.size > 0) {
            url.searchParams.set('filters', Array.from(filters).join(','));
        } else {
            url.searchParams.delete('filters');
        }
        window.history.pushState({}, '', url);
    }, [filters]);

    const loadAnchors = async () => {
        try {
            const data = await anchorsApi.getAnchors();
            setAnchors(data);
        } catch (error) {
            alert('Failed to load anchors: ' + (error as Error).message);
        }
    };

    const handleCreateAnchor = async (data: CreateAnchorData) => {
        await anchorsApi.createAnchor(data);
        loadAnchors();
    };

    const handleDeleteAnchor = async (label: string) => {
        if (window.confirm(`Are you sure you want to delete anchor "${label}"?`)) {
            await anchorsApi.deleteAnchor(label);
            loadAnchors();
        }
    };

    const toggleFilter = (group: string) => {
        setFilters(prev => {
            const next = new Set(prev);
            if (next.has(group)) {
                next.delete(group);
            } else {
                next.add(group);
            }
            return next;
        });
    };

    const filteredAndSortedAnchors = Object.entries(anchors)
        .filter(([label, anchor]) => {
            const matchesLabel = label.toLowerCase().includes(labelSearch.toLowerCase());
            const matchesName = anchor.name.toLowerCase().includes(nameSearch.toLowerCase());
            const matchesFilters = filters.size === 0 || 
                Array.from(filters).every(filter => anchor.groups.includes(filter));
            return matchesLabel && matchesName && matchesFilters;
        })
        .sort(([labelA, anchorA], [labelB, anchorB]) => {
            switch(sortType) {
                case 'value-asc':
                    return new Decimal(anchorA.value).minus(new Decimal(anchorB.value)).toNumber();
                case 'value-desc':
                    return new Decimal(anchorB.value).minus(new Decimal(anchorA.value)).toNumber();
                case 'label-asc':
                    return labelA.localeCompare(labelB);
                case 'label-desc':
                    return labelB.localeCompare(labelA);
                default:
                    return 0;
            }
        });

    return (
        <div className="anchors">
            <div className="anchors__controls">
                <button className="btn btn--create" onClick={() => setIsModalOpen(true)}>
                    <i className="material-icons">add</i>Create Anchor
                </button>

                <div className="anchors__search">
                    <div className="anchors__search-field">
                        <i className="material-icons anchors__search-icon">label</i>
                        <input
                            type="text"
                            className="anchors__search-input"
                            placeholder="Search by label..."
                            value={labelSearch}
                            onChange={e => setLabelSearch(e.target.value)}
                        />
                    </div>
                    <div className="anchors__search-field">
                        <i className="material-icons anchors__search-icon">title</i>
                        <input
                            type="text"
                            className="anchors__search-input"
                            placeholder="Search by name..."
                            value={nameSearch}
                            onChange={e => setNameSearch(e.target.value)}
                        />
                    </div>
                </div>

                <div className="anchors__controls-row">
                    <div className="anchors__filters">
                        <div className="anchors__filters-label">Active filters:</div>
                        <div className="filters__tags">
                            {Array.from(filters).map(filter => (
                                <div key={filter} className="filter-tag">
                                    {filter}
                                    <i 
                                        className="material-icons remove-filter" 
                                        onClick={() => toggleFilter(filter)}
                                    >
                                        close
                                    </i>
                                </div>
                            ))}
                        </div>
                        <button 
                            className="btn btn--clear" 
                            onClick={() => setFilters(new Set())}
                            disabled={filters.size === 0}
                        >
                            Clear All
                        </button>
                    </div>

                    <div className="sort">
                        <select 
                            className="sort__select"
                            value={sortType}
                            onChange={e => setSortType(e.target.value)}
                        >
                            <option value="value-asc">Value ↑</option>
                            <option value="value-desc">Value ↓</option>
                            <option value="label-asc">Label A-Z</option>
                            <option value="label-desc">Label Z-A</option>
                        </select>
                    </div>
                </div>
            </div>

            <div className="anchors__grid">
                {filteredAndSortedAnchors.map(([label, anchor]) => (
                    <AnchorCard
                        key={label}
                        label={label}
                        anchor={anchor}
                        onDelete={handleDeleteAnchor}
                        onUpdate={loadAnchors}
                        onGroupClick={toggleFilter}
                    />
                ))}
            </div>

            <CreateAnchorModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onCreate={handleCreateAnchor}
            />
        </div>
    );
};
