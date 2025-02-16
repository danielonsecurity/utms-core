export interface Anchor {
  label: string;
  name: string;
  value: string;
  value_original?: string;
  name_original?: string;
  groups: string[];
  uncertainty?: {
    absolute: string;
    relative: string;
    confidence_95?: [string, string];
  };
  formats?: Array<{
    format?: string;
    units?: string[];
    options?: string;
  }>;
}

export interface CreateAnchorData {
  label: string;
  name: string;
  value: string;
  groups: string[];
}

export interface UpdateAnchorData {
  label?: string;
  name?: string;
  value?: string;
  groups?: string[];
}
