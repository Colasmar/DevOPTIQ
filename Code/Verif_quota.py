import openai

OPENAI_API_KEY= "Indiquez ici la clé OPEN AI"

usage = openai.Engine.retrieve("davinci")  # Remplacez "davinci" par votre modèle utilisé
print(usage)
