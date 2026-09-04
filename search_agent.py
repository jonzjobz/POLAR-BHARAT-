import pandas as pd
import re
import os
import base64

from google import genai


# ============================================================
# SETTINGS
# ============================================================

MAX_RESULTS = 10

CSV_FILES = [
    "arctic_projects.csv",
    "arctic_team_members.csv",
    "npdc_datasets.csv",
    "npdc_prototype.csv",
    "npdc_station_metadata.csv",
    "polar_images.csv",
    "polar_publications.csv",
    "polar_southern_ocean_reports.csv"
]


# ============================================================
# GEMINI SETTINGS
# ============================================================

# IMPORTANT:
# We use the model that your Gemini API currently supports.
#
# You can override this from the terminal with:
#
# set GEMINI_MODEL=gemini-3.6-flash
#
# or another model available to your API key.

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.6-flash"
)

GEMINI_IMAGE_MODEL = os.getenv(
    "GEMINI_IMAGE_MODEL",
    "gemini-3.1-flash-image"
)

MAX_GEMINI_ATTEMPTS = 1


# ============================================================
# GEMINI SETUP
# ============================================================

client = None

try:

    api_key = os.getenv(
        "GEMINI_API_KEY"
    )

    if api_key:

        client = genai.Client(
            api_key=api_key
        )

        print(
            "Gemini client initialized successfully."
        )

    else:

        print(
            "\nWARNING: GEMINI_API_KEY not found."
        )

        print(
            "AI generation will use fallback content."
        )

except Exception as e:

    print(
        "\nGemini setup failed:"
    )

    print(e)

    client = None


# ============================================================
# LOAD ALL CSV FILES
# ============================================================

all_records = []


for filename in CSV_FILES:

    try:

        df_temp = pd.read_csv(
            filename,
            encoding="utf-8",
            on_bad_lines="skip"
        )

        print(
            f"Loaded {filename}: "
            f"{len(df_temp)} records"
        )

        for _, row in df_temp.iterrows():

            record = row.to_dict()

            record["_source_file"] = filename

            all_records.append(
                record
            )

    except FileNotFoundError:

        print(
            f"WARNING: {filename} not found."
        )

    except Exception as e:

        print(
            f"WARNING: Could not load "
            f"{filename}: {e}"
        )


if all_records:

    df = pd.DataFrame(
        all_records
    )

else:

    df = pd.DataFrame()


print(
    "\nTotal records loaded:",
    len(df)
)


# ============================================================
# HELPER
# ============================================================

def clean_text(value):

    if value is None:

        return ""

    try:

        if pd.isna(value):

            return ""

    except Exception:

        pass

    return str(value).strip()


# ============================================================
# SOURCE
# ============================================================

def get_source(row):

    source_file = clean_text(
        row.get(
            "_source_file",
            ""
        )
    ).lower()

    if "npdc" in source_file:

        return "NPDC"

    if (
        "arctic" in source_file
        or "publication" in source_file
        or "southern" in source_file
        or "image" in source_file
    ):

        return "NCPOR"

    return "Primary Dataset"


# ============================================================
# TITLE
# ============================================================

def get_title(row):

    possible_columns = [

        "title",
        "project",
        "project_title",
        "name",
        "publication",
        "report_title",
        "dataset_title",
        "station_name"

    ]

    for column in possible_columns:

        if column in row.index:

            value = clean_text(
                row.get(
                    column,
                    ""
                )
            )

            if value:

                return value

    return ""


# ============================================================
# CONTENT TYPE
# ============================================================

def get_content_type(row):

    content_type = clean_text(
        row.get(
            "content_type",
            ""
        )
    )

    if content_type:

        return content_type

    # Infer type from source file if column doesn't exist

    filename = clean_text(
        row.get(
            "_source_file",
            ""
        )
    ).lower()

    if "publication" in filename:

        return "Publication"

    if "image" in filename:

        return "Image"

    if "report" in filename:

        return "Expedition Report"

    if "dataset" in filename:

        return "Dataset"

    if "project" in filename:

        return "Project"

    if "station" in filename:

        return "Station Metadata"

    return "Research Record"


