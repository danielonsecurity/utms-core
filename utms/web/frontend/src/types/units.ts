export interface Unit {
  label: string;
  name: string;
  value: string;
  groups: string[];
}

export interface CreateUnitData {
  label: string;
  name: string;
  value: string;
  groups: string[];
}

export interface UpdateUnitField {
  value: string | string[];
}

export interface UnitCardProps {
  unit: Unit;
  label: string;
  onDelete: (label: string) => void;
  onUpdate: () => void;
  onGroupClick?: (group: string) => void;
}

export interface FilterState {
  filters: Set<string>;
  labelSearch: string;
  nameSearch: string;
  sortType: 'value-asc' | 'value-desc' | 'label-asc' | 'label-desc';
}
