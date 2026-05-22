# Empty State Illustrations

**Status:** Placeholder. Tier 3 currently uses Lucide icons as empty state visuals (fallback per spec risk mitigation).

To switch to undraw.co illustrations:
1. Download SVGs from https://undraw.co/illustrations (color picker → `#1e3a8a`)
2. Save here: `welcome.svg`, `locked.svg`, `chat-empty.svg`, `progress-empty.svg`, `achievements-empty.svg`, `upload.svg`
3. Update `EmptyState` usage in pages (Dashboard, Modules, Chat, Progress, Achievements, Admin) from `icon={LucideIcon}` to `illustration={importedSvg}`.