# ============================================================
# CATEGORY
# ============================================================

def get_category(row):

    possible_columns = [

        "category",
        "research_area",
        "discipline"

    ]

    for column in possible_columns:

        value = clean_text(
            row.get(
                column,
                ""
            )
        )

        if value:

            return value

    return ""


# ============================================================
# TOPIC
# ============================================================

def get_topic(row):

    possible_columns = [

        "topic",
        "subcategory",
        "research_topic",
        "parameter"

    ]

    for column in possible_columns:

        value = clean_text(
            row.get(
                column,
                ""
            )
        )

        if value:

            return value

    return ""


# ============================================================
# STATION
# ============================================================

def get_station(row):

    possible_columns = [

        "station",
        "station_name",
        "location"

    ]

    for column in possible_columns:

        value = clean_text(
            row.get(
                column,
                ""
            )
        )

        if value:

            return value

    return ""


# ============================================================
# URL
# ============================================================

def get_url(row):

    possible_columns = [

        "metadata_url",
        "url",
        "source_url",
        "link"

    ]

    for column in possible_columns:

        value = clean_text(
            row.get(
                column,
                ""
            )
        )

        if (
            value
            and value.startswith("http")
        ):

            return value

    return ""


# ============================================================
# FULL SEARCHABLE TEXT
# ============================================================

def get_full_text(row):

    text_parts = []

    for column in row.index:

        value = clean_text(
            row.get(
                column,
                ""
            )
        )

        if value:

            text_parts.append(
                value
            )

    return " ".join(
        text_parts
    ).lower()


# ============================================================
# SEARCH ENGINE
# ============================================================

def search_records(query):

    query = query.lower().strip()

    if not query:

        return []

    # --------------------------------------------------------
    # Extract words
    # --------------------------------------------------------

    words = re.findall(
        r"[a-zA-Z]+",
        query
    )

    # --------------------------------------------------------
    # Stop words
    # --------------------------------------------------------

    stop_words = {

        "what",
        "is",
        "are",
        "the",
        "of",
        "in",
        "on",
        "for",
        "and",
        "how",
        "does",
        "do",
        "about",
        "tell",
        "me",
        "can",
        "with",
        "from",
        "to",
        "this",
        "that",
        "please",
        "give",
        "show",
        "find",
        "research",
        "information",
        "some",
        "more",
        "write",
        "make",
        "create",
        "content",
        "article",
        "post",
        "social",
        "media",
        "website",
        "short",
        "outreach",
        "could",
        "would",
        "you",
        "your",
        "i",
        "we",
        "our",
        "my",
        "explain",
        "generate"

    }

    keywords = [

        word

        for word in words

        if (
            word not in stop_words
            and len(word) > 2
        )

    ]

    keywords = list(
        dict.fromkeys(
            keywords
        )
    )

    scored_records = []

    # --------------------------------------------------------
    # Score every record
    # --------------------------------------------------------

    for index, row in df.iterrows():

        full_text = get_full_text(
            row
        )

        title = get_title(
            row
        ).lower()

        score = 0

        # Exact query

        if query in full_text:

            score += 30

        matched_keywords = 0

        for word in keywords:

            if word in title:

                score += 12

                matched_keywords += 1

            elif word in full_text:

                score += 3

                matched_keywords += 1

        # Multiple keyword bonus

        if matched_keywords >= 2:

            score += (
                matched_keywords * 2
            )

        if score > 0:

            scored_records.append(
                (
                    score,
                    index,
                    row
                )
            )

    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    scored_records.sort(
        key=lambda x: x[0],
        reverse=True
    )

    # --------------------------------------------------------
    # Remove duplicate titles
    # --------------------------------------------------------

    unique_results = []

    seen_titles = set()

    for item in scored_records:

        score, index, row = item

        title = get_title(
            row
        )

        title_key = title.lower().strip()

        if not title_key:

            title_key = (
                f"record-{index}"
            )

        if title_key not in seen_titles:

            seen_titles.add(
                title_key
            )

            unique_results.append(
                item
            )

        if len(unique_results) >= MAX_RESULTS:

            break

    return unique_results


