from fastapi import APIRouter

router = APIRouter(tags=["resources"])

RESOURCES = [
    {
        "category": "Understanding cravings",
        "items": [
            {"title": "Why cravings peak and fade", "summary": "Most cravings pass within 3-5 minutes whether or not you act on them — understanding the curve makes waiting easier."},
            {"title": "The role of nicotine withdrawal", "summary": "What's happening physically in the first two weeks, and why it gets easier."},
        ],
    },
    {
        "category": "Handling triggers",
        "items": [
            {"title": "Naming your top 3 triggers", "summary": "Specific, named triggers are easier to plan around than vague ones."},
            {"title": "Building distance from a cue", "summary": "Small environmental changes — a different chair, a different route — that reduce automatic urges."},
        ],
    },
    {
        "category": "Managing stress",
        "items": [
            {"title": "Paced breathing basics", "summary": "A simple 4-7-8 pattern you can do anywhere in under two minutes."},
            {"title": "Stress vs. craving — telling them apart", "summary": "Sometimes what feels like a craving is stress looking for its usual outlet."},
        ],
    },
    {
        "category": "Preparing for difficult moments",
        "items": [
            {"title": "Making a plan before you need it", "summary": "Deciding your response to a hard moment ahead of time, while calm."},
            {"title": "What to do right after a slip", "summary": "Practical next steps that don't involve starting over from zero."},
        ],
    },
    {
        "category": "Supporting someone else",
        "items": [
            {"title": "What actually helps a partner or friend quit", "summary": "Support that helps versus support that adds pressure."},
        ],
    },
    {
        "category": "Building a smoke-free environment",
        "items": [
            {"title": "Removing cues from home and car", "summary": "A one-time setup pass that removes daily temptation points."},
        ],
    },
    {
        "category": "When to seek professional support",
        "items": [
            {"title": "Signs it's time to involve a doctor", "summary": "Nicotine replacement therapy, prescription options, and when they're worth discussing."},
        ],
    },
    {
        "category": "Emergency or crisis resources",
        "items": [
            {"title": "If you're in crisis right now", "summary": "This app is not an emergency service. If you are in immediate distress, please contact a local crisis line or emergency services."},
        ],
    },
]


@router.get("/resources")
def get_resources():
    return {"categories": RESOURCES}
