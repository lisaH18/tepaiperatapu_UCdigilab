"""
The Māori nucleus/periphery tagger.

Pipeline:
    1. get_grouped_words
       Split each verse into word groups and punctuation.

    2. classify_phrase
       Apply first-pass lexical classifications.

    3. apply_rules
       Refine the classifications using contextual rules.

    4. tag_phrase
       Convert index sets into per-token labels.

The contextual rules allow ambiguous lexical items to become nuclei:

    te ana      -> ana is a nucleus
    ka hoki     -> hoki is a nucleus
    tōku roto   -> roto is a nucleus
    e ia        -> ia is a nucleus
    ia rā       -> rā is a nucleus

Words confirmed as nuclei lose their lexical prep/post tags.
"""

from __future__ import annotations

import re
import unicodedata

from lexicons import (
    distributive_nouns,
    demonstratives, 
    manner_particles_re,
    maori_possessives,
    noun_licensers,
    personal_pronouns,
    post_phrases,
    post_words,
    predicate_licensers,
    prep_words,
)


# Set this to True if your alignment model should treat all personal pronouns
# as nuclei by default.
#
# When False, pronouns begin as preposed periphery but may still be promoted
# contextually, such as "ia" in "e ia".
PRONOUNS_ARE_NUCLEI = True


# Unicode-aware punctuation:
# anything that is neither a word character nor whitespace.
PUNCT_GROUP_RE = re.compile(r"([^\w\s]+)", flags=re.UNICODE)
PUNCT_ONLY_RE = re.compile(r"[^\w\s]+", flags=re.UNICODE)


# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------

def normalise_word(word: str) -> str:
    """Return an NFC-normalised, case-folded token.

    NFC normalisation prevents visually identical macronised forms from being
    treated as different strings because of their underlying Unicode encoding.
    """
    return unicodedata.normalize("NFC", word).casefold()


# ---------------------------------------------------------------------------
# 1. Clean and group the raw text
# ---------------------------------------------------------------------------

def get_grouped_words(verses: list[str]) -> list[dict]:
    """Split verses into word groups and punctuation groups.

    Each word group stores:
        display_words:
            Original forms for output.

        words:
            Normalised forms for tagging.

    """
    grouped: list[dict] = []

    for verse_id, verse in enumerate(verses):
        verse = verse.replace("[", " ").replace("]", " ")

        for part in PUNCT_GROUP_RE.split(verse):
            if not part or not part.strip():
                continue

            if PUNCT_ONLY_RE.fullmatch(part):
                grouped.append({
                    "verse_id": verse_id,
                    "type": "punct",
                    "text": part,
                })
                continue

            display_words = part.split()
            words = [normalise_word(word) for word in display_words]

            grouped.append({
                "verse_id": verse_id,
                "type": "words",
                "display_words": display_words,
                "words": words,
            })

    return grouped


# ---------------------------------------------------------------------------
# 2. First-pass classification, preposed + postposed vs possible nucleus
# ---------------------------------------------------------------------------

def classify_phrase(
    words: list[str],
) -> tuple[set[int], set[int], set[int]]:
    """Return prep, post, and nucleus index sets for one word group."""

    prep = {
        index
        for index, word in enumerate(words)
        if (
            word in prep_words
            and word not in maori_possessives
        )
    }

    post = {
        index
        for index, word in enumerate(words)
        if (
            (
                word in post_words
                or manner_particles_re.fullmatch(word) is not None
            )
            and word not in maori_possessives
        )
    }

    if PRONOUNS_ARE_NUCLEI:
        prep -= {
            index
            for index, word in enumerate(words)
            if word in personal_pronouns
        }

    nucl = {
        index
        for index, word in enumerate(words)
        if (
            word in maori_possessives
            or (
                index not in prep
                and index not in post
            )
        )
    }

    return prep, post, nucl

# ---------------------------------------------------------------------------
# Shared rule helper
# ---------------------------------------------------------------------------

def _promote_to_nucleus(
    index: int,
    words: list[str],
    prep: set[int],
    post: set[int],
    nucl: set[int],
    log: list[dict],
    verse_id: int,
    reason: str,
) -> None:
    """Remove peripheral labels and promote one token to nucleus."""
    if index < 0 or index >= len(words):
        return

    changed = index not in nucl or index in prep or index in post

    prep.discard(index)
    post.discard(index)
    nucl.add(index)

    if changed:
        _log(
            log=log,
            verse_id=verse_id,
            index=index,
            word=words[index],
            rule=reason,
        )

# ---------------------------------------------------------------------------
# 3. Context rules
# ---------------------------------------------------------------------------

def rule_licenser_head(
    words: list[str],
    prep: set[int],
    post: set[int],
    nucl: set[int],
    log: list[dict],
    verse_id: int,
) -> None:
    """Promote the head following a determiner or predicate marker."""

    for index, word in enumerate(words):

        # An independent demonstrative is a nucleus and must not
        # license the following word.
        if word in demonstratives and index in nucl:
            continue

        following_index = index + 1

        if following_index >= len(words):
            continue

        following_word = words[following_index]

        if word in noun_licensers:
            # Let the following determiner license its own head.
            if following_word in noun_licensers:
                continue

            _promote_to_nucleus(
                index=following_index,
                words=words,
                prep=prep,
                post=post,
                nucl=nucl,
                log=log,
                verse_id=verse_id,
                reason="after noun licenser -> nucleus",
            )

        elif word in predicate_licensers:
            # Example: e te iwi — te remains prep and licenses iwi.
            if following_word in noun_licensers:
                continue

            _promote_to_nucleus(
                index=following_index,
                words=words,
                prep=prep,
                post=post,
                nucl=nucl,
                log=log,
                verse_id=verse_id,
                reason="after predicate licenser -> nucleus",
            )