# ============================================================
# CONTENT INTENT
# ============================================================

def detect_content_intent(query):

    query_lower = query.lower()

    requested = []

    social_words = [

        "social media",
        "instagram",
        "linkedin",
        "facebook",
        "tweet",
        "twitter",
        "social post",
        "caption",
        "reel caption"

    ]

    article_words = [

        "article",
        "website article",
        "blog",
        "website content",
        "web article",
        "write an article",
        "write article"

    ]

    short_words = [

        "short post",
        "short outreach",
        "outreach post",
        "short content",
        "announcement",
        "brief post"

    ]

    for word in social_words:

        if word in query_lower:

            requested.append(
                "social"
            )

            break

    for word in article_words:

        if word in query_lower:

            requested.append(
                "article"
            )

            break

    for word in short_words:

        if word in query_lower:

            requested.append(
                "short"
            )

            break

    if requested:

        return list(
            dict.fromkeys(
                requested
            )
        )

    return [
        "article",
        "social",
        "short"
    ]


# ============================================================
# RESEARCH ANALYSIS
# ============================================================

def analyze_records(
    results,
    query
):

    if not results:

        return None

    # --------------------------------------------------------
    # SOURCES
    # --------------------------------------------------------

    sources = {}

    for score, index, row in results:

        source = get_source(
            row
        )

        sources[source] = (
            sources.get(
                source,
                0
            ) + 1
        )

    # --------------------------------------------------------
    # CONTENT TYPES
    # --------------------------------------------------------

    content_types = {}

    for score, index, row in results:

        content_type = get_content_type(
            row
        )

        content_types[
            content_type
        ] = (
            content_types.get(
                content_type,
                0
            ) + 1
        )

    # --------------------------------------------------------
    # CATEGORIES
    # --------------------------------------------------------

    categories = {}

    for score, index, row in results:

        category = get_category(
            row
        )

        if category:

            categories[category] = (
                categories.get(
                    category,
                    0
                ) + 1
            )

    sorted_categories = sorted(
        categories.items(),
        key=lambda x: x[1],
        reverse=True
    )

    # --------------------------------------------------------
    # TOPICS
    # --------------------------------------------------------

    topics = {}

    for score, index, row in results:

        topic = get_topic(
            row
        )

        if topic:

            topics[topic] = (
                topics.get(
                    topic,
                    0
                ) + 1
            )

    sorted_topics = sorted(
        topics.items(),
        key=lambda x: x[1],
        reverse=True
    )

    # --------------------------------------------------------
    # LOCATIONS
    # --------------------------------------------------------

    all_text = ""

    for score, index, row in results:

        all_text += (
            " " +
            get_full_text(row)
        )

    possible_locations = [

        "Arctic",
        "Antarctic",
        "Antarctica",
        "Svalbard",
        "Ny-Ålesund",
        "Himadri",
        "Maitri",
        "Bharati",
        "Dakshin Gangotri",
        "Schirmacher Oasis",
        "Southern Ocean",
        "Kongsfjorden",
        "East Antarctica",
        "West Antarctica",
        "Indian Ocean",
        "India"

    ]

    locations = []

    for location in possible_locations:

        if location.lower() in all_text:

            if location not in locations:

                locations.append(
                    location
                )

    # --------------------------------------------------------
    # EVIDENCE
    # --------------------------------------------------------

    evidence = []

    for score, index, row in results[:5]:

        evidence.append({

            "title": get_title(
                row
            ),

            "source": get_source(
                row
            ),

            "type": get_content_type(
                row
            ),

            "score": score

        })

    return {

        "sources": sources,

        "content_types": content_types,

        "categories": sorted_categories,

        "topics": sorted_topics,

        "locations": locations,

        "evidence": evidence

    }


