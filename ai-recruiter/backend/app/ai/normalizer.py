import os
import json
import re
from typing import Dict, List, Optional, Set, Tuple

TAXONOMY_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "skills_taxonomy.json")
)


def _levenshtein_distance(s1: str, s2: str) -> int:
    """Compute Levenshtein edit distance between two strings."""
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


class SkillNormalizer:
    def __init__(self, taxonomy_file: str = TAXONOMY_PATH):
        self.alias_to_canonical: Dict[str, str] = {}
        self.canonical_to_category: Dict[str, str] = {}
        self.canonical_skills: Set[str] = set()
        self._load_taxonomy(taxonomy_file)

    def _load_taxonomy(self, filepath: str):
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    categories = data.get("categories", {})
                    for cat_name, skill_list in categories.items():
                        for item in skill_list:
                            canonical = item["canonical"]
                            self.canonical_skills.add(canonical)
                            self.canonical_to_category[canonical] = cat_name
                            # Canonical name itself
                            self.alias_to_canonical[canonical.lower()] = canonical
                            # Aliases
                            for alias in item.get("aliases", []):
                                self.alias_to_canonical[alias.lower().strip()] = canonical
            except Exception as e:
                print(f"[!] Warning: Failed loading taxonomy from {filepath}: {e}")

        # Fallback essentials if empty
        if not self.alias_to_canonical:
            fallback = {
                "py": "Python", "python": "Python", "python3": "Python",
                "fastapi": "FastAPI", "django": "Django", "flask": "Flask",
                "react": "React", "reactjs": "React", "react.js": "React",
                "k8s": "Kubernetes", "kubernetes": "Kubernetes",
                "postgres": "PostgreSQL", "postgresql": "PostgreSQL",
                "spring": "Spring Boot", "springboot": "Spring Boot",
                "aws": "AWS", "amazon web services": "AWS",
                "docker": "Docker", "sql": "SQL", "spark": "Apache Spark"
            }
            for a, c in fallback.items():
                self.alias_to_canonical[a] = c
                self.canonical_skills.add(c)
                self.canonical_to_category[c] = "Technical"

    def normalize(self, skill: str) -> str:
        """
        Normalize an input skill string to its canonical title.
        Example: "py" -> "Python", "ReactJS" -> "React", "K8s" -> "Kubernetes"
        """
        if not skill:
            return ""

        clean = skill.strip()
        lower = clean.lower()

        # 1. Direct dictionary match
        if lower in self.alias_to_canonical:
            return self.alias_to_canonical[lower]

        # 2. Canonical exact match (case preserved)
        if clean in self.canonical_skills:
            return clean

        # 3. Strip trailing dots/version numbers (e.g., "Python 3.10" -> "Python")
        simplified = re.sub(r"\s+v?\d+(\.\d+)*$", "", lower).strip()
        if simplified in self.alias_to_canonical:
            return self.alias_to_canonical[simplified]

        # 4. Fuzzy matching for slight typos (e.g., "PostgreSQ" -> "PostgreSQL")
        if len(clean) >= 4:
            for alias, canonical in self.alias_to_canonical.items():
                if len(alias) >= 4 and abs(len(alias) - len(lower)) <= 2:
                    if _levenshtein_distance(alias, lower) <= 1:
                        return canonical

        # Return title-cased original if unrecognized
        return clean.title()

    def get_category(self, canonical_skill: str) -> str:
        """Return the category for a canonical skill."""
        return self.canonical_to_category.get(canonical_skill, "Other Technical")

    def extract_from_text(self, text: str) -> List[Dict[str, any]]:
        """
        Scan unformatted text for known skills and return list of canonical skills with confidence.
        Uses boundary-aware regex to prevent false positives (e.g. "go", "c", "r").
        """
        if not text:
            return []

        lower_text = text.lower()
        found_skills: Dict[str, Dict[str, any]] = {}

        # Sort aliases by descending length so multi-word terms (e.g. "Apache Spark") match before single words
        sorted_aliases = sorted(self.alias_to_canonical.keys(), key=lambda x: len(x), reverse=True)

        for alias in sorted_aliases:
            # Special case for very short terms (1-2 chars) like "c", "r", "go", "ts", "js"
            if len(alias) <= 2:
                # Require explicit technical context around short terms
                pattern = r"(?:skills?|languages?|technologies?|stack|frameworks?|proficient in|experience with)[\s\S]{0,100}\b" + re.escape(alias) + r"\b"
                if not re.search(pattern, lower_text):
                    continue
            else:
                pattern = r"\b" + re.escape(alias) + r"\b"
                if not re.search(pattern, lower_text):
                    continue

            canonical = self.alias_to_canonical[alias]
            if canonical not in found_skills:
                found_skills[canonical] = {
                    "skill": canonical,
                    "matched_alias": alias,
                    "category": self.get_category(canonical),
                    "confidence": 0.95 if alias.lower() == canonical.lower() else 0.90
                }

        return list(found_skills.values())


skill_normalizer = SkillNormalizer()