def rule_independent_demonstrative(
    words,
    prep,
    post,
    nucl,
    log,
    verse_id,
):
    """Promote a demonstrative when it stands in place of a noun phrase.

    A demonstrative remains prep when it introduces an expressed head:

        tēnei whare
        ēnā tāngata

    It becomes a nucleus when it is phrase-final or followed only by
    postposed particles:

        ko tēnei
        tēnei hoki
        tērā anō hoki
    """

    for index, word in enumerate(words):
        if word not in demonstratives:
            continue

        following_indices = range(index + 1, len(words))

        phrase_final = index == len(words) - 1

        followed_only_by_post = (
            not phrase_final
            and all(
                following_index in post
                for following_index in following_indices
            )
        )

        if phrase_final or followed_only_by_post:
            _promote_to_nucleus(
                index=index,
                words=words,
                prep=prep,
                post=post,
                nucl=nucl,
                log=log,
                verse_id=verse_id,
                reason="independent demonstrative -> nucleus",
            )


def rule_distributive_ia(
    words: list[str],
    prep: set[int],
    post: set[int],
    nucl: set[int],
    log: list[dict],
    verse_id: int,
) -> None:
    """Handle distributive ia followed by a recognised nominal head."""

    for index, word in enumerate(words[:-1]):
        following_index = index + 1
        following_word = words[following_index]

        if word == "ia" and following_word in distributive_nouns:
            # Here ia is a distributive determiner, not a pronoun nucleus.
            nucl.discard(index)
            post.discard(index)
            prep.add(index)

            _promote_to_nucleus(
                index=following_index,
                words=words,
                prep=prep,
                post=post,
                nucl=nucl,
                log=log,
                verse_id=verse_id,
                reason="after distributive ia -> nucleus",
            )

def rule_fixed_phrases(
    words: list[str],
    prep: set[int],
    post: set[int],
    nucl: set[int],
    log: list[dict],
    verse_id: int,
) -> None:
    """Lock known multiword expressions into postposed periphery.

    This rule runs last so that fixed expressions override earlier token-level
    classifications.
    """
    phrases = sorted(
        post_phrases,
        key=len,
        reverse=True,
    )

    for target in phrases:
        phrase_length = len(target)

        for start in range(len(words) - phrase_length + 1):
            candidate = tuple(words[start:start + phrase_length])

            if candidate != target:
                continue

            for index in range(start, start + phrase_length):
                prep.discard(index)
                nucl.discard(index)
                post.add(index)

            _log(
                log=log,
                verse_id=verse_id,
                index=start,
                word=" ".join(target),
                rule="fixed phrase -> post",
            )


def apply_rules(
    words: list[str],
    prep: set[int],
    post: set[int],
    nucl: set[int],
    log: list[dict],
    verse_id: int,
) -> None:
    """Apply contextual rules and remove peripheral tags from nuclei."""

    rule_independent_demonstrative(
        words,
        prep,
        post,
        nucl,
        log,
        verse_id,
    )

    rule_licenser_head(
        words,
        prep,
        post,
        nucl,
        log,
        verse_id,
    )

    rule_distributive_ia(
        words,
        prep,
        post,
        nucl,
        log,
        verse_id,
    )

    rule_fixed_phrases(
        words,
        prep,
        post,
        nucl,
        log,
        verse_id,
    )

    prep -= nucl
    post -= nucl

def _log(
    log: list[dict],
    verse_id: int,
    index: int,
    word: str,
    rule: str,
) -> None:
    """Append one rule action to the debugging log."""
    log.append({
        "verse": verse_id,
        "index": index,
        "word": word,
        "rule": rule,
    })


# ---------------------------------------------------------------------------
# 4. Convert index sets into tags
# ---------------------------------------------------------------------------

def tag_phrase(
    words: list[str],
    prep: set[int],
    post: set[int],
    nucl: set[int],
) -> list[str]:
    """Return one tag string for each word."""
    tags: list[str] = []

    for index in range(len(words)):
        roles: list[str] = []

        if index in prep:
            roles.append("prep")

        if index in nucl:
            roles.append("nucl")

        if index in post:
            roles.append("post")

        tags.append("-".join(roles) if roles else "unk")

    return tags


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------

def tag_verses(
    verses: list[str],
) -> tuple[list[dict], list[dict]]:
    """Tag a list of verse strings.

    Returns:
        grouped:
            Grouped text with per-token tags and rendered word/tag strings.

        log:
            Contextual classification changes made by the rules.
    """
    grouped = get_grouped_words(verses)
    log: list[dict] = []

    for part in grouped:
        if part["type"] != "words":
            continue

        words = part["words"]

        prep, post, nucl = classify_phrase(words)

        apply_rules(
            words=words,
            prep=prep,
            post=post,
            nucl=nucl,
            log=log,
            verse_id=part["verse_id"],
        )

        tags = tag_phrase(
            words=words,
            prep=prep,
            post=post,
            nucl=nucl,
        )

        part["tags"] = tags
        part["tagged"] = " ".join(
            f"{part['display_words'][index]}/{tags[index]}"
            for index in range(len(words))
        )

    return grouped, log