# ============================================================
# PREPARE GEMINI EVIDENCE
# ============================================================

def prepare_gemini_evidence(
    results
):

    evidence_parts = []

    # IMPORTANT:
    # Only send the TOP 5 records to Gemini.
    # This makes generation much faster.

    for number, (
        score,
        index,
        row
    ) in enumerate(
        results[:5],
        start=1
    ):

        description = clean_text(
            row.get(
                "description",
                ""
            )
        )

        # Limit huge descriptions

        if len(description) > 700:

            description = (
                description[:700]
                + "..."
            )

        record = f"""
RECORD {number}

Source: {get_source(row)}
Type: {get_content_type(row)}
Title: {get_title(row)}
Category: {get_category(row)}
Topic: {get_topic(row)}
Station/Location: {get_station(row)}
Description: {description}
"""

        evidence_parts.append(
            record
        )

    return "\n".join(
        evidence_parts
    )


# ============================================================
# GEMINI CONTENT INSTRUCTIONS
# ============================================================

def build_content_instructions(
    requested_content
):

    instructions = ""

    if "article" in requested_content:

        instructions += """

WEBSITE ARTICLE

Create one concise website article.

Include:
- Title
- Introduction
- Main research
- Evidence from the records
- Geographic context
- Conclusion

Keep it suitable for a scientific
polar research outreach portal.
"""

    if "social" in requested_content:

        instructions += """

SOCIAL MEDIA POST

Create one engaging Instagram/LinkedIn post.

Include:
- Strong opening
- Main research information
- Evidence from the records
- Supported locations
- Relevant hashtags
"""

    if "short" in requested_content:

        instructions += """

SHORT OUTREACH POST

Create one concise 50-80 word outreach post.
"""

    return instructions


# ============================================================
# GEMINI GENERATION
# ============================================================

def generate_with_gemini(
    query,
    results,
    requested_content
):

    if client is None:

        return None

    if not results:

        return None

    evidence = prepare_gemini_evidence(
        results
    )

    content_instructions = (
        build_content_instructions(
            requested_content
        )
    )

    prompt = f"""
You are an AI content generator for
an Indian Polar Research Outreach Portal.

USER QUERY:
{query}

Use ONLY the supplied research records.

Rules:
- Do not use outside knowledge.
- Do not invent facts.
- Do not invent dates, numbers,
  researchers or institutions.
- Do not invent locations.
- Do not claim discoveries unless
  explicitly supported by the records.
- Clearly distinguish NCPOR and NPDC.
- If evidence is insufficient, do not guess.
- Generate ONLY the requested formats.

RESEARCH RECORDS:

{evidence}

REQUESTED FORMATS:

{", ".join(requested_content)}

{content_instructions}

Return only the final outreach content.
"""

    # ========================================================
    # FAST GEMINI REQUEST
    # ========================================================

    for attempt in range(
        1,
        MAX_GEMINI_ATTEMPTS + 1
    ):

        try:

            print(
                f"\nGemini attempt "
                f"{attempt}/"
                f"{MAX_GEMINI_ATTEMPTS}"
            )

            # ------------------------------------------------
            # CURRENT INTERACTIONS API
            # ------------------------------------------------

            interaction = (
                client.interactions.create(

                    model=GEMINI_MODEL,

                    input=prompt

                )
            )

            generated_text = getattr(
                interaction,
                "output_text",
                None
            )

            if generated_text:

                print(
                    "\nGemini generation successful."
                )

                print(
                    "Model:",
                    GEMINI_MODEL
                )

                return generated_text.strip()

            print(
                "Gemini returned empty output."
            )

        except Exception as e:

            print(
                "\nGemini generation failed:"
            )

            print(
                str(e)
            )

            return None

    return None


# ============================================================
# IMAGE PROMPT GENERATION
# ============================================================

