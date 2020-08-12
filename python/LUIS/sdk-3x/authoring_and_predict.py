# To run this sample, install the following modules.
# pip install azure-cognitiveservices-language-luis

# <Dependencies>
from azure.cognitiveservices.language.luis.authoring import LUISAuthoringClient
from azure.cognitiveservices.language.luis.runtime import LUISRuntimeClient
from msrest.authentication import CognitiveServicesCredentials
from functools import reduce

import datetime, json, os, time
# </Dependencies>

def quickstart(): 

	# <VariablesYouChange>
	authoringKey = 'REPLACE-WITH-YOUR-ASSIGNED-AUTHORING-KEY'
	authoringResourceName = "REPLACE-WITH-YOUR-AUTHORING-RESOURCE-NAME";
	predictionResourceName = "REPLACE-WITH-YOUR-PREDICTION-RESOURCE-NAME";
	# </VariablesYouChange>

	# <VariablesYouDontNeedToChangeChange>
	authoringEndpoint = f'https://{authoringResourceName}.cognitiveservices.azure.com/'
	predictionEndpoint = f'https://{predictionResourceName}.cognitiveservices.azure.com/'

	appName = "Contoso Pizza Company"
	versionId = "0.1"
	intentName = "OrderPizzaIntent"
	# </VariablesYouDontNeedToChangeChange>

	# <AuthoringCreateClient>
	client = LUISAuthoringClient(authoringEndpoint, CognitiveServicesCredentials(authoringKey))
	# </AuthoringCreateClient>

	# Create app
	app_id = create_app(client, appName, versionId)

	# <AddIntent>
	client.model.add_intent(app_id, versionId, intentName)
	# </AddIntent>
	
	# Add Entities
	add_entities(client, app_id, versionId)
	
	# Add labeled examples
	add_labeled_examples(client,app_id, versionId, intentName)

	# <TrainAppVersion>
	client.train.train_version(app_id, versionId)
	waiting = True
	while waiting:
		info = client.train.get_status(app_id, versionId)

		# get_status returns a list of training statuses, one for each model. Loop through them and make sure all are done.
		waiting = any(map(lambda x: 'Queued' == x.details.status or 'InProgress' == x.details.status, info))
		if waiting:
			print ("Waiting 10 seconds for training to complete...")
			time.sleep(10)
		else: 
			print ("trained")
			waiting = False
	# </TrainAppVersion>
	
	# <PublishVersion>
	responseEndpointInfo = client.apps.publish(app_id, versionId, is_staging=False)
	# </PublishVersion>
	
	# <PredictionCreateClient>
	runtimeCredentials = CognitiveServicesCredentials(authoringKey)
	clientRuntime = LUISRuntimeClient(endpoint=predictionEndpoint, credentials=runtimeCredentials)
    # </PredictionCreateClient>

    # <QueryPredictionEndpoint>
    # Production == slot name
	request = { "query" : "I want two small pepperoni pizzas with more salsa" }
	
	response = clientRuntime.prediction.get_slot_prediction(app_id, "Production", request)
	print("Top intent: {}".format(response.prediction.top_intent))
	print("Sentiment: {}".format (response.prediction.sentiment))
	print("Intents: ")

	for intent in response.prediction.intents:
		print("\t{}".format (json.dumps (intent)))
	print("Entities: {}".format (response.prediction.entities))
    # </QueryPredictionEndpoint>

def create_app(client, appName, versionId):

    # <AuthoringCreateApplication>
	appDefinition = {
        "name": appName,
        "initial_version_id": versionId,
        "culture": "en-us"
    }

	app_id = client.apps.add(appDefinition)

	print("Created LUIS app with ID {}".format(app_id))
	# </AuthoringCreateApplication>
	
	return app_id
	
# </createApp>

