export interface ConfigValue {
  value: any;
  is_dynamic: boolean;
  original?: string | null;
}

export type ConfigData = Record<string, ConfigValue>;

export interface ConfigChoices {
  [key: string]: string[];
}
