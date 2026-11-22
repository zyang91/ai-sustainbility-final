"""Planning themes, scored by similarity to short theme descriptions.

Each theme is described by a few plain sentences of the kind a planner would
write. A passage's score for a theme is the cosine similarity between the
passage and the mean of those descriptions. A passage is assigned to the
theme it scores highest on, if that score reaches THRESHOLD and beats the
second theme by MARGIN; otherwise it is "other". Shares are then counted per
plan and per era.

The themes are the ones Vision 1.5 names, plus student housing, planning
process, campus design and athletics, which turned out to be large in the
corpus: in a first reading check, passages about building siting, campus
edges and the field house were all being filed under open space. The descriptions are
written in general terms and do not quote the plans.
"""
import numpy as np

from .embed import encode

THEMES = {
    "Parking and traffic": [
        "parking lots, parking garages and the number of parking spaces",
        "automobile traffic, vehicular circulation and streets for cars",
        "commuting to campus by car, transit and bus",
    ],
    "Campus expansion and land": [
        "the university acquires land and expands the campus into new blocks",
        "redevelopment areas and the purchase of property for university expansion",
        "the boundaries of the campus move outward into the surrounding city",
    ],
    "Land use and density": [
        "land use designations for academic, residential and commercial areas",
        "building density, floor area ratio and building coverage",
        "zoning and the intensity of development on campus sites",
    ],
    "Pedestrian circulation": [
        "pedestrian walkways, footpaths and walking routes across campus",
        "closing streets to traffic to create a pedestrian campus",
        "separating pedestrians from vehicles at crossings",
    ],
    "Open space and landscape": [
        "open space, green lawns, trees and planting on campus",
        "landscape design of courtyards, plazas and parks",
        "trees, shrubs, grass and paving in the outdoor spaces of the campus",
    ],
    "Campus design and character": [
        "the architectural character and image of the campus and its buildings",
        "siting of buildings, building heights and the edges of the campus",
        "urban design guidelines for the form of new buildings",
    ],
    "Athletics and recreation": [
        "athletic fields, gymnasiums and recreation facilities",
        "sports facilities, the field house and the stadium",
        "recreation space for students and intramural sports",
    ],
    "Academic facilities": [
        "new buildings for academic departments, laboratories and libraries",
        "space needs of schools and research facilities",
        "classrooms and teaching facilities for the faculties",
    ],
    "Student housing": [
        "student housing, dormitories and residence halls",
        "housing for undergraduate and graduate students on campus",
        "college houses and residential life",
    ],
    "Neighborhood and city": [
        "relations between the university and the surrounding West Philadelphia neighborhoods",
        "the community, residents and city government around the campus",
        "commercial services and retail for the university community and its neighbors",
    ],
    "Planning process": [
        "the planning process, committees and review of the development plan",
        "objectives and principles that guide the campus plan",
        "implementation, phasing and priorities of the plan",
    ],
    "Sustainability and energy": [
        "energy use, sustainability and green buildings",
        "stormwater management and environmental performance",
        "reducing carbon emissions and resource consumption",
    ],
}
THRESHOLD = 0.60     # below this a passage matches no theme well (25% of passages)
MARGIN = 0.0


def theme_vectors() -> np.ndarray:
    rows = []
    for descriptions in THEMES.values():
        v = encode(descriptions, query=True).mean(0)
        rows.append(v / np.linalg.norm(v))
    return np.stack(rows)


def scores(vectors: np.ndarray) -> np.ndarray:
    """passages x themes cosine similarity."""
    return vectors @ theme_vectors().T


def assign(sim: np.ndarray, threshold: float = None, margin: float = None) -> list[str]:
    threshold = THRESHOLD if threshold is None else threshold
    margin = MARGIN if margin is None else margin
    names = list(THEMES)
    order = np.argsort(-sim, axis=1)
    out = []
    for i, row in enumerate(sim):
        a, b = order[i, 0], order[i, 1]
        out.append(names[a] if row[a] >= threshold and row[a] - row[b] >= margin else "Other")
    return out
