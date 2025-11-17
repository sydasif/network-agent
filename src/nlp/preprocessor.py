"""
NLP Pre-processing Layer using spaCy for fast, local, and deterministic
Intent Classification and Named Entity Recognition.
"""

import spacy
from spacy.matcher import Matcher, PhraseMatcher
from typing import List, Dict
from src.core.models import UserIntent, ExtractedEntities
from src.tools.inventory import network_manager  # Import to get the device list
from src.core.config import settings


class NLPPreprocessor:
    def __init__(self):
        """Initializes the spaCy model, matchers, and intent rules."""
        try:
            self.nlp = spacy.load(settings.spacy_model)
        except OSError:
            print(
                f"spaCy model not found. Please run: python -m spacy download {settings.spacy_model}"
            )
            raise

        self.intent_rules: Dict[str, List[str]] = {
            "get_status": [
                "show",
                "what is",
                "check",
                "display",
                "status",
                "version",
                "uptime",
                "interface",
                "vlan",
                "interface brief",
            ],
            "get_config": [
                "config",
                "configuration",
                "running-config",
                "startup-config",
            ],
            "find_device": ["find", "list", "search", "which devices", "all devices"],
            "troubleshoot_history": [
                "history",
                "log",
                "logs",
                "past",
                "error",
                "errors",
                "flap",
                "flaps",
                "yesterday",
                "last night",
            ],
            "greeting": ["hello", "hi", "hey", "greetings"],
        }

        self.matcher = Matcher(self.nlp.vocab)
        self.phrase_matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")

        device_names = list(network_manager.devices.keys())
        device_patterns = [self.nlp.make_doc(name) for name in device_names]
        self.phrase_matcher.add("DEVICE", device_patterns)

        protocols = ["bgp", "ospf", "eigrp", "spanning-tree", "stp", "vlan"]
        protocol_patterns = [self.nlp.make_doc(p) for p in protocols]
        self.phrase_matcher.add("PROTOCOL", protocol_patterns)

        keywords = ["flaps", "errors", "config", "down", "up", "critical"]
        keyword_patterns = [self.nlp.make_doc(k) for k in keywords]
        self.phrase_matcher.add("KEYWORD", keyword_patterns)

        interface_pattern = [
            {
                "TEXT": {
                    "REGEX": r"([Gg]i|[Ff]a|[Ee]th|[Tt]en)[a-zA-Z]*\d+([/]\d+)*([.]\d+)?"
                }
            }
        ]
        self.matcher.add("INTERFACE", [interface_pattern])

    def _classify_intent(self, doc) -> str:
        query_lower = doc.text.lower()
        for intent, keywords in self.intent_rules.items():
            if any(keyword in query_lower for keyword in keywords):
                return intent
        return "unknown"

    def _extract_entities(self, doc) -> ExtractedEntities:
        matches = self.matcher(doc) + self.phrase_matcher(doc)
        entities = ExtractedEntities(
            device_names=[], interfaces=[], protocols=[], keywords=[]
        )

        for match_id, start, end in matches:
            span = doc[start:end]
            entity_label = self.nlp.vocab.strings[match_id]

            if entity_label == "DEVICE" and span.text not in entities.device_names:
                entities.device_names.append(span.text)
            elif entity_label == "INTERFACE" and span.text not in entities.interfaces:
                entities.interfaces.append(span.text)
            elif (
                entity_label == "PROTOCOL"
                and span.text.lower() not in entities.protocols
            ):
                entities.protocols.append(span.text.lower())
            elif (
                entity_label == "KEYWORD" and span.text.lower() not in entities.keywords
            ):
                entities.keywords.append(span.text.lower())

        return entities

    def process(self, query: str) -> UserIntent:
        doc = self.nlp(query)
        intent = self._classify_intent(doc)
        entities = self._extract_entities(doc)
        is_ambiguous = (
            intent in ["get_status", "get_config"] and not entities.device_names
        )
        sentiment = (
            "urgent"
            if "urgent" in query.lower() or "down" in query.lower()
            else "normal"
        )

        return UserIntent(
            query=query,
            intent=intent,
            entities=entities,
            sentiment=sentiment,
            is_ambiguous=is_ambiguous,
        )
