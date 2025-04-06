import { useState, useEffect, useCallback } from "react";
import { unitsApi } from "../../api/unitsApi";
import { Unit, CreateUnitData } from "../../types/units";
import { UnitCard } from "../../components/units/UnitCard";
import { CreateUnitModal } from "../../components/units/CreateUnitModal";
import Decimal from "decimal.js";

export const Units = () => {
  const [units, setUnits] = useState<Record<string, Unit>>({});
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [filters, setFilters] = useState<Set<string>>(new Set());
  const [labelSearch, setLabelSearch] = useState("");
  const [nameSearch, setNameSearch] = useState("");
  const [sortType, setSortType] = useState("value-asc");

  useEffect(() => {
    // Load filters from URL on mount
    const url = new URL(window.location.href);
    const filterParam = url.searchParams.get("filters");
    if (filterParam) {
      setFilters(new Set(filterParam.split(",")));
    }
  }, []);

  // Update URL when filters change
  useEffect(() => {
    const url = new URL(window.location.href);
    if (filters.size > 0) {
      url.searchParams.set("filters", Array.from(filters).join(","));
    } else {
      url.searchParams.delete("filters");
    }
    window.history.pushState({}, "", url);
  }, [filters]);

  const loadUnits = useCallback(async () => {
    try {
      const data = await unitsApi.getUnits();
      console.log(data);
      setUnits(data);
    } catch (error) {
      alert("Failed to load units: " + (error as Error).message);
    }
  }, []);

  useEffect(() => {
    loadUnits();
  }, [loadUnits]);

  const handleCreateUnit = async (data: CreateUnitData) => {
    await unitsApi.createUnit(data);
    loadUnits();
  };

  const handleDeleteUnit = async (label: string) => {
    if (window.confirm(`Are you sure you want to delete unit "${label}"?`)) {
      await unitsApi.deleteUnit(label);
      loadUnits();
    }
  };

  const toggleFilter = (group: string) => {
    setFilters((prev) => {
      const next = new Set(prev);
      if (next.has(group)) {
        next.delete(group);
      } else {
        next.add(group);
      }
      return next;
    });
  };

  const filteredAndSortedUnits = Object.entries(units)
    .filter(([label, unit]) => {
      const matchesLabel = label
        .toLowerCase()
        .includes(labelSearch.toLowerCase());
      const matchesName = unit.name
        .toLowerCase()
        .includes(nameSearch.toLowerCase());
      const matchesFilters =
        filters.size === 0 ||
        Array.from(filters).every((filter) => unit.groups.includes(filter));
      return matchesLabel && matchesName && matchesFilters;
    })
    .sort(([labelA, unitA], [labelB, unitB]) => {
      switch (sortType) {
        case "value-asc":
          return new Decimal(unitA.value)
            .minus(new Decimal(unitB.value))
            .toNumber();
        case "value-desc":
          return new Decimal(unitB.value)
            .minus(new Decimal(unitA.value))
            .toNumber();
        case "label-asc":
          return labelA.localeCompare(labelB);
        case "label-desc":
          return labelB.localeCompare(labelA);
        default:
          return 0;
      }
    });

  return (
    <div className="units">
      <div className="units__controls">
        <button
          className="btn btn--create"
          onClick={() => setIsModalOpen(true)}
        >
          <i className="material-icons">add</i>Create Unit
        </button>

        <div className="units__search">
          <div className="units__search-field">
            <i className="material-icons units__search-icon">label</i>
            <input
              type="text"
              className="units__search-input"
              placeholder="Search by label..."
              value={labelSearch}
              onChange={(e) => setLabelSearch(e.target.value)}
            />
          </div>
          <div className="units__search-field">
            <i className="material-icons units__search-icon">title</i>
            <input
              type="text"
              className="units__search-input"
              placeholder="Search by name..."
              value={nameSearch}
              onChange={(e) => setNameSearch(e.target.value)}
            />
          </div>
        </div>

        <div className="units__controls-row">
          <div className="units__filters">
            <div className="units__filters-label">Active filters:</div>
            <div className="filters__tags">
              {Array.from(filters).map((filter) => (
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
              onChange={(e) => setSortType(e.target.value)}
            >
              <option value="value-asc">Value ↑</option>
              <option value="value-desc">Value ↓</option>
              <option value="label-asc">Label A-Z</option>
              <option value="label-desc">Label Z-A</option>
            </select>
          </div>
        </div>
      </div>

      <div className="units__grid">
        {filteredAndSortedUnits.map(([label, unit]) => (
          <UnitCard
            key={label}
            label={label}
            unit={unit}
            onDelete={handleDeleteUnit}
            onUpdate={loadUnits}
            onGroupClick={(group) => toggleFilter(group)}
          />
        ))}
      </div>

      <CreateUnitModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onCreate={handleCreateUnit}
      />
    </div>
  );
};
