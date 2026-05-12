# EPL SCOUT 25/26

Premier League Analytics Desktop Application built with Python + Flet (Material Design 3).

## Architecture

This application follows a **strict modular architecture** with loose coupling between layers:

```
/epl_scout/
├── data/               # CSV data files (clubs, players, stats)
├── models/             # Pure data structures (entities)
│   ├── __init__.py
│   └── entities.py     # Dataclass definitions
├── core/               # Business Logic & Data Access
│   ├── __init__.py
│   ├── database.py     # SQLite operations (returns only dataclasses)
│   └── algorithms.py   # Scouting algorithms (pure functions)
├── ui/                 # Presentation Layer
│   ├── __init__.py
│   ├── components.py   # Reusable UI components
│   └── views.py        # Complete view implementations
└── main.py             # Application coordinator
```

## Key Architectural Principles

### 1. Loose Coupling
- **UI Layer** contains ZERO business logic or database queries
- **Core Layer** operates purely on data structures (no UI dependencies)
- **Models Layer** is pure dataclasses with no external dependencies

### 2. Data Boundary
- Communication between layers uses only:
  - Standard Python types (Dict, List, Tuple)
  - Dataclass objects from `models/entities.py`
- No raw SQL cursors exposed to upper layers
- No UI objects passed to business logic

### 3. Database Integrity
- Normalized schema with proper Foreign Keys
- Referential integrity enforced via SQLite constraints
- No flat/denormalized structures

## Installation

```bash
pip install flet pandas numpy matplotlib
```

## Running the Application

```bash
cd /workspace/epl_scout
python main.py
```

## Data Files

The application loads data from CSV files in the `data/` directory:

- `clubs.csv` - 20 Premier League clubs (tab-separated)
- `playersinfo.csv` - Player基本信息 (tab-separated)
- `playerstats.csv` - Gameweek statistics (comma-separated)

## Features

### Home View
- Bento grid navigation to all sections
- Quick stats overview

### Players Hub
- Filter by position, club, market value
- Real-time search with debounce
- Paginated results table (25 per page)
- Click to view player dashboard

### Scouting
- Define ideal player profile using percentile sliders
- Position group selection
- Hard filters (age, value, contract)
- Cosine similarity-based matching algorithm
- Results sorted by match score

### Watchlist
- Add/remove players
- Star rating (1-5)
- Inline notes editing
- Search and filter capabilities

### Player Dashboard
- **Overview Tab**: Player info, performance radar, season stats
- **GW Records Tab**: Gameweek-by-gameweek statistics
- **Performance Tab**: Visual charts (minutes, goals vs xG, assists vs xA, ICT)
- Similar players modal

## Color Scheme

| Role | Color |
|------|-------|
| Background | #1A1A1A |
| Surface | #2D2D2D |
| Primary (Accent) | #FFD700 (Yellow) |
| Text Primary | #FFFFFF |
| Text Secondary | #B0B0B0 |
| Success | #4CAF50 |
| Error | #F44336 |

## Technical Specifications

- **Resolution**: Fixed 1280x800px (16:10 ratio)
- **Framework**: Flet 0.20+ (Material Design 3)
- **Database**: SQLite (local file)
- **Data Processing**: Pandas, NumPy
- **Visualization**: Matplotlib (rendered to base64 for Flet)

## Algorithms

### Similar Players
1. Filter by position group
2. Z-score normalization of key metrics
3. Cosine similarity calculation
4. Match Score = ((similarity + 1) / 2) * 100
5. Return top 5 matches

### Scouting Search
1. Calculate league percentiles for target metrics
2. Score = 100 - abs(player_percentile - target_percentile)
3. Apply hard filters (age, value, contract)
4. Sort by average match score

## State Management

- **Global State**: Current player ID, caches (similar players, charts)
- **View State**: Filters, search terms, pagination
- All state managed in `EPLScoutApp` coordinator class

## Error Handling

- Database errors → Snackbar with error message
- Empty results → Empty state component with CTA
- Image loading failures → Default avatar placeholder
- Chart rendering errors → Placeholder text

## Performance Optimizations

- Lazy load player stats only when needed
- 300ms debounce on search input
- Cache similar players results
- Cache chart renders by player_id
- Use scrollable Columns instead of long lists

## Development Notes

### Adding New Features
1. Add data fields to `models/entities.py`
2. Implement logic in `core/` layer
3. Create UI components in `ui/components.py`
4. Build views in `ui/views.py` with callback parameters
5. Wire up in `main.py` event handlers

### Modifying Existing Features
- Change UI appearance → Edit `ui/components.py` or `ui/views.py`
- Change business logic → Edit `core/algorithms.py`
- Change data schema → Edit `models/entities.py` and `core/database.py`

### Anti-Patterns to Avoid
- ❌ Don't put SQL queries in UI layer
- ❌ Don't pass Flet objects to core layer
- ❌ Don't mix presentation logic with business logic
- ❌ Don't create circular imports between layers

## License

Internal use only.
