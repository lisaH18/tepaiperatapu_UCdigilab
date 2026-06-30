"""
Word lists for the Māori nucleus/periphery POS tagger.
Some labelled subsets are used by contextual disambiguation rules.
The entries are grouped alphabetically in the source for maintenance.
"""

# TODO: a separate tag for discourse marker

# ---------------------------------------------------------------------------
# Preposed periphery
# ---------------------------------------------------------------------------

prep_words = frozenset([
    "a", "ā", "āku", "aha", "ahakoa", "ahau", "āna", "anō", "au", "aua", "āu",
    "e", "ēhea", "ēnā", "ēnei", "ērā", "ētahi", "ētehi",
    "he", "hea", "hei", "heoi",
    "i", "ia",
    "ka", "kei", "ki", "kia", "ko", "koe", "koia", "kōrua", "koutou", "kua",
    "mā", "mātou", "māua", "me", "mō",
    "nā", "ngā", "nō",
    "o", "ō", "ōku", "ōna", "ōu", "oti",
    "rātou", "rāua",
    "tā", "tāku", "tāna", "tātou", "taua", "tāu", "tāua", "te", "tē", "tēhea", "tēnā", "tēnei", "tērā", "tētahi", "tētehi", "tō", "tōku", "tōna", "tōu",
])

# discourse marker treat as prep 

# negation words (kīhai, kaua) - nucleus

# ---------------------------------------------------------------------------
# Discourse marker - treat this as a a separate tag, not prep not nucleus
# ahakoa, nā, ā, 
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Personal pronouns - treat this as a nucleus
# ---------------------------------------------------------------------------

personal_pronouns = frozenset([
    "ahau", "au",
    "ia",
    "koe", "kōrua", "koutou",
    "māua", "mātou",
    "rāua", "rātou",
    "tāua", "tātou",
])


# ---------------------------------------------------------------------------
# Determiners
# ---------------------------------------------------------------------------

# Determiners are a labelled subset of prep_words.
# "ia" is included because it can be distributive, as in "ia rā".
# However, it is excluded from automatic noun licensing because it is much
# more commonly a personal pronoun.

det_words = frozenset([
    "āku", "āna", "aua", "āu",
    "ēhea", "ēnā", "ēnei", "ērā", "ētahi", "ētehi",
    "he",
    "ia",
    "ngā",
    "ōku", "ōna", "ōu",
    "tāku", "tāna", "taua", "tāu", "te", "tēhea", "tēnā", "tēnei", "tērā", "tētahi", "tētehi", "tōku", "tōna", "tōu",
])


# Determiners that safely license the following nominal head.
#
# "ia" is excluded because:
#     e ia     = by him/her
#     i a ia   = him/her
#
# It is handled separately when it has a distributive function.
noun_licensers = det_words - {"ia"}

# ---------------------------------------------------------------------------
# Predicate markers
# ---------------------------------------------------------------------------

# These particles normally introduce a following predicate.
#
# "i" and "kei" are not included as general predicate licensers because they
# also introduce locative phrases:
#
#     i roto i te whare
#     kei roto i te whare
#
# The patterns "i te + predicate" and "kei te + predicate" still work because
# "te" licenses the following nucleus.
predicate_licensers = frozenset([
    "e",
    "ka", "kia", "kua",
])

# Retained as a general combined category for compatibility.
licensers = noun_licensers | predicate_licensers

# ---------------------------------------------------------------------------
# Possessive constructions - treat as nucleus 
# ---------------------------------------------------------------------------

maori_possessives = [ 
    # Mine (1st person) 
    "nāku", "nōku", "māku", "mōku", 
    # Yours (2nd person) 
    "nāu", "nōu", "māu", "mōu", 
    # # His / Hers (3rd person) 
    "nāna", "nōna", "māna", "mōna"
]

# these are considered nucleus when by themselves
demonstratives = [
    "tēnei",
    "tēnā",
    "tērā",
    "tētahi",
    "ēnei",
    "ētahi",
    "ēnā",
    "ērā",
]

# These can introduce a pronoun before the noun:
#
#     tō mātou whare
#     ā rāua pukapuka
#     ō koutou whakaaro

# ---------------------------------------------------------------------------
# Distributive ia
# ---------------------------------------------------------------------------

# A conservative list of words that commonly follow distributive "ia":
#
#     ia rā
#     ia wiki
#     ia tau
#
# This is a heuristic rather than a complete grammatical list.

distributive_nouns = frozenset([
    "haora",
    "marama",
    "pō",
    "rā",
    "tangata",
    "tau",
    "wā",
    "wiki",
])


# ---------------------------------------------------------------------------
# Postposed periphery
# ---------------------------------------------------------------------------

# if noa comes after nucleus it would be a postposed. 
# interesting observationb: "i" is usually followed by a nuclues, occassionally postposed 
# "aua" can mean far ahead/distant if followed by atu/mai 

post_words = frozenset([
    "ai", "ake", "ana", "anō", "atu",
    "hoki",
    "iho",
    "kē", "kau", "kō",
    "mai",
    "nā", "nei", "noa",
    "rā", "rawa",
    "tonu"
]) 

manner_particles = [
    "kē", "kau",
    "mā",
    "noa",
    "rawa", 
    "tonu"
]

# Use regex to find manner particles followed with -tia suffix 
import re
manner_particles_re = re.compile(
    r"(?:rawa|tonu|kau|noa|kē)(?:tia)?$"
)
# ---------------------------------------------------------------------------
# Fixed multiword peripheral expressions
# ---------------------------------------------------------------------------

# Store phrases as tuples so they do not need to be split repeatedly.
#
# Every word in a matched phrase is tagged as postposed periphery.
post_phrases = (
    ("anō", "rā", "hoki"),
    ("anō", "hoki"),
    ("he", "aha"),
)