def build_image_prompt(query, results):

    evidence = prepare_gemini_evidence(results)

    return f"""
Create a professional scientific editorial illustration
for an Indian Polar Research Outreach Portal.

Research topic:
{query}

Research evidence:
{evidence}

IMPORTANT:
- Do not invent scientific discoveries.
- Do not depict fictional experiments.
- Do not add unsupported scientific instruments.
- Do not add readable labels containing invented facts.
- The image should visually represent the research topic.
- It should look suitable for a government/scientific
  research outreach website.
- Use a clean, educational, realistic editorial style.
- Polar environment should be visually prominent.
- Avoid dramatic fantasy elements.
- Avoid misleading scientific claims.

Create a wide 16:9 hero image suitable for a website article.
"""


# ============================================================
# IMAGE GENERATION
# ============================================================

def generate_research_image(
    query,
    results
):

    if client is None:
        return None

    if not results:
        return None

    prompt = build_image_prompt(
        query,
        results
    )

    try:

        interaction = client.interactions.create(

            model=GEMINI_IMAGE_MODEL,

            input=prompt,

            response_format={
                "type": "image",
                "mime_type": "image/jpeg",
                "aspect_ratio": "16:9",
                "image_size": "1K"
            }

        )

        image_output = getattr(
            interaction,
            "output_image",
            None
        )

        if image_output is None:
            return None

        image_data = getattr(
            image_output,
            "data",
            None
        )

        if not image_data:
            return None

        image_bytes = base64.b64decode(
            image_data
        )

        return image_bytes

    except Exception as e:

        print(
            "\nImage generation failed:"
        )

        print(e)

        return None


# ============================================================
# STRUCTURED ARTICLE GENERATION
# ============================================================

def generate_article(
    query,
    results
):

    if client is None:
        return None

    if not results:
        return None

    evidence = prepare_gemini_evidence(
        results
    )

    prompt = f"""
You are the scientific content writer for
an Indian Polar Research Outreach Portal.

USER TOPIC:
{query}

RESEARCH EVIDENCE:
{evidence}

Create a professional public-facing article.

VERY IMPORTANT:
Use ONLY information contained in the supplied records.

Do NOT:
- invent facts
- invent statistics
- invent dates
- invent scientists
- invent institutions
- invent locations
- invent discoveries
- use outside scientific knowledge

The article should be understandable to a
college student or general public reader while
remaining scientifically responsible.

Return the article using EXACTLY this structure:

TITLE:
A clear and engaging article title.

SUBTITLE:
One sentence explaining the article.

INTRODUCTION:
2-3 paragraphs.

RESEARCH HIGHLIGHTS:
3-5 bullet points based only on the evidence.

MAIN STORY:
3-5 paragraphs explaining the research.

GEOGRAPHIC CONTEXT:
Explain the locations supported by the records.

WHY IT MATTERS:
Explain the importance only if supported
by the supplied records.

CONCLUSION:
One concise concluding paragraph.

SOURCE RECORDS:
List the titles of the research records used,
along with their source (NCPOR or NPDC).

IMAGE DESCRIPTION:
Write a short description for a scientific
hero image representing this article.
Do not invent facts.

Return ONLY these sections.
"""

    try:

        interaction = client.interactions.create(

            model=GEMINI_MODEL,

            input=prompt

        )

        generated_text = getattr(
            interaction,
            "output_text",
            None
        )

        if generated_text:

            return generated_text.strip()

    except Exception as e:

        print(
            "\nArticle generation failed:"
        )

        print(e)

    return None


# ============================================================
# FALLBACK CONTENT
# ============================================================

