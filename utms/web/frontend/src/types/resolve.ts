export interface ResolveResult {
    resolved_date: string;
    results: {
        [key: string]: {
            name: string;
            formats: string[];
        };
    };
}

export interface ResolveRequest {
    input: string;
    anchors: string[];
}
