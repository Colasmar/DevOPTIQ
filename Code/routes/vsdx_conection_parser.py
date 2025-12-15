# Code/utils/vsdx_connection_parser.py
"""
Parseur de connexions VSDX pour l'import des liens entre activités.

Ce module extrait les connexions (flèches) d'un fichier Visio (.vsdx)
et retourne une liste de connexions avec :
- source_shape_id / source_name
- target_shape_id / target_name  
- data_name (nom de la donnée qui transite)
- data_type (déclenchante / nourrissante)
"""

import zipfile
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Tuple
import os


class VsdxConnectionParser:
    """Parse les connexions d'un fichier VSDX."""
    
    VISIO_NS = {'v': 'http://schemas.microsoft.com/office/visio/2012/main'}
    
    def __init__(self, vsdx_path: str):
        """
        Initialise le parser avec le chemin du fichier VSDX.
        
        Args:
            vsdx_path: Chemin vers le fichier .vsdx
        """
        self.vsdx_path = vsdx_path
        self.shape_info: Dict[str, Dict] = {}
        self.connections: List[Dict] = []
        
    def parse(self) -> Tuple[List[Dict], List[str]]:
        """
        Parse le fichier VSDX et extrait les connexions.
        
        Returns:
            Tuple contenant:
            - Liste des connexions
            - Liste des erreurs/warnings
        """
        errors = []
        
        # Vérifier que le fichier existe
        if not os.path.exists(self.vsdx_path):
            return [], [f"Fichier non trouvé: {self.vsdx_path}"]
        
        # Vérifier l'extension
        if not self.vsdx_path.lower().endswith('.vsdx'):
            return [], ["Le fichier doit être au format .vsdx"]
        
        try:
            # Extraire et parser le fichier page1.xml
            with zipfile.ZipFile(self.vsdx_path, 'r') as zf:
                # Lister les fichiers de pages disponibles
                page_files = [f for f in zf.namelist() if 'pages/page' in f and f.endswith('.xml')]
                
                if not page_files:
                    return [], ["Aucune page trouvée dans le fichier VSDX"]
                
                # Parser la première page (ou toutes si plusieurs)
                for page_file in page_files:
                    page_xml = zf.read(page_file)
                    self._parse_page(page_xml, errors)
                    
        except zipfile.BadZipFile:
            return [], ["Le fichier VSDX est corrompu ou invalide"]
        except Exception as e:
            return [], [f"Erreur lors du parsing: {str(e)}"]
        
        return self.connections, errors
    
    def _parse_page(self, page_xml: bytes, errors: List[str]):
        """Parse une page XML et extrait les shapes et connexions."""
        
        try:
            root = ET.fromstring(page_xml)
        except ET.ParseError as e:
            errors.append(f"Erreur parsing XML: {str(e)}")
            return
        
        # 1) Récupérer tous les shapes avec leurs infos
        shapes = root.findall('.//v:Shape', self.VISIO_NS)
        
        for shape in shapes:
            shape_id = shape.get('ID')
            if not shape_id:
                continue
                
            shape_name = shape.get('Name', '')
            
            # Chercher le texte du shape
            text_elem = shape.find('.//v:Text', self.VISIO_NS)
            text = ''
            if text_elem is not None and text_elem.text:
                text = text_elem.text.strip()
                # Nettoyer les caractères de contrôle
                text = ''.join(c for c in text if c.isprintable())
            
            self.shape_info[shape_id] = {
                'name': shape_name,
                'text': text
            }
        
        # 2) Récupérer toutes les connexions
        connects = root.findall('.//v:Connect', self.VISIO_NS)
        connectors: Dict[str, Dict] = {}
        
        for connect in connects:
            from_sheet = connect.get('FromSheet')
            from_cell = connect.get('FromCell', '')
            to_sheet = connect.get('ToSheet')
            
            if not from_sheet or not to_sheet:
                continue
            
            if from_sheet not in connectors:
                connectors[from_sheet] = {'source': None, 'target': None}
            
            # BeginX = début du connecteur (source)
            # EndX = fin du connecteur (cible)
            if 'BeginX' in from_cell:
                connectors[from_sheet]['source'] = to_sheet
            elif 'EndX' in from_cell:
                connectors[from_sheet]['target'] = to_sheet
        
        # 3) Construire la liste des connexions avec noms
        for conn_id, data in connectors.items():
            source_id = data.get('source')
            target_id = data.get('target')
            
            # Ignorer les connexions incomplètes
            if not source_id or not target_id:
                continue
            
            source_info = self.shape_info.get(source_id, {})
            target_info = self.shape_info.get(target_id, {})
            conn_info = self.shape_info.get(conn_id, {})
            
            source_name = source_info.get('text') or source_info.get('name', '')
            target_name = target_info.get('text') or target_info.get('name', '')
            
            # Filtrer les shapes sans nom valide
            if not source_name or not target_name:
                continue
            
            # Ignorer les shapes "Résultat" qui sont des artefacts Visio
            if source_name.startswith('Résultat.') or target_name.startswith('Résultat.'):
                continue
            
            # Le nom du connecteur peut être le nom de la donnée qui transite
            connector_text = conn_info.get('text') or ''
            connector_name = conn_info.get('name') or ''
            
            # Extraire le type et le nom de la donnée
            data_type, data_name = self._extract_data_info(connector_name, connector_text)
            
            self.connections.append({
                'source_shape_id': source_id,
                'source_name': source_name.strip(),
                'target_shape_id': target_id,
                'target_name': target_name.strip(),
                'connector_id': conn_id,
                'data_name': data_name,
                'data_type': data_type
            })
    
    def _extract_data_info(self, connector_name: str, connector_text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extrait le type et le nom de la donnée depuis le connecteur.
        
        Convention Visio:
        - "T xxx" ou "T- xxx" = donnée déclenchante
        - "N xxx" ou "N- xxx" = donnée nourrissante
        
        Returns:
            Tuple (data_type, data_name)
        """
        data_type = None
        data_name = connector_text or connector_name or None
        
        # Analyser le préfixe du nom du connecteur
        name = connector_name.strip()
        
        if name.startswith('T ') or name.startswith('T-'):
            data_type = 'déclenchante'
            # Extraire le nom après le préfixe
            data_name = name[2:].strip() if len(name) > 2 else connector_text
        elif name.startswith('N ') or name.startswith('N-'):
            data_type = 'nourrissante'
            data_name = name[2:].strip() if len(name) > 2 else connector_text
        
        # Nettoyer le nom si vide
        if data_name and data_name.strip() == '':
            data_name = None
            
        return data_type, data_name
    
    def get_unique_activities(self) -> List[str]:
        """
        Retourne la liste des noms d'activités uniques trouvées dans les connexions.
        
        Returns:
            Liste des noms d'activités
        """
        activities = set()
        for conn in self.connections:
            activities.add(conn['source_name'])
            activities.add(conn['target_name'])
        return sorted(list(activities))


def parse_vsdx_connections(vsdx_path: str) -> Tuple[List[Dict], List[str]]:
    """
    Fonction utilitaire pour parser les connexions d'un fichier VSDX.
    
    Args:
        vsdx_path: Chemin vers le fichier .vsdx
        
    Returns:
        Tuple contenant:
        - Liste des connexions
        - Liste des erreurs/warnings
    """
    parser = VsdxConnectionParser(vsdx_path)
    return parser.parse()


def validate_connections_against_activities(
    connections: List[Dict], 
    existing_activities: Dict[str, int]
) -> Tuple[List[Dict], List[Dict], List[str]]:
    """
    Valide les connexions par rapport aux activités existantes.
    
    Args:
        connections: Liste des connexions extraites du VSDX
        existing_activities: Dict {nom_activité: activity_id}
        
    Returns:
        Tuple contenant:
        - valid_connections: Connexions où source ET cible existent
        - invalid_connections: Connexions avec activités manquantes
        - missing_activities: Liste des noms d'activités non trouvées
    """
    valid_connections = []
    invalid_connections = []
    missing_activities = set()
    
    for conn in connections:
        source_name = conn['source_name']
        target_name = conn['target_name']
        
        source_exists = source_name in existing_activities
        target_exists = target_name in existing_activities
        
        if source_exists and target_exists:
            # Ajouter les IDs des activités
            conn_with_ids = conn.copy()
            conn_with_ids['source_activity_id'] = existing_activities[source_name]
            conn_with_ids['target_activity_id'] = existing_activities[target_name]
            valid_connections.append(conn_with_ids)
        else:
            invalid_connections.append(conn)
            if not source_exists:
                missing_activities.add(source_name)
            if not target_exists:
                missing_activities.add(target_name)
    
    return valid_connections, invalid_connections, sorted(list(missing_activities))


# Test du module
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python vsdx_connection_parser.py <fichier.vsdx>")
        sys.exit(1)
    
    vsdx_path = sys.argv[1]
    connections, errors = parse_vsdx_connections(vsdx_path)
    
    if errors:
        print("Erreurs:")
        for e in errors:
            print(f"  - {e}")
    
    print(f"\nConnexions trouvées: {len(connections)}")
    for conn in connections:
        print(f"  {conn['source_name']} → {conn['target_name']}")
        if conn['data_name']:
            print(f"    [{conn['data_type'] or 'donnée'}] {conn['data_name']}")