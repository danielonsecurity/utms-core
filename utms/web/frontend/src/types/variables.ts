export interface Variable {
  value: string;
  value_original: string;
  type: string;
}

export interface VariablesState {
  variables: Record<string, Variable>;
  isLoading: boolean;
  error: Error | null;
}
