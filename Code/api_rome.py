def get_job_data(self, query):
    """
    Interroge l'API ROME 4.0 avec le paramètre 'query' pour rechercher des fiches métiers.
    Renvoie la réponse au format JSON.
    
    :param query: Chaîne de caractères servant de critère de recherche (ex: "ingénieur")
    :return: JSON contenant les résultats de la recherche
    """
    url = f"{self.base_url}/job-search"
    params = {"query": query}
    if self.api_key:
        params["api_key"] = self.api_key
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()
