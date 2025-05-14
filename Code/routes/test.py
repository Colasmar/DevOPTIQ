import openai

def analyze_aptitude(activity_description):
    prompt = f"""
Tu es un expert en organisation du travail et en accessibilité inclusive.

À partir de la description suivante d'une activité professionnelle :

{activity_description}

Analyse les points suivants :
1. **Handicaps particulièrement adaptés** : lesquels pourraient apporter une véritable valeur ajoutée à cette activité, et pourquoi ?
2. **Sans aménagement majeur** : cette activité peut-elle être tenue par une personne en situation de handicap sans adaptation spécifique ? Dans quel(s) cas ?
3. **Avec aménagements simples** : si des aménagements légers permettraient de la rendre accessible, lesquels recommandes-tu ?
4. **Contraintes majeures à étudier** : quelles limitations rendent l’activité plus complexe ou bloquante selon certains handicaps ? Et quelles pistes pour lever ces obstacles ?

Donne une réponse **structurée en 4 paragraphes**, en respectant les titres ci-dessus, sans jargon médical, et en te basant uniquement sur les éléments présents dans la description de l’activité.
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Tu es un assistant expert en accessibilité et organisation inclusive du travail."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )

        reply = response['choices'][0]['message']['content']
        return reply.strip()

    except Exception as e:
        return f"Erreur lors de l'appel à l'API : {e}"

# Code pour générer une analyse approfondie par rapport à une catégorie d'activité

def explore_aptitude_block(activity_description, selected_block):
    prompt = f"""
Tu es un expert en accessibilité au travail et en inclusion professionnelle.

Voici la description d'une activité professionnelle :

{activity_description}

Et voici une observation liée à l'inclusion, qu'on souhaite approfondir :

"{selected_block}"

À partir de cela, donne des conseils pratiques sous 3 rubriques :
1. ✔️ **Points à vérifier** avant de confier cette activité à une personne concernée
2. 🛠 **Aménagements possibles ou nécessaires**
3. 🤝 **Forme d’accompagnement ou de soutien recommandé**

Structure ta réponse de façon claire, sans jargon médical, avec des recommandations concrètes.
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Tu es un assistant expert en organisation du travail inclusif."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )

        reply = response['choices'][0]['message']['content']
        return reply.strip()

    except Exception as e:
        return f"Erreur lors de l'appel à l'API : {e}"