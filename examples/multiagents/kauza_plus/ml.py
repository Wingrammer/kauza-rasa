import os
from typing import Any, Dict, List, Optional, Text, Type

import rasa
from rasa.engine.graph import ExecutionContext, GraphComponent
from rasa.engine.recipes.default_recipe import DefaultV1Recipe
from rasa.engine.storage.resource import Resource
from rasa.engine.storage.storage import ModelStorage

from rasa.nlu.classifiers.classifier import IntentClassifier
from rasa.nlu.extractors.extractor import EntityExtractorMixin, EntityTagSpec
from rasa.nlu.featurizers.featurizer import Featurizer
# from rasa.nlu.model import Interpreter

# Replace with your preferred LLM provider and library
# from llm_provider import LLMClient
from rasa.shared.constants import DIAGNOSTIC_DATA
from rasa.shared.nlu.constants import ENTITIES, INTENT
from rasa.shared.nlu.training_data.message import Message
from rasa.shared.nlu.training_data.training_data import TrainingData
from rasa.utils.tensorflow.constants import ENTITY_RECOGNITION, INTENT_CLASSIFICATION
from rasa.utils.tensorflow.models import RasaModel  # Assume this interacts with your LLM
import logging
logger = logging.getLogger(__name__)

@DefaultV1Recipe.register(
    [
        DefaultV1Recipe.ComponentType.INTENT_CLASSIFIER,
        DefaultV1Recipe.ComponentType.ENTITY_EXTRACTOR,
    ],
    is_trainable=True,
)
class LLMIntentClassifier(GraphComponent, IntentClassifier, EntityExtractorMixin):
    """Custom LLM-based intent classifier using a retrieval-augmented approach."""

    @classmethod
    def required_components(cls) -> List[Type]:
        """Specifies required components before this one in the pipeline."""
        return [Featurizer]

    @classmethod
    def get_default_config(cls) -> Dict[Text, Any]:
        """Returns default config (see parent class for full docstring)."""
        
        return {
            "fallback_intent": "out_of_scope",
            "llm": {
                "model_name": "gpt-3.5-turbo",
                "type": "openai",
            },
            "embeddings": {
                "model_name": "text-embedding-ada-002",
                "type": "openai",
            },
            "prompt": """
                Label a users message from a
                conversation with an intent. Reply ONLY with the name of the intent.

                The intent should be one of the following:
                {% for intent in intents %}- {{intent}}
                {% endfor %}
                {% for example in examples %}
                Message: {{example['text']}}
                Intent: {{example['intent']}}
                {% endfor %}
                Message: {{message}}
                Intent:
            """,
            "number_of_examples": 3,
        }

    def __init__(
        self,
        model_storage: ModelStorage,
        resource: Resource,
        training_artifact: Optional[Dict],
        execution_context: ExecutionContext,
    ) -> None:
        # Store both `model_storage` and `resource` as object attributes to be able
        # to utilize them at the end of the training
        self._model_storage = model_storage
        self._resource = resource

    @classmethod
    def create(
        cls,
        config: Dict[Text, Any],
        model_storage: ModelStorage,
        resource: Resource,
        execution_context: ExecutionContext,
    ) -> "LLMIntentClassifier":
        """Creates a new untrained component (see parent class for full docstring)."""
        return cls(config, model_storage, resource, execution_context)

    

    def train(self, training_data: TrainingData) -> Resource:
        """Train the embedding intent classifier on a data set."""
        try:
            training_data.validate()
        except Exception as e:
            logger.debug(f"Failed to validate training data: {e}")
            return self._resource
        
        # logger.info(training_data.nlu_as_json())
        logger.info(os.getcwd())
        logger.info("Ex")
        logger.info([ex.as_dict() for ex in training_data.training_examples])

        # self.model.fit(
        #     data_generator,
        #     epochs=self.component_config[EPOCHS],
        #     validation_data=validation_data_generator,
        #     validation_freq=self.component_config[EVAL_NUM_EPOCHS],
        #     callbacks=callbacks,
        #     verbose=False,
        #     shuffle=False,  # we use custom shuffle inside data generator
        # )

        # self.persist()

        return self._resource
    
    def process(self, messages: List[Message]) -> List[Message]:
        """Augments the message with intents, entities, and diagnostic data."""
        for message in messages:
            out = self._predict(message)

            if self.component_config[INTENT_CLASSIFICATION]:
                label, label_ranking = self._predict_label(out)

                message.set(INTENT, label, add_to_output=True)
                message.set("intent_ranking", label_ranking, add_to_output=True)

            if self.component_config[ENTITY_RECOGNITION]:
                entities = self._predict_entities(out, message)

                message.set(ENTITIES, entities, add_to_output=True)

            if out and self._execution_context.should_add_diagnostic_data:
                message.add_diagnostic_data(
                    self._execution_context.node_name, out.get(DIAGNOSTIC_DATA)
                )

        return messages

    def predict(self, message: Message, data: Dict[Text, Any]) -> Dict[Text, Any]:
        """Predicts intent using LLM with retrieval-augmented generation (RAG)."""

        # Extract features from message (assuming IntentFeaturizer is present)
        intent_features = data.get("intent_features")
        if not intent_features:
            raise Exception("Missing intent features from previous component.")

        # Retrieve similar training examples based on features (replace with your logic)
        most_similar_examples = self.retrieve_similar_examples(intent_features)

        # Formulate prompt based on retrieved examples and all intents (customize)
        prompt = self.formulate_prompt(message.text, most_similar_examples, self.interpreter.intents)

        # Predict intent label using LLM
        predicted_label = self.llm_client.predict(prompt)

        # Map predicted label to existing intent (optional, based on your use case)
        if self.intent_lookup and predicted_label in self.intent_lookup:
            predicted_intent = self.intent_lookup[predicted_label]
        else:
            # Handle out-of-scope predictions (consider fallback intent)
            predicted_intent = {"name": predicted_label, "confidence": 0.5}  # Adjust confidence

        return {"intent": predicted_intent, **data}

    def retrieve_similar_examples(self, intent_features: Dict) -> List[Dict]:
        # Replace with your logic to retrieve similar examples from training data
        # based on the provided features (e.g., using a k-Nearest Neighbors approach)
        raise NotImplementedError("Implement logic to retrieve similar examples")

    def formulate_prompt(self, message: Text, examples: List[Dict], intents: List[Dict]) -> Text:
        # Customize the prompt template to guide the LLM (consider Jinja2 templating)
        prompt = f"Classify the user message '{message}' based on the following intents:\n"
        for intent in intents:
            prompt += f"- {intent['name']}\n"

        # Add retrieved examples if any (adjust format as needed)
        if examples:
            prompt += "\nExamples:\n"
            for example in examples:
                prompt += f"- {example['text']} (intent: {example['intent']})\n"

        return prompt


