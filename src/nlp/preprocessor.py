"""
NLP Pre-processing Layer using spaCy.

This module implements an NLP pre-processor that classifies user intent and extracts
named entities from natural language queries. The pre-processor is self-configuring,
dynamically building its rules from the command.yaml file to ensure it stays in sync
with the agent's capabilities.

The pre-processor uses spaCy for natural language understanding and includes:
- Intent classification based on keyword matching
- Entity extraction for devices, interfaces, protocols, and keywords
- Dynamic rule loading from configuration files
- Interface pattern recognition for network equipment

This approach allows the NLP layer to be always in sync with the agent's capabilities.
"""
import spacy
import yaml
from spacy.matcher import Matcher, PhraseMatcher
from typing import List, Dict, Set
from src.core.models import UserIntent, ExtractedEntities
from src.tools.inventory import network_manager
from src.core.config import settings

class NLPPreprocessor:
    """NLP pre-processor for classifying user intent and extracting entities.

    This class processes natural language queries from users, classifying the intent
    (e.g., get_status, get_config) and extracting relevant entities (device names,
    interfaces, protocols). The pre-processor is self-configuring, dynamically
    building its rules from the command.yaml file.

    Attributes:
        nlp: The spaCy NLP model instance.
        intent_rules (Dict[str, List[str]]): Mapping of intents to keyword lists.
        phrase_matcher: spaCy PhraseMatcher for entity recognition.
        matcher: spaCy Matcher for pattern-based matching.
    """

    def __init__(self, template_file: str = "command.yaml"):
        """Initializes the NLP pre-processor with spaCy model and dynamic rules.

        The constructor loads the spaCy model and dynamically builds intent rules
        and entity matchers from the command template file. This ensures the NLP
        layer stays synchronized with the agent's capabilities.

        Args:
            template_file (str): Path to the command template file (default: "command.yaml").

        Raises:
            OSError: If the spaCy model is not found.
            FileNotFoundError: If the template file is not found.
        """
        try:
            self.nlp = spacy.load(settings.spacy_model)
        except OSError:
            print(f"spaCy model not found. Please run: python -m spacy download {settings.spacy_model}")
            raise

        # --- DYNAMICALLY BUILD RULES FROM TEMPLATES ---
        self.intent_rules: Dict[str, List[str]] = {}
        self.phrase_matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")

        try:
            with open(template_file, "r") as f:
                templates = yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Error: Command template file not found at {template_file}")
            # Fallback to empty templates
            templates = {}

        # Dynamically build intent rules and entity patterns
        all_entities: Dict[str, Set[str]] = {}

        for intent, rules in templates.items():
            if intent == "global_entities":
                for entity_type, entity_list in rules.items():
                    all_entities.setdefault(entity_type, set()).update(entity_list)
                continue

            if isinstance(rules, list):  # Ensure rules is a list of templates
                self.intent_rules[intent] = []
                for rule in rules:
                    if "keywords" in rule:
                        self.intent_rules[intent].extend(rule["keywords"])
                        if "entities" in rule:
                            for entity_type, entity_list in rule["entities"].items():
                                all_entities.setdefault(entity_type, set()).update(entity_list)

        # Add all collected entities to the PhraseMatcher
        for entity_type, entity_set in all_entities.items():
            patterns = [self.nlp.make_doc(text) for text in entity_set]
            self.phrase_matcher.add(entity_type, patterns)

        # --- Add static matchers that are always needed ---
        self.matcher = Matcher(self.nlp.vocab)

        # Device names are still dynamic from the live inventory, cache them to avoid repeated lookups
        self._device_names = list(network_manager.devices.keys())
        device_patterns = [self.nlp.make_doc(name) for name in self._device_names]
        self.phrase_matcher.add("DEVICE", device_patterns)

        # Interface patterns are regex-based and remain static
        interface_pattern = [{"TEXT": {"REGEX": r"([Gg]i|[Ff]a|[Ee]th|[Tt]en)[a-zA-Z]*\d+([/]\d+)*([.]\d+)?"}}]
        self.matcher.add("INTERFACE", [interface_pattern])

    def _classify_intent(self, doc) -> str:
        """Classifies the intent of the user query based on keyword matching.

        This method analyzes the processed spaCy document and determines the
        user's intent by matching against the dynamically loaded intent rules.

        Args:
            doc: The processed spaCy document.

        Returns:
            str: The classified intent (e.g., 'get_status', 'get_config', 'unknown').
        """
        # This logic remains the same, but its rules are now dynamic
        query_lower = doc.text.lower()
        for intent, keywords in self.intent_rules.items():
            if any(keyword in query_lower for keyword in keywords):
                return intent
        return "unknown"

    def _extract_entities(self, doc) -> ExtractedEntities:
        """Extracts named entities from the processed query document.

        This method identifies and extracts various types of entities from the
        spaCy document, including device names, interfaces, protocols, and keywords.

        Args:
            doc: The processed spaCy document.

        Returns:
            ExtractedEntities: An object containing all extracted entities.
        """
        # This logic remains the same
        matches = self.matcher(doc) + self.phrase_matcher(doc)
        entities = ExtractedEntities(device_names=[], interfaces=[], protocols=[], keywords=[])

        # Use a set to avoid duplicate entities from overlapping matches
        found_entities = set()

        for match_id, start, end in matches:
            span = doc[start:end]
            entity_label = self.nlp.vocab.strings[match_id]
            entity_text = span.text

            if (entity_label, entity_text) in found_entities:
                continue

            if entity_label == "DEVICE":
                entities.device_names.append(entity_text)
            elif entity_label == "INTERFACE":
                entities.interfaces.append(entity_text)
            elif entity_label == "PROTOCOL":
                entities.protocols.append(entity_text.lower())
            elif entity_label == "KEYWORD":
                entities.keywords.append(entity_text.lower())

            found_entities.add((entity_label, entity_text))

        return entities

    def process(self, query: str) -> UserIntent:
        """Processes a natural language query and returns structured intent information.

        This is the main method of the pre-processor, which analyzes a user's query
        and returns a structured representation containing the intent, extracted
        entities, and additional metadata.

        Args:
            query (str): The natural language query from the user.

        Returns:
            UserIntent: A structured representation of the user's intent and entities.
        """
        # This logic remains the same
        doc = self.nlp(query)
        intent = self._classify_intent(doc)
        entities = self._extract_entities(doc)
        is_ambiguous = (intent in ["get_status", "get_config"] and not entities.device_names)
        sentiment = "urgent" if "urgent" in query.lower() or "down" in query.lower() else "normal"

        return UserIntent(
            query=query, intent=intent, entities=entities, sentiment=sentiment, is_ambiguous=is_ambiguous
        )

    def refresh_device_names(self):
        """Refreshes the device names in the NLP preprocessor when inventory changes.

        This method updates the device name patterns in the phrase matcher to include
        any new devices that have been added to the network inventory since initialization.
        """
        # Get the latest device names from the network manager
        current_device_names = list(network_manager.devices.keys())

        # If device names have changed, update the matcher
        if set(current_device_names) != set(self._device_names):
            # Remove old device patterns
            try:
                self.phrase_matcher.remove("DEVICE")
            except KeyError:
                # DEVICE pattern might not exist, which is fine
                pass

            # Update the internal list of device names
            self._device_names = current_device_names

            # Create and add new device patterns
            device_patterns = [self.nlp.make_doc(name) for name in self._device_names]
            self.phrase_matcher.add("DEVICE", device_patterns)