def add_entities(client, appId, versionId):

	# <AuthoringAddEntities>
	# Add Prebuilt entity
	client.model.add_prebuilt(appId, versionId, prebuilt_extractor_names=["number"])

	mlEntityDefinition = [
	{
		"name": "Pizza",
		"children": [
			{ "name": "Quantity" },
			{ "name": "Type" },
			{ "name": "Size" }
			]
			},
			{
			"name": "Toppings",
			"children": [
				{ "name": "Type" },
				{ "name": "Quantity" }
			]
		}
	]

	modelId = client.model.add_entity(appId, versionId, name="Pizza order", children=mlEntityDefinition)
	
	# Add phraselist feature
	phraseList = {
		"enabledForAllModels": False,
		"isExchangeable": True,
		"name": "QuantityPhraselist",
		"phrases": "few,more,extra"
	}
	
	phraseListId = client.features.add_phrase_list(appId, versionId, phraseList)
	
	# Get entity and subentities
	modelObject = client.model.get_entity(appId, versionId, modelId)
	toppingQuantityId = get_grandchild_id(modelObject, "Toppings", "Quantity")
	pizzaQuantityId = get_grandchild_id(modelObject, "Pizza", "Quantity")

	# add model as feature to subentity model
	prebuiltFeatureRequiredDefinition = { "model_name": "number", "is_required": True }
	client.features.add_entity_feature(appId, versionId, pizzaQuantityId, prebuiltFeatureRequiredDefinition)
	
	# add model as feature to subentity model
	prebuiltFeatureNotRequiredDefinition = { "model_name": "number" }
	client.features.add_entity_feature(appId, versionId, toppingQuantityId, prebuiltFeatureNotRequiredDefinition)

    # add phrase list as feature to subentity model
	phraseListFeatureDefinition = { "feature_name": "QuantityPhraselist", "model_name": None }
	client.features.add_entity_feature(appId, versionId, toppingQuantityId, phraseListFeatureDefinition)
    # </AuthoringAddEntities>
	

def add_labeled_examples(client, appId, versionId, intentName):

	# <AuthoringAddLabeledExamples>
    # Define labeled example
    labeledExampleUtteranceWithMLEntity = {
        "text": "I want two small seafood pizzas with extra cheese.",
        "intentName": intentName,
        "entityLabels": [
            {
                "startCharIndex": 7,
                "endCharIndex": 48,
                "entityName": "Pizza order",
                "children": [
                    {
                        "startCharIndex": 7,
                        "endCharIndex": 30,
                        "entityName": "Pizza",
                        "children": [
                            {
                                "startCharIndex": 7,
                                "endCharIndex": 9,
                                "entityName": "Quantity"
                            },
                            {
                                "startCharIndex": 11,
                                "endCharIndex": 15,
                                "entityName": "Size"
                            },
                            {
                                "startCharIndex": 17,
                                "endCharIndex": 23,
                                "entityName": "Type"
                            }]
                    },
                    {
                        "startCharIndex": 37,
                        "endCharIndex": 48,
                        "entityName": "Toppings",
                        "children": [
                            {
                                "startCharIndex": 37,
                                "endCharIndex": 41,
                                "entityName": "Quantity"
                            },
                            {
                                "startCharIndex": 43,
                                "endCharIndex": 48,
                                "entityName": "Type"
                            }]
                    }
                ]
            }
        ]
    }

    print("Labeled Example Utterance:", labeledExampleUtteranceWithMLEntity)

    # Add an example for the entity.
    # Enable nested children to allow using multiple models with the same name.
	# The quantity subentity and the phraselist could have the same exact name if this is set to True
    client.examples.add(appId, versionId, labeledExampleUtteranceWithMLEntity, { "enableNestedChildren": True })
	# </AuthoringAddLabeledExamples>
	
# <AuthoringSortModelObject>
def get_grandchild_id(model, childName, grandChildName):
	
	theseChildren = next(filter((lambda child: child.name == childName), model.children))
	theseGrandchildren = next(filter((lambda child: child.name == grandChildName), theseChildren.children))
	
	grandChildId = theseGrandchildren.id
	
	return grandChildId
# </AuthoringSortModelObject>

quickstart()