def fallback_outreach(
    query,
    results,
    requested_content
):

    titles = []

    for score, index, row in results:

        title = get_title(
            row
        )

        if (
            title
            and title not in titles
        ):

            titles.append(
                title
            )

    sources = []

    for score, index, row in results:

        source = get_source(
            row
        )

        if source not in sources:

            sources.append(
                source
            )

    source_text = " and ".join(
        sources
    )

    output_parts = []

    # ========================================================
    # ARTICLE
    # ========================================================

    if "article" in requested_content:

        article = f"""
## Website Article

### Exploring Indian Polar Research:
{query.title()}

Indian polar research covers a range
of scientific activities across Arctic
and Antarctic environments.

The retrieved {source_text} records
include research related to:

"""

        for title in titles[:5]:

            article += (
                f"- {title}\n"
            )

        article += """
    
### Source Note

This content is based only on the
retrieved research records.
No additional scientific findings
have been added.
"""

        output_parts.append(
            article
        )

    # ========================================================
    # SOCIAL
    # ========================================================

    if "social" in requested_content:

        social = """
## Social Media Post

🧊 Exploring India's Polar Research!

The retrieved NCPOR and NPDC records
highlight research across the
polar regions.

Some retrieved records include:

"""

        for title in titles[:3]:

            social += (
                f"🔬 {title}\n"
            )

        social += """

Explore India's polar research through
projects, scientific datasets,
publications and expedition records.

#PolarResearch #PolarScience
#NCPOR #NPDC #Arctic #Antarctica
"""

        output_parts.append(
            social
        )

    # ========================================================
    # SHORT
    # ========================================================

    if "short" in requested_content:

        short = f"""
## Short Outreach Post

Indian polar research spans diverse
scientific areas across the Arctic
and Antarctic. Retrieved records
include {", ".join(titles[:3])}.
Explore these research resources
through the NCPOR and NPDC archive.
"""

        output_parts.append(
            short
        )

    return "\n".join(
        output_parts
    ).strip()


# ============================================================
# PUBLIC FUNCTION FOR STREAMLIT
# ============================================================

def generate_outreach(
    query,
    results,
    requested_content=None
):

    if not results:

        return None

    if requested_content is None:

        requested_content = (
            detect_content_intent(
                query
            )
        )

    generated = generate_with_gemini(

        query,

        results,

        requested_content

    )

    if generated:

        return generated

    return fallback_outreach(

        query,

        results,

        requested_content

    )


# ============================================================
# CONSOLE TEST
# ============================================================

if __name__ == "__main__":

    print(
        "\n" + "=" * 65
    )

    print(
        "          POLAR OUTREACH ASSISTANT"
    )

    print(
        "=" * 65
    )

    while True:

        query = input(
            "\nAsk about polar research "
            "(type 'exit' to stop): "
        ).strip()

        if query.lower() == "exit":

            print(
                "\nGoodbye!"
            )

            break

        if not query:

            print(
                "Please enter a query."
            )

            continue

        requested_content = (
            detect_content_intent(
                query
            )
        )

        results = search_records(
            query
        )

        print(
            f"\nFound {len(results)} "
            f"relevant records."
        )

        for number, (
            score,
            index,
            row
        ) in enumerate(
            results,
            start=1
        ):

            print(
                "\n--------------------------------"
            )

            print(
                f"RESULT {number}"
            )

            print(
                "--------------------------------"
            )

            print(
                "Title:",
                get_title(row)
            )

            print(
                "Source:",
                get_source(row)
            )

            print(
                "Type:",
                get_content_type(row)
            )

            category = get_category(row)

            if category:

                print(
                    "Category:",
                    category
                )

            topic = get_topic(row)

            if topic:

                print(
                    "Topic:",
                    topic
                )

            station = get_station(row)

            if station:

                print(
                    "Station/Location:",
                    station
                )

            url = get_url(row)

            if url:

                print(
                    "URL:",
                    url
                )

            print(
                "Score:",
                score
            )

        analysis = analyze_records(
            results,
            query
        )

        if results:

            print(
                "\nGenerating outreach content..."
            )

            content = generate_outreach(

                query,

                results,

                requested_content

            )

            print(
                "\n" + "=" * 50
            )

            print(
                "GENERATED CONTENT"
            )

            print(
                "=" * 50
            )

            print(
                content
            )