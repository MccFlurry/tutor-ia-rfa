import { create } from 'zustand'

interface ModuleProgress {
  id: number
  title: string
  pct: number
  completed: number
  total: number
}

interface ProgressState {
  overallPct: number
  modules: ModuleProgress[]
  setProgress: (overall: number, modules: ModuleProgress[]) => void
}

export const useProgressStore = create<ProgressState>((set) => ({
  overallPct: 0,
  modules: [],
  setProgress: (overall, modules) => set({ overallPct: overall, modules }),
}))
