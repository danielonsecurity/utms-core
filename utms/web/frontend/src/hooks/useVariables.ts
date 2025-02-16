import { useQuery } from '@tanstack/react-query'
import { variablesApi } from '../api/variables'

export const useVariables = () => {
  return useQuery(['variables'], variablesApi.getVariables)
}
